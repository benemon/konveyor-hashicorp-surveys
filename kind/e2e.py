"""End-to-end check of a running environment: BASE=https://localhost:8443 python3 kind/e2e.py

Creates one respondent per persona through Healthcheck Console, answers it through the hub,
generates its readout and checks what MTA holds. E2E_CLEAR=1 also exercises delete-all, which
removes every respondent in the environment.
"""

import csv
import io
import json
import os
import ssl
import sys
import time
import unittest
import urllib.request
from pathlib import Path

import yaml

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "healthcheck-readout"))
import readout  # noqa: E402
from pointers import FEATURES  # noqa: E402

BASE = os.environ.get("BASE", "https://localhost:8443")
PREFIX = "E2E "
CONTEXT = ssl._create_unverified_context()
PERSONAS = yaml.safe_load((HERE.parent / "hashicorp-healthcheck" / "personas.yaml").read_text())
QUESTIONNAIRE = yaml.safe_load((HERE.parent / "hashicorp-healthcheck" / "questionnaire.yaml").read_text())
QUESTIONS = [q for s in QUESTIONNAIRE["sections"] for q in s["questions"]]
QUESTIONNAIRE_VERSION = next(
    t["tag"] for t in QUESTIONS[0]["answers"][0]["applyTags"] if t["category"] == readout.QUESTIONNAIRE_VERSION
)


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


def risks(persona):
    return [next(a["risk"] for a in q["answers"] if a["order"] == n) for q, n in zip(QUESTIONS, persona["answers"])]


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

    def test_console_lists_the_questionnaire(self):
        self.assertIn(QUESTIONNAIRE["name"], console("questionnaires"))

    def test_every_readout_succeeds_with_the_persona_s_signals(self):
        for persona in PERSONAS:
            application, state = self.results[persona["name"]]
            with self.subTest(persona["name"]):
                self.assertEqual(state["state"], "Succeeded", state["errors"])
                self.assertEqual({a["capability"]: a["strength"] for a in state["areas"]}, persona["direct"])
                for area in state["areas"]:
                    self.assertEqual(area["product"], readout.FOLLOW_UP[area["capability"]]["product"])
                self.assertEqual({p["name"] for p in state["patterns"]}, set(persona["patterns"]))
                self.assertEqual(state["issues"], sum(r in ("red", "yellow") for r in risks(persona)))

    def test_mta_computes_the_persona_s_overall_result(self):
        for persona in PERSONAS:
            application, _ = self.results[persona["name"]]
            with self.subTest(persona["name"]):
                self.assertEqual(hub(f"applications/{application}")["risk"], persona["overall"])

    def test_facts_carry_the_versions_and_the_adjacent_signals(self):
        for persona in PERSONAS:
            application, _ = self.results[persona["name"]]
            facts = hub(f"applications/{application}/facts/healthcheck-readout:")
            with self.subTest(persona["name"]):
                self.assertEqual(facts["readout_version"], readout.VERSION)
                self.assertEqual(facts["questionnaire_version"], QUESTIONNAIRE_VERSION)
                self.assertEqual({a["capability"] for a in facts["adjacent"]}, set(persona["adjacent"]))
                self.assertTrue(all(u.keys() == {"question"} for u in facts["unknowns"]))

    def test_issues_and_insights_follow_the_design(self):
        for persona in PERSONAS:
            application, state = self.results[persona["name"]]
            facts = hub(f"applications/{application}/facts/healthcheck-readout:")
            entries = hub(f"applications/{application}/analysis/insights") or []
            gaps = [e for a in facts["areas"] for e in a["evidence"]]
            with self.subTest(persona["name"]):
                self.assertEqual(len(entries), 2 * len(gaps) + len(facts["patterns"]) + len(facts["adjacent"]))
                issues = [e for e in entries if e.get("effort")]
                insights = [e for e in entries if not e.get("effort")]
                self.assertEqual(len(issues), len(gaps))
                self.assertEqual(sum(e["category"] == "Pattern" for e in insights), len(facts["patterns"]))
                self.assertEqual(sum(e["category"] == "Adjacent" for e in insights), len(facts["adjacent"]))
                for gap in gaps:
                    entry = next(e for e in issues if e["rule"] == f"{gap['key']} (issue)")
                    labels = set(entry["labels"])
                    area = next(a for a in facts["areas"] if gap in a["evidence"])
                    self.assertIn(f"konveyor.io/target={area['capability']}", labels)
                    self.assertIn(f"konveyor.io/target={area['product']}", labels)
                    self.assertIn(gap["rationale"], entry["description"])
                    self.assertIn(f"**Suggested change:** {gap['mitigation']}", entry["description"])
                    self.assertIn("##### Features for the follow-up session", entry["description"])
                    for product, features in gap["pointers"].items():
                        self.assertIn(f"**{product}**", entry["description"])
                        for name in features:
                            sentence, url = FEATURES[name]
                            self.assertIn(f"- **{name}.** {sentence} [Documentation]({url})", entry["description"])
                    self.assertNotIn("Direction", entry["description"])

    def test_summary_is_a_pdf(self):
        for persona in PERSONAS:
            application, _ = self.results[persona["name"]]
            with self.subTest(persona["name"]):
                pdf = console(f"summaries/{application}", raw=True)
                self.assertTrue(pdf.startswith(b"%PDF-"))
                # Without a cover file the smallest summary is about 16 KB.
                self.assertGreater(len(pdf), 10_000)

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
        self.assertFalse([t for t in hub("tasks") if (t.get("application") or {}).get("id") == application])
        if os.environ.get("E2E_CLEAR") == "1":
            removed = console("respondents", "DELETE", {"confirm": "delete all respondents"})["removed"]
            self.assertGreaterEqual(removed, len(PERSONAS) - 1)
            self.assertEqual(console("respondents"), [])
            self.assertFalse([t for t in hub("tasks") if t.get("application")])


if __name__ == "__main__":
    unittest.main(verbosity=2)
