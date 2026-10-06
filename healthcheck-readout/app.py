import json
import os
import urllib.request
from datetime import datetime, timezone

import readout
import summary
from impacts import IMPACTS
from pointers import FEATURES

HUB = os.environ["HUB_BASE_URL"].rstrip("/")
TOKEN = os.environ["TOKEN"]
TASK = os.environ["TASK"]

QUESTIONNAIRE = "HashiCorp Healthcheck"
# Facts and tags written here are owned by this source, so each run replaces the last.
SOURCE = "healthcheck-readout"


def hub(method, path, body=None):
    request = urllib.request.Request(
        HUB + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read()
        return json.loads(payload) if payload else None


def product_tags(direct):
    # MTA colours tags by category, so each product has its own.
    categories = {c["name"]: c for c in hub("GET", "/tagcategories")}
    for capability, strength in direct.items():
        product = readout.FOLLOW_UP[capability]
        category = categories.get(product["product"]) or hub(
            "POST", "/tagcategories", {"name": product["product"], "colour": product["colour"]}
        )
        name = f"{product['product']}: {strength}"
        existing = {t["name"]: t["id"] for t in category.get("tags") or []}
        yield existing.get(name) or hub("POST", "/tags", {"name": name, "category": {"id": category["id"]}})["id"]


def insight(rule, headline, detail, category, answer, targets, effort=0):
    return {
        "ruleset": QUESTIONNAIRE,
        "rule": rule,
        "name": headline,
        # MTA titles an insight with the first line of its description.
        "description": f"{headline}\n\n{detail}",
        "category": category,
        "effort": effort,
        "labels": [f"konveyor.io/source={QUESTIONNAIRE}"] + [f"konveyor.io/target={t}" for t in targets],
        "incidents": [{"file": QUESTIONNAIRE, "message": answer}],
    }


def impact_markdown(facet):
    lines = ["##### Business impact", ""]
    lines += [f"- **{dimension.capitalize()}.** {text}" for dimension, text in IMPACTS[facet]["impacts"].items()]
    return "\n".join(lines) + "\n\n"


def pointers_markdown(pointers):
    if not pointers:
        return ""
    # MTA renders a description as Markdown, where a single newline does not break a line.
    lines = ["##### Features for the follow-up session"]
    for product, features in pointers.items():
        lines += ["", f"**{product}**", ""]
        for name in features:
            sentence, url = FEATURES[name]
            lines.append(f"- **{name}.** {sentence} [Documentation]({url})")
    return "\n".join(lines)


def insights(result):
    for area in result["areas"]:
        for item in area["evidence"]:
            # MTA lists an entry under Issues when it has effort and under Insights when it has none.
            for rule, effort in ((item["key"], 0), (f"{item['key']} (issue)", 1)):
                yield insight(
                    rule,
                    f"{item['facet'].capitalize()}: {item['answer']}",
                    f"{item['rationale']}\n\n**Suggested change:** {item['mitigation']}\n\n"
                    + impact_markdown(item["facet"])
                    + pointers_markdown(item["pointers"]),
                    "High" if item["risk"] == "red" else "Medium",
                    f"{item['question']} {item['answer']}",
                    [area["capability"], *item["pointers"]],
                    effort,
                )
    for adjacent in result["adjacent"]:
        answers = "\n".join(f"- **{a['facet'].capitalize()}**: {a['answer']}. {a['note']}" for a in adjacent["answers"])
        yield insight(
            f"adjacent: {adjacent['capability']}",
            f"Adjacent signal: {adjacent['capability']}",
            f"Derived from responses given under {', '.join(adjacent['via'])}. It is not a direct finding.\n\n{answers}",
            "Adjacent",
            "; ".join(a["answer"] for a in adjacent["answers"]),
            [adjacent["capability"]],
        )
    for pattern in result["patterns"]:
        answers = "\n".join(f"- **{a['facet'].capitalize()}**: {a['answer']}" for a in pattern["answers"])
        yield insight(
            f"pattern: {pattern['name']}",
            f"Pattern: {pattern['name']}",
            f"{pattern['detail']}\n\n##### Answers behind this pattern\n\n{answers}\n\n"
            + pointers_markdown(pattern["pointers"]),
            "Pattern",
            pattern["detail"],
            pattern["capabilities"] + pattern["products"],
        )


def upload(path, content, content_type):
    boundary = "healthcheck-readout-upload"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="file"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
    request = urllib.request.Request(
        HUB + path,
        data=body,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        },
    )
    urllib.request.urlopen(request, timeout=30).close()


def analysis(result):
    # The hub reads an analysis as one file of three sections delimited by GS-wrapped markers.
    def section(name, documents):
        return f"\x1dBEGIN-{name}\x1d\n" + "\n".join(json.dumps(d) for d in documents) + f"\n\x1dEND-{name}\x1d\n"

    return (section("MAIN", [{}]) + section("INSIGHTS", insights(result)) + section("DEPS", [])).encode()


def run():
    task = hub("GET", f"/tasks/{TASK}")
    application = task["application"]["id"]
    # An addon token cannot read assessments, so the submitter passes the assessment as task data.
    assessment = task["data"]["assessment"]

    result = readout.build(assessment["sections"], assessment["verdict"])
    result["generated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    hub("PUT", f"/applications/{application}/facts/{SOURCE}:", result)
    upload(f"/applications/{application}/analyses", analysis(result), "application/json")
    upload(
        f"/applications/{application}/bucket/{summary.FILE}",
        summary.pdf(task["application"]["name"], result),
        "application/pdf",
    )
    hub(
        "PUT",
        f"/applications/{application}/tags?source={SOURCE}",
        [{"id": tag} for tag in product_tags(result["direct"])],
    )
    return [f"{capability}: {strength}" for capability, strength in result["direct"].items()] or [
        "no capability signals"
    ]


path = f"/tasks/{TASK}/report"
# The hub saves a report update as a new row unless it carries the id from the create.
report = {"id": hub("POST", path, {"status": "Running"})["id"]}
try:
    hub("PUT", path, report | {"status": "Succeeded", "activity": run()})
except Exception as reason:
    failure = {"severity": "Error", "description": str(reason)}
    hub("PUT", path, report | {"status": "Failed", "errors": [failure]})
    raise
