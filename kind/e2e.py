"""End-to-end check of a running environment: BASE=https://localhost:8443 python3 kind/e2e.py

Creates one respondent per persona, and one per red or yellow answer on an all-green baseline,
through Healthcheck Console; answers each through the hub; generates its readout; and checks
that what MTA holds and what the summary prints follow from the answers chosen. E2E_CLEAR=1
also exercises delete-all, which removes every respondent in the environment. The summary's
text is checked when pdftotext is installed.
"""

import csv
import io
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import time
import unittest
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "healthcheck-readout"))
import readout  # noqa: E402
from pointers import FEATURES, POINTERS  # noqa: E402

BASE = os.environ.get("BASE", "https://localhost:8443")
PREFIX = "E2E "
CONTEXT = ssl._create_unverified_context()
PERSONAS = yaml.safe_load((HERE.parent / "hashicorp-healthcheck" / "personas.yaml").read_text())
QUESTIONNAIRE = yaml.safe_load((HERE.parent / "hashicorp-healthcheck" / "questionnaire.yaml").read_text())
QUESTIONS = [q for s in QUESTIONNAIRE["sections"] for q in s["questions"]]
BASELINE = next(p for p in PERSONAS if p["name"].startswith("D"))["answers"]
PDFTOTEXT = shutil.which("pdftotext")


def organisation(persona):
    return f"{PREFIX}persona {persona['name'][0]}"
TABLE_HEADER = "Aspect Response What this means Suggested change"


def tags(answer, category):
    return {t["tag"] for t in answer.get("applyTags", []) if t["category"] == category}


def expected(answers):
    """What a set of answers establishes, read from the questionnaire alone."""
    gaps, unknowns, greens = [], [], []
    for question, chosen in zip(QUESTIONS, answers):
        answer = next(a for a in question["answers"] if a["order"] == chosen)
        if answer["risk"] in ("red", "yellow"):
            key = next(iter(tags(answer, readout.KEY)))
            capability = next(iter(tags(answer, readout.DIRECT)))
            gaps.append(
                {
                    "key": key,
                    "facet": key.split(": ")[0],
                    "question": question["text"],
                    "answer": answer["text"],
                    "risk": answer["risk"],
                    "rationale": answer["rationale"],
                    "mitigation": answer["mitigation"],
                    "capability": capability,
                    "adjacent": tags(answer, readout.ADJACENT),
                    "product": readout.FOLLOW_UP[capability]["product"],
                    "pointers": POINTERS[key],
                }
            )
        elif answer["risk"] == "unknown":
            unknowns.append(question["text"])
        elif question is not QUESTIONS[0]:
            greens.append(answer["text"])
    return gaps, unknowns, greens


def squash(text):
    """Letters and digits only, so wrapped, hyphenated or re-quoted text still matches."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def call(path, method="GET", body=None, raw=False):
    request = urllib.request.Request(
        BASE + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, context=CONTEXT, timeout=120) as response:
        data = response.read()
        return data if raw else (json.loads(data) if data else None)


def console(path, method="GET", body=None, raw=False):
    return call("/console/api/" + path, method, body, raw)


def hub(path, method="GET", body=None):
    return call("/hub/" + path, method, body)


def respond(name, answers):
    """Starts an assessment, answers it and generates its readout; returns the application and the console's state."""
    started = console("assessments", "POST", {"organisation": name, "email": "e2e@example.com"})
    assessment = hub(f"assessments/{started['assessment']}")
    for question, chosen in zip((q for s in assessment["sections"] for q in s["questions"]), answers):
        for answer in question["answers"]:
            answer["selected"] = answer["order"] == chosen
    hub(f"assessments/{started['assessment']}", "PUT", assessment)
    task = console("readouts", "POST", {"organisation": name})["task"]
    for _ in range(120):
        state = console(f"readouts/{task}")
        if state["state"] in ("Succeeded", "Failed", "Canceled"):
            return started["application"], state
        time.sleep(2)
    raise TimeoutError(f"readout task {task} did not finish")


def respond_all(cases):
    with ThreadPoolExecutor(4) as pool:
        return dict(zip(cases, pool.map(lambda c: respond(c, cases[c]), cases)))


def entries(application):
    """The application's analysis entries: Issues, gap Insights, pattern Insights, adjacent Insights."""
    found = hub(f"applications/{application}/analysis/insights") or []
    return (
        [e for e in found if e.get("effort")],
        [e for e in found if not e.get("effort") and e["category"] in ("High", "Medium")],
        [e for e in found if e["category"] == "Pattern"],
        [e for e in found if e["category"] == "Adjacent"],
    )


