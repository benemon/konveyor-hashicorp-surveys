"""End-to-end check of a running environment: BASE=https://localhost:8443 python3 kind/e2e.py

Creates one respondent per persona through Healthcheck Console, answers it through the hub,
generates its readout and checks that what MTA holds and what the summary prints follow from
the answers chosen. E2E_CLEAR=1 also exercises delete-all, which removes every respondent in
the environment. The summary's text is checked when pdftotext is installed.
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
PDFTOTEXT = shutil.which("pdftotext")


def tags(answer, category):
    return {t["tag"] for t in answer.get("applyTags", []) if t["category"] == category}


def expected(persona):
    """What the persona's answers establish, read from the questionnaire alone."""
    gaps, unknowns, greens = [], [], []
    for question, chosen in zip(QUESTIONS, persona["answers"]):
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


def body(extracted, organisation):
    """The summary's text without footnotes, running headers and page numbers, which pdftotext
    interleaves with a sentence that runs over a page break."""
    kept = []
    for line in extracted.splitlines():
        furniture = re.match(r"(\d+)?https?://", line) or line.strip().isdigit() or line.startswith(organisation)
        if not furniture:
            kept.append(line)
    return squash("\n".join(kept))


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


def respond(persona):
    """Starts the persona's assessment, answers it and generates its readout; returns the console's state."""
    started = console("assessments", "POST", {"organisation": PREFIX + persona["name"], "email": "e2e@example.com"})
    assessment = hub(f"assessments/{started['assessment']}")
    for question, chosen in zip((q for s in assessment["sections"] for q in s["questions"]), persona["answers"]):
        for answer in question["answers"]:
            answer["selected"] = answer["order"] == chosen
    hub(f"assessments/{started['assessment']}", "PUT", assessment)
    task = console("readouts", "POST", {"organisation": PREFIX + persona["name"]})["task"]
    for _ in range(90):
        state = console(f"readouts/{task}")
        if state["state"] in ("Succeeded", "Failed", "Canceled"):
            return started["application"], state
        time.sleep(2)
    raise TimeoutError(f"readout task {task} did not finish")


