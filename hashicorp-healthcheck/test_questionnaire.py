import copy
import re
import sys
import unittest
from collections import Counter
from pathlib import Path

import yaml

HERE = Path(__file__).parent
# The addon's logic is the single implementation of the signal model.
sys.path.insert(0, str(HERE.parent / "healthcheck-readout"))
import readout  # noqa: E402
import summary  # noqa: E402
from readout import ADJACENCY, ADJACENT, CAPABILITIES, DIRECT, FOLLOW_UP, KEY, QUESTIONNAIRE_VERSION, tags  # noqa: E402

QUESTIONNAIRE = yaml.safe_load((HERE / "questionnaire.yaml").read_text())
PERSONAS = yaml.safe_load((HERE / "personas.yaml").read_text())
QUESTIONS = [q for s in QUESTIONNAIRE["sections"] for q in s["questions"]]
CONTEXT, SCORED = QUESTIONS[0], QUESTIONS[1:]

# DESIGN.md section 4.4, by answer key.
CROSS_TAGS = {
    "access credentials: shared": {"Machine Identity and Secrets"},
    "service-to-service security: network-location": {"Machine Identity and Secrets"},
    "service-to-service security: manual-rules": {"Machine Identity and Secrets"},
}

PRODUCTS = re.compile(r"terraform|vault|boundary|consul|nomad|hashicorp", re.IGNORECASE)


def strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from strings(value)


def overall(risks):
    for colour in ("red", "yellow", "unknown"):
        if risks.count(colour) / len(risks) >= QUESTIONNAIRE["thresholds"][colour] / 100:
            return colour
    return "green"


def select(answers):
    sections = copy.deepcopy(QUESTIONNAIRE["sections"])
    for question, n in zip([q for s in sections for q in s["questions"]], answers):
        question["answers"][n - 1]["selected"] = True
    return sections


def evaluate(answers):
    result = readout.build(select(answers), "")
    implementation = result["implementation"]
    return {
        "direct": result["direct"],
        "presented": result["presented"],
        "adjacent": {a["capability"]: a["via"] for a in result["adjacent"]},
        "solution_adjacency": implementation["via"] if implementation else [],
        "patterns": [pattern["name"] for pattern in result["patterns"]],
        "overall": overall([q["answers"][n - 1]["risk"] for q, n in zip(QUESTIONS, answers)]),
    }


class Structure(unittest.TestCase):
    def test_schema(self):
        self.assertTrue(QUESTIONNAIRE["name"])
        self.assertIs(QUESTIONNAIRE["required"], True)
        self.assertEqual(set(QUESTIONNAIRE["thresholds"]), {"red", "yellow", "unknown"})
        self.assertEqual(set(QUESTIONNAIRE["riskMessages"]), {"red", "yellow", "green", "unknown"})
        sections = QUESTIONNAIRE["sections"]
        self.assertEqual([s["order"] for s in sections], list(range(1, len(sections) + 1)))
        for section in sections:
            self.assertTrue(section["name"])
            questions = section["questions"]
            self.assertEqual([q["order"] for q in questions], list(range(1, len(questions) + 1)))
            for question in questions:
                self.assertTrue(question["text"])
                self.assertTrue(question["explanation"])
                answers = question["answers"]
                self.assertEqual([a["order"] for a in answers], list(range(1, len(answers) + 1)))
                for answer in answers:
                    self.assertTrue(answer["text"])
                    self.assertIn(answer["risk"], {"red", "yellow", "green", "unknown"})
                    for tag in answer.get("applyTags", []):
                        self.assertIn(tag["category"], {DIRECT, ADJACENT, KEY, QUESTIONNAIRE_VERSION})
                        if tag["category"] in (DIRECT, ADJACENT):
                            self.assertIn(tag["tag"], CAPABILITIES)

    def test_context_question_carries_the_questionnaire_version(self):
        versions = {next(iter(tags(a, QUESTIONNAIRE_VERSION)), None) for a in CONTEXT["answers"]}
        self.assertEqual(len(versions), 1)
        self.assertIsNotNone(next(iter(versions)))
        for question in SCORED:
            for answer in question["answers"]:
                self.assertFalse(tags(answer, QUESTIONNAIRE_VERSION))

    def test_question_and_answer_counts(self):
        self.assertTrue(14 <= len(QUESTIONS) <= 16, len(QUESTIONS))
        for question in QUESTIONS:
            self.assertTrue(4 <= len(question["answers"]) <= 6, question["text"])

    def test_no_branching(self):
        for question in QUESTIONS:
            self.assertFalse({"includeFor", "excludeFor"} & set(question), question["text"])
            for answer in question["answers"]:
                self.assertNotIn("autoAnswerFor", answer, answer["text"])

    def test_context_question_is_green_and_carries_no_signal(self):
        for answer in CONTEXT["answers"]:
            self.assertEqual(answer["risk"], "green", answer["text"])
            self.assertFalse(tags(answer, DIRECT) | tags(answer, ADJACENT), answer["text"])

    def test_every_answer_has_one_key(self):
        facets, keys = [], []
        for question in QUESTIONS:
            found = [tags(a, KEY) for a in question["answers"]]
            for answer, key in zip(question["answers"], found):
                self.assertEqual(len(key), 1, answer["text"])
            keys += [k for key in found for k in key]
            question_facets = {k.split(": ")[0] for key in found for k in key}
            self.assertEqual(len(question_facets), 1, question["text"])
            facets += question_facets
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(len(facets), len(set(facets)))

    def test_patterns_use_existing_keys(self):
        keys = {k for q in QUESTIONS for a in q["answers"] for k in tags(a, KEY)}
        for pattern in readout.PATTERNS:
            for facet, wanted in (pattern["all"] | pattern.get("any", {})).items():
                for key in wanted:
                    self.assertIn(f"{facet}: {key}", keys, pattern["name"])

    def test_tags_only_on_red_and_yellow(self):
        for question in SCORED:
            capabilities = set()
            for answer in question["answers"]:
                if answer["risk"] in ("red", "yellow"):
                    self.assertEqual(len(tags(answer, DIRECT)), 1, answer["text"])
                    capabilities |= tags(answer, DIRECT)
                else:
                    self.assertFalse(tags(answer, DIRECT) | tags(answer, ADJACENT), answer["text"])
            self.assertEqual(len(capabilities), 1, question["text"])

    def test_green_and_unknown_answers_exist(self):
        for question in SCORED:
            risks = [a["risk"] for a in question["answers"]]
            self.assertIn("green", risks, question["text"])
            self.assertEqual(risks.count("unknown"), 1, question["text"])

    def test_each_capability_has_two_questions(self):
        counts = Counter(
            capability
            for question in SCORED
            for capability in set().union(*(tags(a, DIRECT) for a in question["answers"]))
        )
        for capability in CAPABILITIES:
            self.assertGreaterEqual(counts[capability], 2, capability)

    def test_adjacent_tags_match_cross_tag_table(self):
        found = {
            next(iter(tags(a, KEY))): tags(a, ADJACENT)
            for question in QUESTIONS
            for a in question["answers"]
            if tags(a, ADJACENT)
        }
        self.assertEqual(found, CROSS_TAGS)
        self.assertEqual(set(ADJACENCY), set(CROSS_TAGS))
        for key, adjacent in CROSS_TAGS.items():
            for capability in adjacent:
                self.assertIn(FOLLOW_UP[capability]["product"], readout.POINTERS[key], key)

    def test_rationale_and_mitigation(self):
        for question in QUESTIONS:
            for answer in question["answers"]:
                expected = answer["risk"] in ("red", "yellow")
                for field in ("rationale", "mitigation"):
                    self.assertEqual(bool(answer.get(field)), expected, (field, answer["text"]))

    def test_pointers_cover_exactly_the_red_and_yellow_answers(self):
        gaps = {
            next(iter(tags(a, KEY))): next(iter(tags(a, DIRECT)))
            for q in QUESTIONS
            for a in q["answers"]
            if a["risk"] in ("red", "yellow")
        }
        self.assertEqual(set(readout.POINTERS), set(gaps))
        for key, capability in gaps.items():
            self.assertEqual(next(iter(readout.POINTERS[key])), readout.FOLLOW_UP[capability]["product"], key)

    def test_no_product_names(self):
        # The questionnaire's own name is the one place the company is named.
        for text in strings({k: v for k, v in QUESTIONNAIRE.items() if k != "name"}):
            self.assertIsNone(PRODUCTS.search(text), text)


