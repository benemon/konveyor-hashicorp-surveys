# DESIGN.md section 4.10. For each aspect, what the organisation gains when the suggested change is
# made, by dimension, the primary one first; and the dimensions not claimed, with the reason. A
# statement holds whichever red or yellow answer the respondent gave.
IMPACTS = {
    "provisioning": {
        "impacts": {
            "speed": (
                "Product teams get the environments they need with less waiting, so new services and business changes "
                "can reach customers sooner."
            ),
            "cost": (
                "Engineering effort falls as teams reuse proven infrastructure patterns, and recurring environment "
                "delivery becomes less expensive to build and maintain across the organisation."
            ),
            "risk": (
                "Security and governance teams see fewer configuration exceptions and policy gaps, and can be more "
                "confident that infrastructure changes meet organisational standards."
            ),
        },
        "omitted": {},
    },
    "image build": {
        "impacts": {
            "cost": (
                "The cost of image maintenance falls as teams reuse shared definitions across platforms, avoiding "
                "repeated engineering work whenever baselines change."
            ),
            "speed": (
                "Application teams receive updated machine images sooner, so platform changes and security fixes reach "
                "dependent systems with less delay."
            ),
            "risk": (
                "Fewer configuration variations reach production, so inconsistent machine images are less likely to "
                "introduce avoidable vulnerabilities or operational failures."
            ),
        },
        "omitted": {},
    },
    "image lifecycle": {
        "impacts": {
            "risk": (
                "Security teams can retire vulnerable or obsolete machine images, limiting further exposure once an "
                "affected version has been identified."
            ),
        },
        "omitted": {
            "speed": "Faster remediation depends on lifecycle automation beyond the target state of this aspect.",
            "cost": (
                "A lower operating burden depends on rollback and inherited revocation, which go beyond the target "
                "state."
            ),
        },
    },
    "image composition": {
        "impacts": {
            "risk": (
                "Vulnerability investigations focus on systems that contain affected software, helping security teams "
                "limit unnecessary disruption during urgent remediation."
            ),
        },
        "omitted": {
            "speed": (
                "The gain is a faster security investigation, which is a risk outcome here; product delivery is no "
                "quicker."
            ),
            "cost": "Recording an image's contents and ancestry has no distinct cost outcome.",
        },
    },
    "guardrails": {
        "impacts": {
            "risk": (
                "Security and compliance teams stop more policy violations before production, so incidents and audit "
                "findings from non-compliant infrastructure become less likely."
            ),
        },
        "omitted": {
            "speed": (
                "Only the central-approval answer waits for a review, so a speed benefit does not hold for every "
                "answer."
            ),
            "cost": "Policies can carry cost controls, but the aspect does not establish that they do.",
        },
    },
    "change and drift": {
        "impacts": {
            "risk": (
                "Operations teams catch unintended infrastructure changes earlier, making outages, failed recoveries "
                "and compliance problems from hidden differences less likely."
            ),
            "cost": (
                "Incident investigation and repair consume less engineering time once unexpected changes are visible, "
                "and less rework is needed after infrastructure diverges."
            ),
        },
        "omitted": {
            "speed": "The gain is operational visibility and less downtime; time to market is unchanged.",
        },
    },
    "secret storage": {
        "impacts": {
            "risk": (
                "Application credentials come under consistent control and traceability, so an exposed secret is less "
                "likely and quicker to contain."
            ),
            "cost": (
                "Credential governance requires less duplicated administration across teams and platforms, freeing "
                "security and platform capacity from overlapping secret-handling processes."
            ),
        },
        "omitted": {
            "speed": (
                "Central secret handling changes control and administrative effort; products and people are productive "
                "no sooner."
            ),
        },
    },
    "workload identity": {
        "impacts": {
            "risk": (
                "Applications depend less on long-lived credentials that can be copied or stolen, shrinking the window "
                "in which a compromised secret remains useful."
            ),
            "cost": (
                "Credential administration consumes less platform-team capacity, with fewer long-lived application "
                "secrets to distribute, track and replace across changing environments."
            ),
        },
        "omitted": {
            "speed": "Less credential management is a cost outcome; the target state delivers products no sooner.",
        },
    },
    "rotation": {
        "impacts": {
            "risk": (
                "A stolen application credential remains useful for less time, limiting the opportunity for "
                "unauthorised access before expiry or automatic replacement."
            ),
            "cost": (
                "Routine credential changes demand less coordination from platform and application teams, and keeping "
                "access current takes less recurring effort."
            ),
        },
        "omitted": {
            "speed": "Credentials on demand are a convenience; time to market is unchanged.",
        },
    },
    "certificates": {
        "impacts": {
            "risk": (
                "Service owners face fewer outages and security exposures from expired or mismanaged internal "
                "certificates, protecting application availability and trusted connections."
            ),
            "cost": (
                "Certificate administration consumes less platform-team capacity, freeing engineers from repeated "
                "requests, tracking and renewal work across internal services."
            ),
        },
        "omitted": {
            "speed": "The gain is fewer errors, missed renewals and outages; product delivery is no quicker.",
        },
    },
    "access path": {
        "impacts": {
            "risk": (
                "A compromised engineer account exposes fewer systems, limiting the potential blast radius of "
                "unauthorised access to sensitive infrastructure."
            ),
        },
        "omitted": {
            "speed": "Direct or broad network access is already fast for some respondents.",
            "cost": "The saving on bastion administration applies to one starting answer only.",
        },
    },
    "access credentials": {
        "impacts": {
            "risk": (
                "Stolen, shared or lingering privileged credentials become less common, limiting the organisation's "
                "exposure to unauthorised infrastructure access."
            ),
            "cost": (
                "Privileged access needs less manual credential administration, freeing operations teams from repeated "
                "issuing, rotation and withdrawal work."
            ),
        },
        "omitted": {
            "speed": (
                "Simpler credential handling reduces friction, but the starting answers do not consistently imply a "
                "delivery gain."
            ),
        },
    },
    "visibility": {
        "impacts": {
            "risk": (
                "Incident response teams establish the scope of privileged-access incidents with greater confidence, "
                "supporting faster containment and more complete evidence."
            ),
            "cost": (
                "Audit and incident teams reconstruct privileged activity from one evidence trail, so investigations "
                "and compliance reviews take less effort."
            ),
        },
        "omitted": {
            "speed": "Faster evidence gathering improves investigations and audits; product delivery is no quicker.",
        },
    },
    "discovery": {
        "impacts": {
            "speed": (
                "Application teams change and scale services with less coordination around changing endpoints, so "
                "releases proceed sooner across dynamic environments."
            ),
            "cost": (
                "Service-location changes create less platform work across environments, avoiding the recurring effort "
                "of maintaining separate discovery methods and configuration."
            ),
        },
        "omitted": {
            "risk": "Lower downtime risk is not established for every starting answer.",
        },
    },
    "service-to-service security": {
        "impacts": {
            "risk": (
                "Compromising one service exposes fewer unintended targets, limiting lateral movement and the "
                "potential impact of a breach across application environments."
            ),
        },
        "omitted": {
            "speed": (
                "Automated policy removes network-change delays for some respondents, but broad network access already "
                "connects without waiting."
            ),
            "cost": "The saving on firewall management does not hold for every starting answer.",
        },
    },
    "deployment": {
        "impacts": {
            "speed": (
                "Product teams release application changes sooner, with fewer delays caused by platform-specific "
                "deployment practices and reliance on individual operating knowledge."
            ),
        },
        "omitted": {
            "cost": "A common workflow is simpler to operate, but the target state has no distinct cost outcome.",
            "risk": "Safer update strategies go beyond the target state of this aspect.",
        },
    },
    "non-standard workloads": {
        "impacts": {
            "cost": (
                "Operations teams support diverse workloads with less duplicated tooling and specialist "
                "administration, avoiding the expense of separate operating models for each type."
            ),
        },
        "omitted": {
            "speed": "Separate platforms may already deliver these workloads quickly.",
            "risk": "Respondents using separate platforms may already have equivalent recovery.",
        },
    },
}
