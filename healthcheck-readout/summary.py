import json
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

from readout import FOLLOW_UP

COVER = Path(__file__).with_name("cover.pdf")
# Name of the summary in the application's bucket in MTA.
FILE = "healthcheck-summary.pdf"
TEMPLATE = "/opt/eisvogel.latex"

# Pandoc sizes the columns of a pipe table from the dashes when a row is wider than the page.
AREA_COLUMNS = "|------|------------|------------------|"
# Characters per line in the two wider columns of an area's table, to estimate its height.
ANSWER_WIDTH, DIRECTION_WIDTH = 27, 42


def escaped(text):
    return re.sub(r"([\\`*_{}\[\]()<>#+\-.!|~^$@%&])", r"\\\1", text)


def summary_table(rows):
    """Returns a grid table, the Pandoc table form whose cells can hold a list."""
    cells = [(item, value if isinstance(value, list) else [value]) for item, value in rows]
    left = max(len(item) for item, _ in cells)
    right = max(len(line) for _, value in cells for line in value)
    rule = f"+{'-' * (left + 2)}+{'-' * (right + 2)}+"
    lines = [rule]
    for item, value in cells:
        for number, line in enumerate(value):
            lines.append(f"| {(item if number == 0 else ''):<{left}} | {line:<{right}} |")
        lines.append(rule)
    return lines


def needspace(count):
    return ["", f"\\needspace{{{count}\\baselineskip}}", ""]


def lines_needed(evidence):
    rows = sum(
        max(len(e["answer"]) // ANSWER_WIDTH, len(e["rationale"] + e["mitigation"]) // DIRECTION_WIDTH) + 2
        for e in evidence
    )
    return rows + 7


def markdown(organisation, readout):
    generated = datetime.fromisoformat(readout["generated"])
    day = f"{generated.day} {generated:%B %Y}"
    areas = readout["areas"]
    lines = [
        "---",
        f"title: {json.dumps(organisation + ': 5 Minute HashiCorp Healthcheck')}",
        f"date: {json.dumps(day)}",
        "lang: en-GB",
        "papersize: a4",
        'mainfont: "IBM Plex Sans"',
        'sansfont: "IBM Plex Sans"',
        "table-use-row-colors: true",
        "titlepage: true",
        'titlepage-color: "000000"',
        "titlepage-rule-height: 0",
        'titlepage-text-color: "FFFFFF"',
    ]
    if COVER.exists():
        lines.append(f"titlepage-background: {json.dumps(str(COVER))}")
    lines += [
        "header-includes:",
        "  - \\usepackage{needspace}",
        "---",
        "",
        "# Introduction",
        "",
        f"This document summarises what {escaped(organisation)} told HashiCorp during a 5 Minute HashiCorp "
        f"Healthcheck on {day}. The healthcheck asks fourteen questions about how infrastructure is "
        "delivered, secured, connected and run.",
        "",
        "Each response that highlighted an opportunity for improvement appears below under the area it "
        "belongs to, with the reason it matters and a direction for improvement.",
        "",
        "These results come from a short questionnaire. They show where further discussion would benefit "
        f"{escaped(organisation)}.",
        "",
    ]
    lines += summary_table([
        ("Environment", readout["environment"]),
        ("Overall result", readout["verdict"]),
        ("Areas highlighted", [f"- {a['capability']} ({a['strength']})" for a in areas] or "None"),
        ("No signal in", [f"- {c}" for c in readout["in_good_shape"]] or "None"),
    ])
    for number, area in enumerate(areas):
        # Keeps an area's heading and table on one page.
        lines += needspace(lines_needed(area["evidence"]) + (0 if number else 4))
        if number == 0:
            lines += ["# What was highlighted", ""]
        lines += [
            f"## {area['capability']}",
            "",
            f"Signal: {area['strength']}.",
            "",
            "| **Aspect** | **Response** | **Why it matters, and a direction** |",
            AREA_COLUMNS,
        ]
        lines += [
            f"| {e['facet'].capitalize()} | {e['answer']} | {e['rationale']} {e['mitigation']} |"
            for e in area["evidence"]
        ]
    if readout["patterns"]:
        lines += ["", "# Patterns across areas", ""]
        lines += [f"- **{p['name']}.** {p['detail']}" for p in readout["patterns"]]
    if readout["unknowns"]:
        lines += ["", "# Not answered", ""]
        lines += [f"- {u['question']}" for u in readout["unknowns"]]
    lines += needspace(4 + sum(4 + len(FOLLOW_UP[a["capability"]]["roles"]) for a in areas))
    lines += ["# Suggested next steps", ""]
    if not areas:
        lines.append("No area was highlighted, so this healthcheck suggests no follow-up session.")
    for number, area in enumerate(areas, 1):
        follow_up = FOLLOW_UP[area["capability"]]
        topics = follow_up["topics"][0].lower() + follow_up["topics"][1:]
        lines += [
            f"{number}. **{area['capability']}.** A follow-up session on {follow_up['product']}, covering "
            f"{topics}. Worth involving:",
            "",
        ]
        lines += [f"    - {role}" for role in follow_up["roles"]]
        lines.append("")
    if readout["implementation"]:
        product = FOLLOW_UP[readout["implementation"]["capability"]]["product"]
        lines += [
            f"Changes in the areas above are usually delivered as code, which makes {product} relevant "
            "to those sessions.",
        ]
    return "\n".join(lines) + "\n"


def pdf(organisation, readout, cached=True):
    with tempfile.TemporaryDirectory() as directory:
        Path(directory, "summary.md").write_text(markdown(organisation, readout))
        subprocess.run(
            ["pandoc", "summary.md", "-o", "summary.pdf", "--template", TEMPLATE, "--pdf-engine", "tectonic"]
            + (["--pdf-engine-opt=--only-cached"] if cached else []),
            cwd=directory,
            check=True,
        )
        return Path(directory, "summary.pdf").read_bytes()