class Summary:
    """The summary's text as pdftotext extracts it, with the footnotes read into a table and the
    running headers and page numbers removed, so a sentence that runs over a page break still reads
    as one."""

    def __init__(self, pdf, organisation):
        raw = subprocess.run([PDFTOTEXT, "-raw", "-", "-"], input=pdf, capture_output=True, check=True).stdout.decode()
        lines = raw.splitlines()
        self.notes, kept, note = {}, [], None
        for number, line in enumerate(lines):
            following = lines[number + 1] if number + 1 < len(lines) else ""
            if line.strip().isdigit() and following.startswith("http"):
                note = int(line)
                self.notes[note] = following
            elif line.startswith("http") or line.strip().isdigit() or line.startswith(organisation):
                continue
            elif note and " " not in line and len(self.notes[note]) > 90:
                # A footnote URL wrapped at the margin continues on the next line.
                self.notes[note] += line
                note = None
            else:
                note = None
                kept.append(line)
        self.text = squash("\n".join(kept))
        self.everything = squash(raw)

    def find(self, text, start=0):
        return self.text.find(squash(text), start)

    def note_after(self, sentence):
        """The footnote number printed after a sentence, or None."""
        position = self.find(sentence)
        if position < 0:
            return None
        digits = re.match(r"\d+", self.text[position + len(squash(sentence)) :])
        return int(digits.group()) if digits else None


def check_gap_entry(test, entry, gap):
    test.assertEqual(entry["name"], f"{gap['facet'].capitalize()}: {gap['answer']}")
    test.assertEqual([i["message"] for i in entry["incidents"]], [f"{gap['question']} {gap['answer']}"])
    test.assertIn(f"konveyor.io/target={gap['capability']}", entry["labels"])
    test.assertIn(f"konveyor.io/target={gap['product']}", entry["labels"])
    test.assertIn(gap["rationale"], entry["description"])
    test.assertIn(f"**Suggested change:** {gap['mitigation']}", entry["description"])
    for product, features in gap["pointers"].items():
        test.assertIn(f"**{product}**", entry["description"])
        for name in features:
            sentence, url = FEATURES[name]
            test.assertIn(f"- **{name}.** {sentence} [Documentation]({url})", entry["description"])


def check_summary(test, pdf, organisation, direct, presented, gaps, unknowns, greens):
    """The summary prints the presented areas in order, each gap under its own area, the next steps in
    the same order with every feature sentence footnoted to its page, the unknown questions, and no
    green answer."""
    test.assertTrue(pdf.startswith(b"%PDF-"))
    if not PDFTOTEXT:
        test.skipTest("pdftotext is not installed; the summary's text is not checked")
    summary = Summary(pdf, organisation)
    test.assertIn(squash(organisation), summary.everything)
    for capability, strength in direct.items():
        test.assertIn(squash(f"{capability} ({strength})"), summary.text)
    for question in unknowns:
        test.assertIn(squash(question), summary.text)
    for green in greens:
        test.assertNotIn(squash(green), summary.text)
    test.assertEqual(summary.find("Suggested next steps") >= 0, bool(gaps))
    if not gaps:
        return
    headings = [summary.find(f"{c} {TABLE_HEADER}") for c in presented]
    steps = [
        summary.find(f"{n}. {c}. A follow-up session on {readout.FOLLOW_UP[c]['product']} is recommended")
        for n, c in enumerate(presented, 1)
    ]
    sequence = [summary.find("What was highlighted"), *headings, summary.find("Suggested next steps"), *steps]
    test.assertGreaterEqual(min(sequence), 0, presented)
    test.assertEqual(sequence, sorted(sequence), presented)
    end = len(summary.text)
    for gap in gaps:
        shown = gap["capability"] in presented
        test.assertEqual(summary.find(gap["rationale"]) >= 0, shown, gap["key"])
        test.assertEqual(summary.find(gap["mitigation"]) >= 0, shown, gap["key"])
        if not shown:
            continue
        index = presented.index(gap["capability"])
        low, high = headings[index], (headings + [steps[0]])[index + 1]
        for field in ("answer", "rationale", "mitigation"):
            test.assertTrue(low < summary.find(gap[field]) < high, (gap["key"], field))
        low, high = steps[index], (steps + [end])[index + 1]
        for features in gap["pointers"].values():
            for name in features:
                sentence, url = FEATURES[name]
                test.assertTrue(low < summary.find(sentence) < high, (gap["key"], name))
                test.assertEqual(summary.notes.get(summary.note_after(sentence)), url, (gap["key"], name))
    for index, capability in enumerate(presented):
        roles = "Worth involving: " + ", ".join(readout.FOLLOW_UP[capability]["roles"])
        test.assertTrue(steps[index] < summary.find(roles) < (steps + [end])[index + 1], capability)
    cited = {FEATURES[n][1] for g in gaps if g["capability"] in presented for fs in g["pointers"].values() for n in fs}
    test.assertEqual(sorted(summary.notes.values()), sorted(cited))