class Personas(unittest.TestCase):
    def test_expected_results(self):
        for persona in PERSONAS:
            with self.subTest(persona["name"]):
                answers = persona["answers"]
                self.assertEqual(len(answers), len(QUESTIONS))
                expected = {k: v for k, v in persona.items() if k not in ("name", "answers")}
                self.assertEqual(evaluate(answers), expected)

    def test_every_pattern_holds_for_some_persona(self):
        expected = {name for persona in PERSONAS for name in persona["patterns"]}
        self.assertEqual(expected, {pattern["name"] for pattern in readout.PATTERNS})

    def test_gaps_are_the_red_and_yellow_answers(self):
        for persona in PERSONAS:
            with self.subTest(persona["name"]):
                chosen = [q["answers"][n - 1] for q, n in zip(QUESTIONS, persona["answers"])]
                expected = [
                    (q["text"], a["text"], a["risk"], a["rationale"], a["mitigation"])
                    for q, a in zip(QUESTIONS, chosen)
                    if a["risk"] in ("red", "yellow")
                ]
                found = [
                    (e["question"], e["answer"], e["risk"], e["rationale"], e["mitigation"])
                    for area in readout.build(select(persona["answers"]), "")["areas"]
                    for e in area["evidence"]
                ]
                self.assertCountEqual(found, expected)

    def test_summary_covers_every_gap(self):
        for persona in PERSONAS:
            with self.subTest(persona["name"]):
                result = readout.build(select(persona["answers"]), "") | {"generated": "2026-10-02T09:00:00+00:00"}
                text = summary.markdown("Example Ltd", result)
                for area in result["areas"]:
                    self.assertIn(f"## {area['capability']}", text)
                    for e in area["evidence"]:
                        self.assertIn(f"| {e['answer']} |", text)

    def test_no_signal_excludes_every_area_with_a_signal(self):
        for persona in PERSONAS:
            with self.subTest(persona["name"]):
                result = readout.build(select(persona["answers"]), "")
                signalled = set(result["direct"]) | {a["capability"] for a in result["adjacent"]}
                self.assertFalse(signalled & set(result["in_good_shape"]))

    def test_summary_claims_a_benefit_only_when_an_area_is_highlighted(self):
        for persona in PERSONAS:
            with self.subTest(persona["name"]):
                result = readout.build(select(persona["answers"]), "") | {"generated": "2026-10-02T09:00:00+00:00"}
                text = summary.markdown("Example Ltd", result)
                self.assertEqual("would benefit" in text, bool(result["areas"]))
                self.assertEqual("# Suggested next steps" in text, bool(result["areas"]))

    def test_summary_omits_the_overall_result(self):
        for message in QUESTIONNAIRE["riskMessages"].values():
            result = readout.build(select(PERSONAS[0]["answers"]), message) | {"generated": "2026-10-02T09:00:00+00:00"}
            self.assertNotIn(message, summary.markdown("Example Ltd", result))
