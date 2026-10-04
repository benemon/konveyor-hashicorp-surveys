import sys
from pathlib import Path

import yaml

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "healthcheck-readout"))
import readout  # noqa: E402

ABBR = {
    "Infrastructure Lifecycle": "IL",
    "Image Lifecycle": "IM",
    "Machine Identity and Secrets": "MIS",
    "Human Access": "HA",
    "Service Networking": "SN",
    "Workload Lifecycle": "WL",
}
# Design notes printed after a question's table, by facet.
NOTES = {
    "environment": "Q1 is context. It opens the conversation and helps the facilitator read the later answers. Its "
    "answers are green and carry no signal tag.",
    "image build": "Each image question has a not-applicable answer for organisations that do not maintain machine "
    "images. It is green and carries no signal.",
    "image composition": "Build definitions alone establish neither an image version's contents nor its parent image.",
    "workload identity": "The identity may come from the platform, the runtime or a workload identity system, and may "
    "be used directly or exchanged for short-lived credentials.",
    "certificates": "This question covers certificate lifecycle where certificates exist. Whether their absence is a "
    'gap is left to the service-to-service security question and to the pattern "Network-centric controls without '
    'internal certificates".',
}


# What a persona demonstrates beyond the counts in its row.
SHOWS = {
    "B": "IL as a solution adjacency note only; no machine images maintained; hand-managed service accounts",
    "C": "A published image record that provisioning does not validate",
    "F": "An adjacent signal that is not absorbed",
    "G": "Ordering within the strong tier; images built by hand, unmanaged and of unknown contents beside codified "
    "provisioning",
    "H": "Fragmented image automation; platform identity for some workloads",
    "J": "A pattern that rests on a green answer; an adjacent signal from Service Networking",
}
WORDS = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]


def tags(answer, category):
    return [t["tag"] for t in answer.get("applyTags", []) if t["category"] == category]


def questions(doc):
    out, number = [], 0
    for section in doc["sections"]:
        out.append(f"### Section {section['order']}: {section['name']}\n")
        for question in section["questions"]:
            number += 1
            facet = tags(question["answers"][0], readout.KEY)[0].split(": ")[0]
            out.append(f"**Q{number} ({facet}). {question['text']}**\n")
            out.append("| # | Answer | Key | Risk | Direct | Adjacent |\n|---|---|---|---|---|---|")
            for answer in question["answers"]:
                key = tags(answer, readout.KEY)[0].split(": ")[1]
                direct = ", ".join(ABBR[t] for t in tags(answer, readout.DIRECT))
                adjacent = ", ".join(ABBR[t] for t in tags(answer, readout.ADJACENT))
                out.append(f"| {answer['order']} | {answer['text']} | `{key}` | {answer['risk']} | {direct} | {adjacent} |")
            out.append("")
            if facet in NOTES:
                out.append(NOTES[facet] + "\n")
    return "\n".join(out)


def condition(facets):
    return [f"`{facet}` is " + " or ".join(f"`{k}`" for k in sorted(keys)) for facet, keys in facets.items()]


def patterns():
    rows = ["| Pattern | Holds when | Meaning |", "|---|---|---|"]
    for pattern in readout.PATTERNS:
        parts = condition(pattern["all"])
        if "any" in pattern:
            n = pattern.get("at_least", 1)
            parts.append(("at least two of: " if n == 2 else "one of: ") + "; ".join(condition(pattern["any"])))
        rows.append(f"| {pattern['name']} | {', and '.join(parts)} | {pattern['detail']} |")
    return "\n".join(rows)


def thresholds(doc):
    total = sum(len(s["questions"]) for s in doc["sections"])
    needed = {c: -(-pct * total // 100) for c, pct in doc["thresholds"].items()}
    out = ["```yaml", "thresholds:"] + [f"  {c}: {pct}" for c, pct in doc["thresholds"].items()] + ["```", ""]
    out += [f"With {total} questions this gives:", "", "| Overall | Condition | Message intent |", "|---|---|---|"]
    out.append(f"| red | {WORDS[needed['red']]} or more red answers | Follow-up discussion indicated |")
    out.append(f"| yellow | no red, {WORDS[needed['yellow']]} or more yellow | Areas worth exploring |")
    out.append(f"| unknown | neither of the above, {WORDS[needed['unknown']]} or more unknown | Not enough information for a signal |")
    out.append("| green | otherwise | No strong or repeated signal overall |")
    return "\n".join(out)


def personas(doc):
    questions = [q for s in doc["sections"] for q in s["questions"]]
    rows = ["| Persona | Answers | Signals | Patterns | Overall | Shows |", "|---|---|---|---|---|---|"]
    for persona in yaml.safe_load((HERE / "personas.yaml").read_text()):
        risks = [next(a["risk"] for a in q["answers"] if a["order"] == n) for q, n in zip(questions, persona["answers"])]
        answers = ", ".join(f"{risks.count(c)} {c}" for c in ("red", "yellow", "unknown"))
        strong = sum(v == "strong" for v in persona["direct"].values())
        signals = f"{len(persona['direct'])} direct ({strong} strong), {len(persona['adjacent'])} adjacent"
        shows = SHOWS.get(persona["name"][0], "")
        rows.append(f"| {persona['name']} | {answers} | {signals} | {len(persona['patterns'])} | {persona['overall']} | {shows} |")
    return "\n".join(rows)


def render():
    doc = yaml.safe_load((HERE / "questionnaire.yaml").read_text())
    text = (HERE / "design.tmpl.md").read_text()
    for placeholder, value in (
        ("{{QUESTIONS}}", questions(doc)),
        ("{{PATTERNS}}", patterns()),
        ("{{THRESHOLDS}}", thresholds(doc)),
        ("{{PERSONAS}}", personas(doc)),
    ):
        text = text.replace(placeholder, value)
    return text


if __name__ == "__main__":
    (HERE / "DESIGN.md").write_text(render())
