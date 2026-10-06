import json
import re
import subprocess
import tempfile
import textwrap
from datetime import datetime
from pathlib import Path

from impacts import IMPACTS
from pointers import FEATURES
from readout import FOLLOW_UP

COVER = Path(__file__).with_name("cover.pdf")
# The smallest readout the summary accepts. The image build renders it to fetch the TeX files.
SAMPLE = {
    "generated": "2026-01-01T00:00:00+00:00",
    "questionnaire_version": "0",
    "readout_version": "0",
    "environment": "e",
    "verdict": "v",
    "areas": [
        {
            "capability": "Human Access",
            "strength": "strong",
            "evidence": [
                {
                    "facet": "access path",
                    "answer": "a",
                    "rationale": "r",
                    "mitigation": "m",
                    "pointers": {"Boundary": ["Targets"]},
                }
            ],
        }
    ],
    "presented": ["Human Access"],
    "in_good_shape": ["Workload Lifecycle"],
    "patterns": [{"name": "n", "detail": "d"}],
    "unknowns": [{"question": "q"}],
    "implementation": None,
}
# Name of the summary in the application's bucket in MTA.
FILE = "healthcheck-summary.pdf"
TEMPLATE = "/opt/eisvogel.latex"
# Product marks as PDF, made by the image build. The summary shows a product's mark beside its next step.
LOGOS = Path("/opt/logos")


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


def aspect_table(heading, rows):
    """Returns a grid table with a heading across both columns, then a bold label and its text per row."""
    rows = [(f"**{item}**", value) for item, value in rows]
    label, width = max(len(item) for item, _ in rows), 72
    rule = f"+{'-' * (label + 2)}+{'-' * (width + 2)}+"
    lines = [f"+{'-' * (label + width + 5)}+", f"| {f'**{heading}**':<{label + width + 3}} |", rule.replace("-", "=")]
    for item, value in rows:
        # A list item's later lines are indented under its text, which keeps them in the item.
        wrapped = [
            line
            for text in (value if isinstance(value, list) else [value])
            for line in textwrap.wrap(text, width, subsequent_indent="  " if text.startswith("- ") else "")
        ]
        for number, line in enumerate(wrapped):
            lines.append(f"| {(item if number == 0 else ''):<{label}} | {line:<{width}} |")
        lines.append(rule)
    return lines


def mark(product):
    logo = LOGOS / f"{product}.pdf"
    return f"![]({logo}){{height=1.1em}} " if logo.exists() else ""


def footnote(url, noted):
    """Returns the mark for a documentation link: a footnote the first time, then that footnote's number again."""
    if url not in noted:
        # The summary has no other footnotes, so the nth link is footnote n.
        noted[url] = len(noted) + 1
        # Inside another macro's argument, url wants # and % escaped.
        return f"`\\footnote{{\\url{{{url.replace('#', '\\#').replace('%', '\\%')}}}}}`{{=latex}}"
    return f"`\\footnotemark[{noted[url]}]`{{=latex}}"


def needspace(count):
    return ["", f"\\needspace{{{count}\\baselineskip}}", ""]


