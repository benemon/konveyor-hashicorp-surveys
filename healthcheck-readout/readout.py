from pointers import POINTERS

DIRECT = "Capability Signal"
ADJACENT = "Adjacent Capability Signal"
# Identifies the interpretation and rendering rules that produced a result. The questionnaire
# has its own version, carried in the assessment.
VERSION = "0.6"

# "<facet>: <key>", one per answer. The category is never created in MTA, so the hub keeps
# the tag in the assessment but off applications.
KEY = "Answer Key"
# Every answer to the first question carries the questionnaire's version in this category, which is
# never created in MTA for the same reason.
QUESTIONNAIRE_VERSION = "Questionnaire Version"

# Order is the tie-break in DESIGN.md section 4.7.
CAPABILITIES = [
    "Infrastructure Lifecycle",
    "Image Lifecycle",
    "Machine Identity and Secrets",
    "Human Access",
    "Service Networking",
    "Workload Lifecycle",
]

# DESIGN.md section 4.4, by source answer key: why the answer also bears on the adjacent capability.
ADJACENCY = {
    "access credentials: shared": "Shared credentials need issuing and rotating centrally.",
}

# DESIGN.md section 4.8. A pattern holds when every "all" facet has one of its keys
# and, if "any" is present, at least "at_least" of those do (one when not given). Its
# capabilities are those of the answers that matched, so a definition names none.
PATTERNS = [
    {
        "name": "Day-two change escapes automation",
        "detail": "Infrastructure is provisioned as code, but day-two changes still bypass the automated lifecycle.",
        "all": {"provisioning": {"fragmented-code", "shared-code"}, "change and drift": {"by-hand", "mixed"}},
    },
    {
        "name": "Automated delivery with uneven guardrails",
        "detail": "Infrastructure is delivered as code, but standards are checked after deployment or team by team.",
        "all": {"provisioning": {"fragmented-code", "shared-code"}, "guardrails": {"after-the-fact", "per-team"}},
    },
    {
        "name": "Automated delivery with a human gate",
        "detail": "Infrastructure delivery is automated, but every change still waits for a central team to approve it by hand.",
        "all": {"provisioning": {"fragmented-code", "shared-code"}, "guardrails": {"central-approval"}},
    },
    {
        "name": "Centralised secrets, manual credential lifecycle",
        "detail": "Secrets are held in one central store, but credentials are long-lived or rotated by hand.",
        "all": {"secret storage": {"central-store"}, "rotation": {"rarely", "manual-schedule"}},
    },
    {
        "name": "Controlled path, shared or long-lived credentials",
        "detail": "Access is brokered to specific systems, but the credentials used are shared or long-lived.",
        "all": {"access path": {"brokered"}, "access credentials": {"shared", "personal-long-lived"}},
    },
    {
        "name": "Identity without session accountability",
        "detail": "Target access uses organisational identity or session-scoped credentials, but privileged activity cannot be fully reconstructed afterwards.",
        "all": {"access credentials": {"single-sign-on", "per-session"}, "visibility": {"none", "who-only"}},
    },
    {
        "name": "Trust by network location",
        "detail": "Engineer access and traffic between services both rest on being inside the network.",
        "all": {"access path": {"direct", "vpn"}, "service-to-service security": {"network-location"}},
    },
    {
        "name": "Distributed estate, fragmented control planes",
        "detail": "Workloads span several environments, and discovery, traffic policy or deployment is done differently in each.",
        "all": {"environment": {"several-clouds", "hybrid"}},
        "any": {
            "discovery": {"per-environment"},
            "service-to-service security": {"per-environment"},
            "deployment": {"per-platform"},
        },
        "at_least": 2,
    },
    {
        "name": "Deployment is standardised, networking is not",
        "detail": "Workloads are deployed through one consistent workflow across platforms, but discovery or traffic policy still differs by environment.",
        "all": {"deployment": {"one-workflow"}},
        "any": {"discovery": {"per-environment"}, "service-to-service security": {"per-environment"}},
    },
    {
        "name": "Non-standard workloads sit outside the main platform",
        "detail": "The main platform meets most needs, but batch, legacy or non-containerised workloads are run by hand or on separate tooling.",
        "all": {"deployment": {"one-platform"}, "non-standard workloads": {"individual-servers", "separate-platforms"}},
    },
    {
        "name": "Automated infrastructure, unmanaged image lifecycle",
        "detail": "Infrastructure delivery is codified, but the machine images consumed by that workflow are not governed to the same standard.",
        "all": {
            "provisioning": {"fragmented-code", "shared-code"},
            "image lifecycle": {"unmanaged-versions", "manual-governance"},
        },
    },
    {
        "name": "Golden-image pipeline disconnected from provisioning",
        "detail": "Approved image metadata exists, but downstream infrastructure workflows do not consistently validate what they consume.",
        "all": {"provisioning": {"fragmented-code", "shared-code"}, "image lifecycle": {"central-no-validation"}},
    },
    {
        "name": "Manual image maintenance outside automated delivery",
        "detail": "Provisioning automation does not extend to the machine-image build process, leaving a manual dependency in the delivery chain.",
        "all": {"provisioning": {"fragmented-code", "shared-code"}, "image build": {"manual"}},
    },
    {
        "name": "Network-centric controls without internal certificates",
        "detail": "Traffic between services is controlled by network location or hand-maintained rules, and internal services do not commonly use certificates.",
        "all": {
            "service-to-service security": {"network-location", "manual-rules"},
            "certificates": {"not-used"},
        },
    },
    {
        "name": "Network rules with a manual certificate lifecycle",
        "detail": "Traffic between services is controlled by network location or hand-maintained rules, and the certificates that could identify services are issued by hand or unevenly.",
        "all": {
            "service-to-service security": {"network-location", "manual-rules"},
            "certificates": {"by-hand", "partly-automated"},
        },
    },
]

