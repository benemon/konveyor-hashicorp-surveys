import csv
import io
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MTA_HUB = os.environ["MTA_HUB"].rstrip("/")
# Written by the chart's setup job after the pod may already be running, so it is read per call.
API_KEY = Path("/etc/healthcheck-console/api-key")
INDEX = (Path(__file__).parent / "index.html").read_bytes()
STYLES = (Path(__file__).parent / "patternfly.min.css").read_bytes()
# The route serves this path on MTA's own host, so links into MTA are same-origin and
# keep the browser tab's MTA session.
PREFIX = "/console"
ADDON = "healthcheck-readout"
# The questionnaire the readout addon understands.
HEALTHCHECK = "HashiCorp Healthcheck"
# Name the addon gives the summary in the application's bucket.
SUMMARY = "healthcheck-summary.pdf"
# What a caller must send to delete every respondent.
CONFIRMATION = "delete all respondents"
CAPABILITIES = (
    "Infrastructure Lifecycle",
    "Machine Identity and Secrets",
    "Human Access",
    "Service Networking",
    "Workload Lifecycle",
)


def call(path, body=None, method=None):
    request = urllib.request.Request(
        f"{MTA_HUB}/{path}",
        method=method,
        data=json.dumps(body).encode() if body else None,
        headers={
            "Authorization": f"Bearer {API_KEY.read_text()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def hub(path, body=None):
    return json.loads(call(path, body))


def questionnaires():
    return [q for q in hub("questionnaires") if not q.get("builtin")]


def start(organisation, email, questionnaire):
    available = questionnaires()
    if questionnaire:
        available = [q for q in available if q["name"] == questionnaire]
    if len(available) != 1:
        raise ValueError("questionnaire must name one of the questionnaires in MTA")
    chosen = available[0]["id"]

    # The MTA wizard will not advance past its first step without a stakeholder.
    stakeholder = next(
        (s for s in hub("stakeholders") if s["email"] == email), None
    ) or hub("stakeholders", {"name": email, "email": email})
    application = next(
        (a for a in hub("applications") if a["name"] == organisation), None
    ) or hub("applications", {"name": organisation, "owner": {"id": stakeholder["id"]}})
    path = f"applications/{application['id']}/assessments"
    # The list also returns assessments inherited from archetypes.
    assessment = next(
        (
            a
            for a in hub(path)
            if (a.get("application") or {}).get("id") == application["id"]
            and a["questionnaire"]["id"] == chosen
        ),
        None,
    ) or hub(path, {"questionnaire": {"id": chosen}, "stakeholders": [{"id": stakeholder["id"]}]})
    return {
        "application": application["id"],
        "assessment": assessment["id"],
        "url": f"/applications/assessment/{assessment['id']}",
    }


def completed():
    """Returns the completed healthcheck assessments by application id."""
    healthcheck = next((q["id"] for q in hub("questionnaires") if q["name"] == HEALTHCHECK), None)
    return {
        a["application"]["id"]: a
        for a in hub("assessments")
        if a.get("application") and a["questionnaire"]["id"] == healthcheck and a["status"] == "complete"
    }


def readout(organisation):
    assessment = next((a for a in completed().values() if a["application"]["name"] == organisation), None)
    if not assessment:
        raise ValueError(f"organisation has no completed {HEALTHCHECK} assessment")
    # An addon token cannot read assessments, so the assessment travels as task data.
    task = hub(
        "tasks",
        {
            "name": f"{organisation} readout",
            "addon": ADDON,
            "application": {"id": assessment["application"]["id"]},
            "state": "Ready",
            "data": {
                "assessment": {
                    "verdict": assessment["riskMessages"][assessment["risk"]],
                    "sections": assessment["sections"],
                }
            },
        },
    )
    return {"task": task["id"]}


def respondents():
    complete = completed()
    listed = []
    for application in sorted(hub("applications"), key=lambda a: a["name"].lower()):
        facts = hub(f"applications/{application['id']}/facts/{ADDON}:")
        listed.append(
            {
                "application": application["id"],
                "organisation": application["name"],
                "contact": (application.get("owner") or {}).get("name", ""),
                "completed": application["id"] in complete,
                "generated": facts.get("generated"),
                "version": facts.get("version"),
                "verdict": facts.get("verdict"),
                "direct": facts.get("direct", {}),
            }
        )
    return listed


def respondents_csv():
    output = io.StringIO()
    rows = csv.writer(output)
    rows.writerow(
        ["Organisation", "Contact", "Assessment completed", "Readout generated", "Version", "Result", *CAPABILITIES]
    )
    for r in respondents():
        rows.writerow(
            [r["organisation"], r["contact"], "yes" if r["completed"] else "no", r["generated"], r["version"], r["verdict"]]
            + [r["direct"].get(capability, "") for capability in CAPABILITIES]
        )
    return output.getvalue().encode()


def summary(application):
    try:
        return call(f"applications/{application}/bucket/{SUMMARY}")
    except urllib.error.HTTPError as reason:
        if reason.code != 404:
            raise
        raise ValueError("no summary is stored for this respondent: generate its readout") from None


def remove(application):
    # The hub does not remove an application's tasks with it.
    for task in hub("tasks"):
        if (task.get("application") or {}).get("id") == application:
            call(f"tasks/{task['id']}", method="DELETE")
    call(f"applications/{application}", method="DELETE")
    return {"removed": application}


def clear():
    removed = [remove(a["id"])["removed"] for a in hub("applications")]
    for stakeholder in hub("stakeholders"):
        call(f"stakeholders/{stakeholder['id']}", method="DELETE")
    return {"removed": len(removed)}


def readout_state(task):
    found = hub(f"tasks/{task}")
    if found.get("addon") != ADDON:
        raise ValueError("not a readout task")
    state = {
        "state": found["state"],
        "errors": [e["description"] for e in found.get("errors") or []],
    }
    if found["state"] == "Succeeded":
        # Reported from what the addon stored in MTA, not from what it said it did.
        application = found["application"]["id"]
        facts = hub(f"applications/{application}/facts/{ADDON}:")
        state |= {
            "verdict": facts["verdict"],
            "areas": [
                {key: area[key] for key in ("product", "capability", "strength", "facets")}
                for area in facts["areas"]
            ],
            "issues": sum(len(area["evidence"]) for area in facts["areas"]),
            "patterns": [
                {key: pattern[key] for key in ("name", "detail", "products")}
                for pattern in facts["patterns"]
            ],
            "generated": facts["generated"],
            "url": f"/issues/single-app/{application}",
            "application": application,
        }
    return state


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body, content_type="application/json", filename=None):
        payload = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(payload)

    def call_mta(self, action, **reply):
        try:
            self.reply(200, action(), **reply)
        except ValueError as reason:
            self.reply(400, {"error": str(reason)})
        except urllib.error.HTTPError as reason:
            # The hub echoes the bearer token in its 401 body, so the body is not relayed.
            self.reply(502, {"error": f"MTA returned {reason.code}"})
        except (urllib.error.URLError, FileNotFoundError):
            self.reply(502, {"error": "MTA is unreachable or the service has no API key yet"})

    def fields(self):
        try:
            fields = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        except ValueError:
            return {}
        return fields if isinstance(fields, dict) else {}

    def do_GET(self):
        path = self.path.removeprefix(PREFIX)
        task = path.removeprefix("/api/readouts/")
        application = path.removeprefix("/api/summaries/")
        if self.path == PREFIX:
            self.send_response(301)
            self.send_header("Location", f"{PREFIX}/")
            self.end_headers()
        elif path == self.path:
            self.reply(404, {"error": "not found"})
        elif path == "/":
            self.reply(200, INDEX, "text/html; charset=utf-8")
        elif path == "/patternfly.min.css":
            self.reply(200, STYLES, "text/css")
        elif path == "/api/questionnaires":
            self.call_mta(lambda: [q["name"] for q in questionnaires()])
        elif path == "/api/organisations":
            self.call_mta(lambda: sorted(a["name"] for a in hub("applications")))
        elif path == "/api/respondents":
            self.call_mta(respondents)
        elif path == "/api/respondents.csv":
            self.call_mta(respondents_csv, content_type="text/csv; charset=utf-8", filename="respondents.csv")
        elif task != path and task.isdigit():
            self.call_mta(lambda: readout_state(task))
        elif application != path and application.isdigit():
            self.call_mta(lambda: summary(application), content_type="application/pdf")
        else:
            self.reply(404, {"error": "not found"})

    def do_POST(self):
        path = self.path.removeprefix(PREFIX)
        fields = self.fields()
        organisation = str(fields.get("organisation", "")).strip()
        email = str(fields.get("email", "")).strip()
        if path == self.path:
            self.reply(404, {"error": "not found"})
        elif path == "/api/readouts" and organisation:
            self.call_mta(lambda: readout(organisation))
        elif path == "/api/readouts":
            self.reply(400, {"error": "organisation is required"})
        elif path == "/api/assessments" and organisation and email:
            self.call_mta(lambda: start(organisation, email, fields.get("questionnaire")))
        elif path == "/api/assessments":
            self.reply(400, {"error": "organisation and email are required"})
        else:
            self.reply(404, {"error": "not found"})

    def do_DELETE(self):
        path = self.path.removeprefix(PREFIX)
        application = path.removeprefix("/api/respondents/")
        if path == "/api/respondents" and path != self.path:
            if self.fields().get("confirm") == CONFIRMATION:
                self.call_mta(clear)
            else:
                self.reply(400, {"error": f'confirm must be "{CONFIRMATION}"'})
        elif application != path and application.isdigit():
            self.call_mta(lambda: remove(int(application)))
        else:
            self.reply(404, {"error": "not found"})


ThreadingHTTPServer(("", 8080), Handler).serve_forever()