class Environment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = {p["name"]: respond(p) for p in PERSONAS}

    def entries(self, application):
        entries = hub(f"applications/{application}/analysis/insights") or []
        return (
            [e for e in entries if e.get("effort")],
            [e for e in entries if not e.get("effort") and e["category"] in ("High", "Medium")],
            [e for e in entries if e["category"] == "Pattern"],
            [e for e in entries if e["category"] == "Adjacent"],
        )

    def check_gap_entry(self, entry, gap):
        self.assertEqual(entry["name"], f"{gap['facet'].capitalize()}: {gap['answer']}")
        self.assertEqual([i["message"] for i in entry["incidents"]], [f"{gap['question']} {gap['answer']}"])
        self.assertIn(f"konveyor.io/target={gap['capability']}", entry["labels"])
        self.assertIn(f"konveyor.io/target={gap['product']}", entry["labels"])
        self.assertIn(gap["rationale"], entry["description"])
        self.assertIn(f"**Suggested change:** {gap['mitigation']}", entry["description"])
        for product, features in gap["pointers"].items():
            self.assertIn(f"**{product}**", entry["description"])
            for name in features:
                sentence, url = FEATURES[name]
                self.assertIn(f"- **{name}.** {sentence} [Documentation]({url})", entry["description"])

    def test_console_lists_the_questionnaire(self):
        self.assertIn(QUESTIONNAIRE["name"], console("questionnaires"))

    def test_readout_reports_the_signals_the_answers_establish(self):
        for persona in PERSONAS:
            gaps, _, _ = expected(persona)
            application, state = self.results[persona["name"]]
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
            gaps, _, greens = expected(persona)
            application, _ = self.results[persona["name"]]
            issues, insights, _, _ = self.entries(application)
            with self.subTest(persona["name"]):
                for entries in (issues, insights):
                    self.assertEqual(
                        sorted(e["rule"].removesuffix(" (issue)") for e in entries), sorted(g["key"] for g in gaps)
                    )
                    for gap in gaps:
                        self.check_gap_entry(next(e for e in entries if e["rule"].startswith(gap["key"])), gap)
                for entry in issues + insights:
                    for green in greens:
                        self.assertNotIn(green, entry["name"])

    def test_pattern_and_adjacent_insights_name_the_answers_behind_them(self):
        for persona in PERSONAS:
            gaps, _, _ = expected(persona)
            application, _ = self.results[persona["name"]]
            _, _, patterns, adjacent = self.entries(application)
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
            gaps, unknowns, _ = expected(persona)
            application, _ = self.results[persona["name"]]
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

    def test_summary_prints_the_presented_answers_and_their_next_steps(self):
        for persona in PERSONAS:
            gaps, unknowns, greens = expected(persona)
            application, _ = self.results[persona["name"]]
            pdf = console(f"summaries/{application}", raw=True)
            with self.subTest(persona["name"]):
                self.assertTrue(pdf.startswith(b"%PDF-"))
                if not PDFTOTEXT:
                    self.skipTest("pdftotext is not installed; the summary's text is not checked")
                extracted = subprocess.run([PDFTOTEXT, "-raw", "-", "-"], input=pdf, capture_output=True, check=True)
                everything = squash(extracted.stdout.decode())
                text = body(extracted.stdout.decode(), PREFIX + persona["name"])
                self.assertIn(squash(PREFIX + persona["name"]), everything)
                for capability, strength in persona["direct"].items():
                    self.assertIn(squash(f"{capability} ({strength})"), text)
                for question in unknowns:
                    self.assertIn(squash(question), text)
                for gap in gaps:
                    shown = gap["capability"] in persona["presented"]
                    self.assertEqual(squash(gap["rationale"]) in text, shown, gap["key"])
                    self.assertEqual(squash(gap["mitigation"]) in text, shown, gap["key"])
                    if shown:
                        self.assertIn(squash(gap["answer"]), text, gap["key"])
                        for features in gap["pointers"].values():
                            for name in features:
                                sentence, url = FEATURES[name]
                                self.assertIn(squash(sentence), text, name)
                                self.assertIn(squash(url), everything, name)
                for capability in persona["presented"]:
                    follow_up = readout.FOLLOW_UP[capability]
                    self.assertIn(squash(f"A follow-up session on {follow_up['product']} is recommended"), text)
                    self.assertIn(squash("Worth involving: " + ", ".join(follow_up["roles"])), text)
                for green in greens:
                    self.assertNotIn(squash(green), text)
                self.assertEqual(squash("Suggested next steps") in text, bool(gaps))

    def test_respondents_and_csv_list_every_persona(self):
        listed = {r["organisation"]: r for r in console("respondents")}
        rows = list(csv.reader(io.StringIO(console("respondents.csv", raw=True).decode())))
        self.assertEqual(rows[0][:4], ["Organisation", "Contact", "Assessment completed", "Readout generated"])
        exported = {row[0]: row for row in rows[1:]}
        for persona in PERSONAS:
            with self.subTest(persona["name"]):
                row = listed[PREFIX + persona["name"]]
                self.assertTrue(row["completed"])
                self.assertTrue(row["generated"])
                self.assertEqual(row["readout_version"], readout.VERSION)
                self.assertEqual(row["direct"], persona["direct"])
                self.assertEqual(exported[PREFIX + persona["name"]][1:3], ["e2e@example.com", "yes"])
        self.assertIn(PREFIX + PERSONAS[0]["name"], console("organisations"))

    def test_zz_delete_one_then_optionally_all(self):
        application, _ = self.results[PERSONAS[0]["name"]]
        self.assertEqual(console(f"respondents/{application}", "DELETE"), {"removed": application})
        self.assertNotIn(application, {r["application"] for r in console("respondents")})
        self.assertEqual(hub(f"tasks?filter=application.id=={application}"), [])
        if os.environ.get("E2E_CLEAR") == "1":
            removed = console("respondents", "DELETE", {"confirm": "delete all respondents"})["removed"]
            self.assertGreaterEqual(removed, len(PERSONAS) - 1)
            self.assertEqual(console("respondents"), [])
            self.assertEqual(hub("tasks?filter=application.id>0&limit=500"), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
