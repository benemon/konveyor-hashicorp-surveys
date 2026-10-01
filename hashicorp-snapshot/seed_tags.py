import json
import os
import urllib.request
from pathlib import Path

import yaml

HUB = os.environ["MTA_ENDPOINT"].rstrip("/") + "/hub"
TOKEN = os.environ["MTA_ADMIN_TOKEN"]


def hub(method, path, body=None):
    request = urllib.request.Request(
        HUB + path,
        method=method,
        data=json.dumps(body).encode() if body else None,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)


questionnaire = yaml.safe_load((Path(__file__).parent / "questionnaire.yaml").read_text())
wanted = {}
for section in questionnaire["sections"]:
    for question in section["questions"]:
        for answer in question["answers"]:
            for tag in answer.get("applyTags", []):
                # Answer keys must not exist in MTA: the hub then leaves them off applications.
                if tag["category"] != "Answer Key":
                    wanted.setdefault(tag["category"], set()).add(tag["tag"])

existing = {c["name"]: c for c in hub("GET", "/tagcategories")}
for category, names in sorted(wanted.items()):
    found = existing.get(category)
    if not found:
        found = hub("POST", "/tagcategories", {"name": category, "colour": "#6a6e73"})
        print(f"created category: {category}")
    present = {t["name"] for t in found.get("tags") or []}
    for name in sorted(names - present):
        hub("POST", "/tags", {"name": name, "category": {"id": found["id"]}})
        print(f"created tag: {category} / {name}")