class Personas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = respond_all({organisation(p): p["answers"] for p in PERSONAS})

    def test_console_lists_the_questionnaire(self):
        self.assertIn(QUESTIONNAIRE["name"], console("questionnaires"))

    def test_readout_reports_the_signals_the_answers_establish(self):
        for persona in PERSONAS:
            gaps, _, _ = expected(persona["answers"])
            application, state = self.results[organisation(persona)]
            with self.subTest(persona["name"]):
                self.assertEqual(state["state"], "Succeeded", state["errors"])
                self.assertEqual({a["capability"]: a["strength"] for a in state["areas"]}, persona["direct"])
                self.assertEqual(
                    {a["capability"]: a["product"] for a in state["areas"]},
                    {g["capability"]: g["product"] for g in gaps},
                )
                self.assertEqual({p["name"] for p in state["patterns"]}, set(persona["patterns"]))
                self.assertEqual(state["issues"], len(gaps))
                self.assertEqual(hub(f"applications/{application}")["risk"], persona["overall"])

    def test_issues_and_insights_are_exactly_the_red_and_yellow_answers(self):
        for persona in PERSONAS:
            gaps, _, greens = expected(persona["answers"])
            application, _ = self.results[organisation(persona)]
            issues, insights, _, _ = entries(application)
            with self.subTest(persona["name"]):
                for found in (issues, insights):
                    self.assertEqual(
                        sorted(e["rule"].removesuffix(" (issue)") for e in found), sorted(g["key"] for g in gaps)
                    )
                    for gap in gaps:
                        check_gap_entry(self, next(e for e in found if e["rule"].startswith(gap["key"])), gap)
                for entry in issues + insights:
                    for green in greens:
                        self.assertNotIn(green, entry["name"])

    def test_pattern_and_adjacent_insights_name_the_answers_behind_them(self):
        for persona in PERSONAS:
            gaps, _, _ = expected(persona["answers"])
            application, _ = self.results[organisation(persona)]
            _, _, patterns, adjacent = entries(application)
            with self.subTest(persona["name"]):
                self.assertEqual(
                    sorted(e["name"] for e in patterns), sorted(f"Pattern: {p}" for p in persona["patterns"])
                )
                for entry in patterns:
                    definition = next(p for p in readout.PATTERNS if entry["name"] == f"Pattern: {p['name']}")
                    self.assertIn(definition["detail"], entry["description"])
                    for facet in definition["all"]:
                        self.assertIn(f"- **{facet.capitalize()}**: ", entry["description"])
                self.assertEqual({e["name"] for e in adjacent}, {f"Adjacent signal: {c}" for c in persona["adjacent"]})
                for entry in adjacent:
                    capability = entry["name"].removeprefix("Adjacent signal: ")
                    sources = [g for g in gaps if capability in g["adjacent"]]
                    self.assertTrue(sources, capability)
                    for gap in sources:
                        self.assertIn(f"- **{gap['facet'].capitalize()}**: {gap['answer']}.", entry["description"])
                        self.assertIn(f"Derived from responses given under {gap['capability']}", entry["description"])

    def test_facts_follow_the_answers(self):
        for persona in PERSONAS:
            gaps, unknowns, _ = expected(persona["answers"])
            application, _ = self.results[organisation(persona)]
            facts = hub(f"applications/{application}/facts/healthcheck-readout:")
            with self.subTest(persona["name"]):
                self.assertEqual(facts["readout_version"], readout.VERSION)
                self.assertEqual(
                    facts["questionnaire_version"],
                    next(iter(tags(QUESTIONS[0]["answers"][0], readout.QUESTIONNAIRE_VERSION))),
                )
                self.assertEqual([u["question"] for u in facts["unknowns"]], unknowns)
                self.assertEqual(
                    sorted(e["key"] for a in facts["areas"] for e in a["evidence"]), sorted(g["key"] for g in gaps)
                )
                self.assertEqual({a["capability"] for a in facts["adjacent"]}, set(persona["adjacent"]))

    def test_summary_prints_the_presented_answers_in_order_with_their_next_steps(self):
        for persona in PERSONAS:
            gaps, unknowns, greens = expected(persona["answers"])
            application, _ = self.results[organisation(persona)]
            with self.subTest(persona["name"]):
                check_summary(
                    self,
                    console(f"summaries/{application}", raw=True),
                    organisation(persona),
                    persona["direct"],
                    persona["presented"],
                    gaps,
                    unknowns,
                    greens,
                )

    def test_respondents_and_csv_list_every_persona(self):
        listed = {r["organisation"]: r for r in console("respondents")}
        rows = list(csv.reader(io.StringIO(console("respondents.csv", raw=True).decode())))
        self.assertEqual(rows[0][:4], ["Organisation", "Contact", "Assessment completed", "Readout generated"])
        exported = {row[0]: row for row in rows[1:]}
        for persona in PERSONAS:
            with self.subTest(persona["name"]):
                row = listed[organisation(persona)]
                self.assertTrue(row["completed"])
                self.assertTrue(row["generated"])
                self.assertEqual(row["readout_version"], readout.VERSION)
                self.assertEqual(row["direct"], persona["direct"])
                self.assertEqual(exported[organisation(persona)][1:3], ["e2e@example.com", "yes"])
        self.assertIn(organisation(PERSONAS[0]), console("organisations"))

    def test_zz_delete_one_then_optionally_all(self):
        application, _ = self.results[organisation(PERSONAS[0])]
        self.assertEqual(console(f"respondents/{application}", "DELETE"), {"removed": application})
        self.assertNotIn(application, {r["application"] for r in console("respondents")})
        self.assertEqual(hub(f"tasks?filter=application.id=={application}"), [])
        if os.environ.get("E2E_CLEAR") == "1":
            removed = console("respondents", "DELETE", {"confirm": "delete all respondents"})["removed"]
            self.assertGreaterEqual(removed, len(PERSONAS) - 1)
            self.assertEqual(console("respondents"), [])
            self.assertEqual(hub("tasks?filter=application.id>0&limit=500"), [])