# The colour is the product's brand colour, used for its tag category in MTA.
FOLLOW_UP = {
    "Infrastructure Lifecycle": {
        "topics": "How infrastructure is provisioned, governed and changed after day one",
        "roles": ["Platform or infrastructure engineering lead"],
        "product": "Terraform",
        "colour": "#7B42BC",
        "talk_track": "Drift detection identifies divergence but does not remediate it automatically. Remediation "
        "returns through a run, once it is decided whether the external change is kept or overwritten.",
    },
    "Image Lifecycle": {
        "topics": "How machine images are built, which versions are approved and how outdated images are retired",
        "roles": ["Platform engineering lead", "Security engineering lead"],
        "product": "Packer",
        "colour": "#02A8EF",
        "talk_track": "Building an image and governing its lifecycle are separate questions. First establish whether image "
        "creation is reproducible and version-controlled, then whether published images have a system of record, an "
        "approved-version mechanism and a revocation path. Packer builds image artefacts, HCP Packer tracks and governs "
        "their lifecycle, and Terraform can consume and validate those artefacts during provisioning. An organisation "
        "that does not maintain machine images has no Image Lifecycle gap.",
    },
    "Machine Identity and Secrets": {
        "topics": "Where credentials and certificates come from, how long they live and how they are rotated",
        "roles": ["Security architect", "Application platform owner"],
        "product": "Vault",
        "colour": "#FFCF25",
        "talk_track": "A useful progression: store secrets, automate rotation, eliminate standing credentials, "
        "then establish workload identity with short-lived credentials.",
    },
    "Human Access": {
        "topics": "How engineers reach systems, what they sign in with and how access is recorded",
        "roles": ["Security operations lead", "Infrastructure access owner"],
        "product": "Boundary",
        "colour": "#F24C53",
        "talk_track": "Authentication, authorisation, target connectivity, credentials and session accountability "
        "are separate controls. Boundary covers identity-aware access and sessions; Vault integration can then "
        "remove long-lived target credentials.",
    },
    "Service Networking": {
        "topics": "How services find each other and how traffic between them is authorised across environments",
        "roles": ["Network or platform architect"],
        "product": "Consul",
        "colour": "#E03875",
        "talk_track": "Service discovery answers where a service is. Service identity and intentions answer "
        "whether one service should be allowed to talk to another.",
    },
    "Workload Lifecycle": {
        "topics": "How workloads of different types are deployed, scheduled and operated",
        "roles": ["Platform engineering lead", "Application operations owner"],
        "product": "Nomad",
        "colour": "#06D092",
        "talk_track": "Task drivers include Docker, isolated exec, Java, QEMU and raw exec, so bringing a workload "
        "under a scheduler does not mean containerising it first.",
    },
}


def tags(answer, category):
    return {t["tag"] for t in answer.get("applyTags") or [] if t["category"] == category}


def in_order(capabilities):
    return sorted(capabilities, key=CAPABILITIES.index)


