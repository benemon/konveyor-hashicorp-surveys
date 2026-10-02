import base64
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

HUB = os.environ["MTA_HUB"]
ADMIN = base64.b64encode(f"{os.environ['username']}:{os.environ['password']}".encode()).decode()
ACCOUNT = Path("/var/run/secrets/kubernetes.io/serviceaccount")
CLUSTER = "https://kubernetes.default.svc"
NAMESPACE = os.environ["NAMESPACE"]
SECRET = f"{CLUSTER}/api/v1/namespaces/{NAMESPACE}/secrets/snapshot-console"
BUILDS = f"{CLUSTER}/apis/build.openshift.io/v1/namespaces/{NAMESPACE}/buildconfigs"
# Answer keys must not exist in MTA: the hub then leaves them off applications.
UNSEEDED = "Answer Key"


def call(url, authorization, method="GET", body=None, content_type="application/json", context=None):
    request = urllib.request.Request(
        url,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": authorization, "Content-Type": content_type, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30, context=context) as response:
        payload = response.read()
        return json.loads(payload) if payload else None


cluster = ssl.create_default_context(cafile=ACCOUNT / "ca.crt")
token = f"Bearer {(ACCOUNT / 'token').read_text()}"

# OpenShift starts a build by itself only when a BuildConfig is first created.
for name in os.environ["BUILDS"].split():
    request = {"kind": "BuildRequest", "apiVersion": "build.openshift.io/v1", "metadata": {"name": name}}
    call(f"{BUILDS}/{name}/instantiate", token, "POST", request, context=cluster)
    print(f"started build: {name}")


def api_key():
    stored = call(SECRET, token, context=cluster).get("data") or {}
    if "api-key" in stored:
        return base64.b64decode(stored["api-key"]).decode()
    try:
        call(f"{HUB}/tagcategories", "")
        # Upstream Konveyor does not require authentication by default, and then ignores the key.
        key = "authentication-not-required"
    except urllib.error.HTTPError as reason:
        if reason.code != 401:
            raise
        key = call(f"{HUB}/auth/tokens", f"Basic {ADMIN}", "POST", {})["token"]
    patch = {"data": {"api-key": base64.b64encode(key.encode()).decode()}}
    call(SECRET, token, "PATCH", patch, "application/merge-patch+json", cluster)
    print("stored the API key")
    return key


# The operator may still be bringing the hub up.
for attempt in range(90):
    try:
        key = api_key()
        break
    except (urllib.error.URLError, ConnectionError) as reason:
        print(f"waiting for the hub: {reason}")
        time.sleep(10)
else:
    raise SystemExit("the hub did not become available")

bearer = f"Bearer {key}"
questionnaire = json.loads(Path(__file__).with_name("questionnaire.json").read_text())

wanted = {}
for section in questionnaire["sections"]:
    for question in section["questions"]:
        for answer in question["answers"]:
            for tag in answer.get("applyTags", []):
                if tag["category"] != UNSEEDED:
                    wanted.setdefault(tag["category"], set()).add(tag["tag"])

existing = {c["name"]: c for c in call(f"{HUB}/tagcategories", bearer)}
for category, names in sorted(wanted.items()):
    found = existing.get(category) or call(
        f"{HUB}/tagcategories", bearer, "POST", {"name": category, "colour": "#6a6e73"}
    )
    present = {t["name"] for t in found.get("tags") or []}
    for name in sorted(names - present):
        call(f"{HUB}/tags", bearer, "POST", {"name": name, "category": {"id": found["id"]}})
        print(f"created tag: {category} / {name}")

current = next((q for q in call(f"{HUB}/questionnaires", bearer) if q["name"] == questionnaire["name"]), None)
if current:
    call(f"{HUB}/questionnaires/{current['id']}", bearer, "PUT", questionnaire | {"id": current["id"]})
    print("updated the questionnaire")
else:
    call(f"{HUB}/questionnaires", bearer, "POST", questionnaire)
    print("imported the questionnaire")