def markdown(organisation, readout):
    generated = datetime.fromisoformat(readout["generated"])
    day = f"{generated.day} {generated:%B %Y}"
    areas = readout["areas"]
    # DESIGN.md section 4.7: the respondent sees the strongest tier. MTA holds every area.
    presented = [a for a in areas if a["capability"] in readout["presented"]]
    lines = [
        "---",
        f"title: {json.dumps(organisation)}",
        'subtitle: "5 Minute HashiCorp Healthcheck"',
        f"date: {json.dumps(day)}",
        f"subject: {json.dumps(f'questionnaire {readout["questionnaire_version"]}, readout {readout["readout_version"]}')}",
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
        # Bullets in the summary table line up with the plain text in the rows above them.
        "  - \\usepackage{enumitem}",
        "  - \\usepackage{etoolbox}",
        "  - \\AtBeginEnvironment{longtable}{\\setlist[itemize]{leftmargin=1.1em}}",
        # A long table repeats its header when it runs over a page. Ending every row the way the
        # starred row end does forbids a break inside a table, so one that does not fit moves whole.
        "  - |",
        "    ```{=latex}",
        "    \\makeatletter",
        "    \\def\\LT@tabularcr{\\relax\\iffalse{\\fi\\ifnum0=`}\\fi"
        "\\def\\crcr{\\LT@crcr\\noalign{\\nobreak}}\\let\\cr\\crcr\\LT@t@bularcr}",
        "    \\makeatother",
        "    ```",
        "---",
        "",
        "# Introduction",
        "",
        f"This document summarises what {escaped(organisation)} told HashiCorp during a 5 Minute HashiCorp "
        f"Healthcheck on {day}. The healthcheck asks eighteen questions about how infrastructure is "
        "delivered, secured, connected and run.",
        "",
    ]
    if areas:
        lines += [
            "These results come from a short questionnaire and show where further discussion would benefit "
            f"{escaped(organisation)}. Each response that highlighted an opportunity for improvement was triaged, "
            "and the highest priority areas have been captured in this report.",
            "",
        ]
    else:
        lines += ["These results come from a short questionnaire. No areas were highlighted.", ""]
    lines += summary_table([
        ("Environment", readout["environment"]),
        ("Areas highlighted", [f"- {a['capability']} ({a['strength']})" for a in areas] or "None"),
        ("Not highlighted", [f"- {c}" for c in readout["in_good_shape"]] or "None"),
    ])
    for number, area in enumerate(presented):
        tables = [
            aspect_table(
                e["facet"].capitalize(),
                [
                    ("Your response", e["answer"]),
                    ("What this means", e["rationale"]),
                    ("Suggested change", e["mitigation"]),
                    (
                        "Business impact",
                        [f"- *{d.capitalize()}.* {text}" for d, text in IMPACTS[e["facet"]]["impacts"].items()],
                    ),
                ],
            )
            for e in area["evidence"]
        ]
        if number == 0:
            # Starts the section where its first table fits, at about a line per line of the table's source.
            lines += needspace(len(tables[0]) + 10)
            lines += ["# What was highlighted", ""]
            if len(presented) < len(areas):
                lines += [
                    "This section covers the areas with a strong signal, which are the highest priority. The areas "
                    "with a moderate signal are open for a later discussion.",
                    "",
                ]
            elif presented[0]["strength"] == "strong":
                lines += ["Every area highlighted has a strong signal and is covered below.", ""]
            else:
                lines += ["No area has a strong signal, so this section covers the areas with a moderate signal.", ""]
        lines += [f"## {area['capability']}", ""]
        for table in tables:
            lines += [*table, ""]
    if readout["patterns"]:
        lines += ["", "# Patterns across areas", ""]
        lines += [f"- **{p['name']}.** {p['detail']}" for p in readout["patterns"]]
    if readout["unknowns"]:
        lines += ["", "# Not answered", ""]
        lines += [f"- {u['question']}" for u in readout["unknowns"]]
    if areas:
        lines += needspace(8)
        lines += ["# Suggested next steps", ""]
    noted = {}
    for number, area in enumerate(presented, 1):
        follow_up = FOLLOW_UP[area["capability"]]
        editions = f", in {follow_up['editions']}" if "editions" in follow_up else ""
        lines += [
            f"{number}. {mark(follow_up['product'])}**{area['capability']}.** A follow-up session on "
            f"{follow_up['product']} is recommended. The features it would cover{editions}:",
            "",
        ]
        # The features sit under the step, indented from it.
        lines += ["    ```{=latex}", "    \\begin{list}{}{\\setlength{\\leftmargin}{1.5em}\\setlength{\\topsep}{0pt}}\\item[]", "    ```", ""]
        shown = set()
        for e in area["evidence"]:
            sentences = []
            for name in (f for features in e["pointers"].values() for f in features):
                if name in shown:
                    continue
                shown.add(name)
                sentence, url = FEATURES[name]
                sentences.append(sentence + footnote(url, noted))
            if sentences:
                lines += [f"    **{e['facet'].capitalize()}.** {' '.join(sentences)}", ""]
        lines += ["    ```{=latex}", "    \\end{list}", "    ```", ""]
        roles = ", ".join(role[0].lower() + role[1:] for role in follow_up["roles"])
        lines += [f"    Worth involving: {roles}.", ""]
    if readout["implementation"]:
        product = FOLLOW_UP[readout["implementation"]["capability"]]["product"]
        lines += [
            f"{mark(product)}Changes in the areas above are usually delivered as code, which makes {product} "
            "relevant to those sessions.",
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