class SingleGaps(unittest.TestCase):
    """Each red or yellow answer on its own, against the all-green baseline of persona D."""

    @classmethod
    def setUpClass(cls):
        cls.cases = {}
        for index, question in enumerate(QUESTIONS):
            for answer in question["answers"]:
                if answer["risk"] in ("red", "yellow"):
                    key = next(iter(tags(answer, readout.KEY)))
                    cls.cases[f"{PREFIX}gap {key}"] = BASELINE[:index] + [answer["order"]] + BASELINE[index + 1 :]
        cls.results = respond_all(cls.cases)

    @classmethod
    def tearDownClass(cls):
        for application, _ in cls.results.values():
            console(f"respondents/{application}", "DELETE")

    def test_each_answer_alone_lands_as_exactly_its_own_gap(self):
        for name, answers in self.cases.items():
            (gap,), unknowns, _ = expected(answers)
            application, state = self.results[name]
            with self.subTest(gap["key"]):
                self.assertEqual(state["state"], "Succeeded", state["errors"])
                strength = "strong" if gap["risk"] == "red" else "moderate"
                self.assertEqual({a["capability"]: a["strength"] for a in state["areas"]}, {gap["capability"]: strength})
                self.assertEqual(state["issues"], 1)
                issues, insights, patterns, adjacent = entries(application)
                for found in (issues, insights):
                    self.assertEqual([e["rule"].removesuffix(" (issue)") for e in found], [gap["key"]])
                    check_gap_entry(self, found[0], gap)
                for entry in patterns:
                    self.assertIn(f"- **{gap['facet'].capitalize()}**: {gap['answer']}", entry["description"])
                self.assertEqual({e["name"] for e in adjacent}, {f"Adjacent signal: {c}" for c in gap["adjacent"]})
                facts = hub(f"applications/{application}/facts/healthcheck-readout:")
                self.assertEqual([e["key"] for a in facts["areas"] for e in a["evidence"]], [gap["key"]])
                self.assertEqual(facts["unknowns"], [])

    def test_each_answer_alone_prints_one_area(self):
        for name, answers in self.cases.items():
            (gap,), _, greens = expected(answers)
            application, _ = self.results[name]
            with self.subTest(gap["key"]):
                check_summary(
                    self,
                    console(f"summaries/{application}", raw=True),
                    name,
                    {gap["capability"]: "strong" if gap["risk"] == "red" else "moderate"},
                    [gap["capability"]],
                    [gap],
                    [],
                    greens,
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