def pattern(definition, keys, texts, signals):
    required = [facet for facet, wanted in definition["all"].items() if keys.get(facet) in wanted]
    optional = [facet for facet, wanted in definition.get("any", {}).items() if keys.get(facet) in wanted]
    if len(required) < len(definition["all"]) or len(optional) < ("any" in definition and definition.get("at_least", 1)):
        return None
    matched = required + optional
    capabilities = in_order(set().union(*(signals.get(facet, set()) for facet in matched)))
    pointers = {}
    for facet in matched:
        for product, named in POINTERS.get(f"{facet}: {keys[facet]}", {}).items():
            listed = pointers.setdefault(product, [])
            listed += [c for c in named if c not in listed]
    return {
        "name": definition["name"],
        "detail": definition["detail"],
        "capabilities": capabilities,
        "products": [FOLLOW_UP[c]["product"] for c in capabilities],
        "answers": [{"facet": facet, "answer": texts[facet]} for facet in matched],
        "pointers": pointers,
    }


def build(sections, verdict):
    evidence = {c: [] for c in CAPABILITIES}
    keys, texts, unknowns, unclear, sources, signals = {}, {}, [], set(), {}, {}
    environment = questionnaire_version = ""
    for question in (q for s in sections for q in s["questions"]):
        identities = [tags(a, KEY) for a in question["answers"]]
        if not all(len(identity) == 1 for identity in identities):
            raise ValueError("the assessment's questionnaire has no answer keys; assess again with the current one")
        facet = next(iter(identities[0])).split(": ")[0]
        answer = next((a for a in question["answers"] if a.get("selected")), None)
        if answer:
            key = next(iter(tags(answer, KEY)))
            keys[facet] = key.split(": ")[1]
            texts[facet] = answer["text"]
        capability = next(iter(set().union(*(tags(a, DIRECT) for a in question["answers"]))), None)
        if not capability:
            environment = answer["text"] if answer else ""
            questionnaire_version = next(iter(tags(question["answers"][0], QUESTIONNAIRE_VERSION)), "")
        elif not answer or answer["risk"] == "unknown":
            unknowns.append({"facet": facet, "question": question["text"]})
            unclear.add(capability)
        elif answer["risk"] in ("red", "yellow"):
            evidence[capability].append(
                {
                    "key": key,
                    "facet": facet,
                    "question": question["text"],
                    "answer": answer["text"],
                    "risk": answer["risk"],
                    "rationale": answer.get("rationale", ""),
                    "mitigation": answer.get("mitigation", ""),
                    "pointers": POINTERS.get(key, {}),
                }
            )
            signals[facet] = {capability} | tags(answer, ADJACENT)
            for adjacent in tags(answer, ADJACENT):
                sources.setdefault(adjacent, []).append(
                    {"capability": capability, "facet": facet, "answer": answer["text"], "note": ADJACENCY[key]}
                )

    reds = {c: sum(e["risk"] == "red" for e in evidence[c]) for c in CAPABILITIES}
    direct = {c: "strong" if reds[c] else "moderate" for c in CAPABILITIES if evidence[c]}
    ranked = sorted(direct, key=lambda c: (direct[c] != "strong", -reds[c], -len(evidence[c])))

    adjacent = [
        {
            "capability": c,
            "via": in_order({source["capability"] for source in sources[c]}),
            "answers": [{k: source[k] for k in ("facet", "answer", "note")} for source in sources[c]],
        }
        for c in CAPABILITIES
        if c in sources and c not in direct
    ]

    delivery = CAPABILITIES[0]
    implementation = None
    if direct and delivery not in direct:
        implementation = {"capability": delivery, "via": in_order(direct)}

    return {
        "questionnaire_version": questionnaire_version,
        "readout_version": VERSION,
        "environment": environment,
        "verdict": verdict,
        "direct": direct,
        "areas": [
            {
                "capability": c,
                "product": FOLLOW_UP[c]["product"],
                "strength": direct[c],
                "facets": [e["facet"] for e in evidence[c]],
                "evidence": evidence[c],
            }
            for c in ranked
        ],
        "presented": ranked[:3],
        "adjacent": adjacent,
        "implementation": implementation,
        "patterns": [found for p in PATTERNS if (found := pattern(p, keys, texts, signals))],
        "in_good_shape": [c for c in CAPABILITIES if c not in direct and c not in unclear and c not in sources],
        "unknowns": unknowns,
        "follow_up": [{"capability": c} | FOLLOW_UP[c] for c in ranked[:3]],
    }
