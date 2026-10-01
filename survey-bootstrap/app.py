import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MTA_HUB = os.environ["MTA_HUB"].rstrip("/")
MTA_API_KEY = os.environ["MTA_API_KEY"]
INDEX = (Path(__file__).parent / "index.html").read_bytes()
# The route serves this path on MTA's own host, so links into MTA are same-origin and
# keep the browser tab's MTA session.
PREFIX = "/bootstrap"
ADDON = "snapshot-readout"
# The questionnaire the readout addon understands.
SNAPSHOT = "HashiCorp Snapshot"


def hub(path, body=None):
    request = urllib.request.Request(
        f"{MTA_HUB}/{path}",
        data=json.dumps(body).encode() if body else None,
        headers={
            "Authorization": f"Bearer {MTA_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


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


def readout(organisation):
    application = next((a for a in hub("applications") if a["name"] == organisation), None)
    if not application:
        raise ValueError("organisation not found in MTA")
    snapshot = next((q["id"] for q in hub("questionnaires") if q["name"] == SNAPSHOT), None)
    assessment = next(
        (
            a
            for a in hub(f"applications/{application['id']}/assessments")
            if (a.get("application") or {}).get("id") == application["id"]
            and a["questionnaire"]["id"] == snapshot
            and a["status"] == "complete"
        ),
        None,
    )
    if not assessment:
        raise ValueError(f"organisation has no completed {SNAPSHOT} assessment")
    # An addon token cannot read assessments, so the assessment travels as task data.
    task = hub(
        "tasks",
        {
            "name": f"{organisation} readout",
            "addon": ADDON,
            "application": {"id": application["id"]},
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
        }
    return state


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body, content_type="application/json"):
        payload = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def call_mta(self, action):
        try:
            self.reply(200, action())
        except ValueError as reason:
            self.reply(400, {"error": str(reason)})
        except urllib.error.HTTPError as reason:
            # The hub echoes the bearer token in its 401 body, so the body is not relayed.
            self.reply(502, {"error": f"MTA returned {reason.code}"})
        except urllib.error.URLError:
            self.reply(502, {"error": "MTA is unreachable"})

    def do_GET(self):
        path = self.path.removeprefix(PREFIX)
        task = path.removeprefix("/api/readouts/")
        if self.path == PREFIX:
            self.send_response(301)
            self.send_header("Location", f"{PREFIX}/")
            self.end_headers()
        elif path == self.path:
            self.reply(404, {"error": "not found"})
        elif path == "/":
            self.reply(200, INDEX, "text/html; charset=utf-8")
        elif path == "/api/questionnaires":
            self.call_mta(lambda: [q["name"] for q in questionnaires()])
        elif path == "/api/organisations":
            self.call_mta(lambda: sorted(a["name"] for a in hub("applications")))
        elif task != path and task.isdigit():
            self.call_mta(lambda: readout_state(task))
        else:
            self.reply(404, {"error": "not found"})

    def do_POST(self):
        path = self.path.removeprefix(PREFIX)
        if path == self.path or path not in ("/api/assessments", "/api/readouts"):
            self.reply(404, {"error": "not found"})
            return
        try:
            fields = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            organisation = fields["organisation"].strip()
            email = fields.get("email", "").strip()
            questionnaire = fields.get("questionnaire")
        except (ValueError, KeyError, AttributeError, TypeError):
            organisation = email = ""
        if path == "/api/readouts":
            if not organisation:
                self.reply(400, {"error": "organisation is required"})
                return
            self.call_mta(lambda: readout(organisation))
            return
        if not organisation or not email:
            self.reply(400, {"error": "organisation and email are required"})
            return
        self.call_mta(lambda: start(organisation, email, questionnaire))


ThreadingHTTPServer(("", 8080), Handler).serve_forever()
