# DESIGN.md section 4.9. For each red or yellow answer, by answer key: the product
# capabilities a facilitator can discuss if the respondent wants to go deeper, each as
# (capability, what it does here). The first product listed is the one associated with
# the answer's capability.
POINTERS = {
    "provisioning: manual": {
        "Terraform": [
            ("Terraform infrastructure as code", "declarative desired-state provisioning"),
            (
                "HCP Terraform or Terraform Enterprise remote execution and managed runs",
                "a consistent execution lifecycle",
            ),
            ("Private registry modules and providers", "reusable, versioned infrastructure patterns"),
            ("No-code provisioning", "self-service consumption of approved modules"),
            ("Search and import", "bring existing manually created infrastructure under Terraform management"),
        ],
    },
    "provisioning: team-scripts": {
        "Terraform": [
            ("Private registry modules and providers", "common versioned building blocks"),
            ("VCS-driven workflows", "version-controlled infrastructure change"),
            ("HCP Terraform managed execution", "a standard run lifecycle in place of team-specific execution"),
            ("Projects and workspaces", "common organisational execution scopes"),
        ],
    },
    "provisioning: fragmented-code": {
        "Terraform": [
            ("Private registry", "shared modules and providers"),
            ("Module versioning", "controlled adoption of standard patterns"),
            ("HCP Terraform managed workflows", "a consistent plan and apply lifecycle"),
            ("No-code provisioning", "expose approved modules as standard self-service offerings where appropriate"),
        ],
    },
    "guardrails: after-the-fact": {
        "Terraform": [
            ("Policy as code", "Sentinel or OPA policies evaluated against Terraform runs"),
            ("Policy sets", "distribute those controls centrally"),
            ("Run tasks", "invoke external security, compliance or validation systems during the run lifecycle"),
            ("Mandatory enforcement", "prevent non-compliant changes from proceeding"),
        ],
    },
    "guardrails: per-team": {
        "Terraform": [
            ("Policy sets", "centrally defined Sentinel or OPA policies scoped globally or to projects and workspaces"),
            ("Central policy versioning", "consistent controls across teams"),
            ("Global and project run tasks", "apply third-party checks consistently across delivery workflows"),
        ],
    },
    "guardrails: central-approval": {
        "Terraform": [
            ("Policy as code with enforcement levels", "automate routine approval decisions"),
            ("Policy sets", "consistent organisational guardrails"),
            ("Run tasks", "automate external checks"),
            (
                "No-code provisioning and approved registry modules",
                "governed self-service within predefined patterns",
            ),
        ],
    },
    "change and drift: by-hand": {
        "Terraform": [
            ("HCP Terraform health assessments", "ongoing assessment after provisioning"),
            ("Drift detection", "identify out-of-band changes against Terraform configuration"),
            ("Continuous validation", "verify that custom assertions continue to hold after deployment"),
            (
                "Managed plan and apply workflow",
                "deliberately reconcile actual infrastructure with desired configuration",
            ),
            ("Search and import", "onboard resources that are not yet managed"),
        ],
    },
    "change and drift: mixed": {
        "Terraform": [
            ("HCP Terraform health assessments", ""),
            ("Drift detection", "periodically detect configuration divergence"),
            ("Continuous validation", "detect operational conditions that fail even without configuration drift"),
            ("Workspace health visibility and Explorer", "identify unhealthy or drifted workspaces at scale"),
            ("Managed Terraform runs", "return remediation to the controlled lifecycle"),
        ],
    },
    "change and drift: fixed-by-hand": {
        "Terraform": [
            ("Drift detection", "discover divergence automatically"),
            ("Continuous validation", "continually evaluate Terraform checks, preconditions and postconditions"),
            ("Health assessments", "combine both forms of lifecycle monitoring"),
            (
                "Plan and apply",
                "controlled reconciliation, either restoring desired state or updating configuration to accept the change",
            ),
        ],
    },
    "secret storage: in-files": {
        "Vault": [
            ("KV secrets engine and central secrets management", "move static secrets into controlled storage"),
            ("Policies", "authorise access"),
            ("Auth methods and identity", "authenticate people and workloads without embedding Vault credentials"),
            ("Audit devices", "record secret access"),
            (
                "HCP Vault Radar",
                "find exposed or unmanaged secrets in source code and elsewhere, as part of discovery and remediation",
            ),
        ],
    },
    "secret storage: several-stores": {
        "Vault": [
            ("A central Vault secrets platform", "one control plane for secret storage and issuance"),
            ("Policies", "consistent authorisation"),
            ("Auth methods and identity", "common authentication for workloads and people"),
            ("Audit devices", "centralised auditability"),
            ("Namespaces", "organisational isolation under common governance"),
            ("Secrets sync", "where existing platforms must keep consuming secrets through their native stores"),
        ],
    },
    "rotation: rarely": {
        "Vault": [
            ("Dynamic secrets", "generate credentials on demand in place of standing credentials"),
            ("Leases and TTLs", "an explicit credential lifetime"),
            ("Automatic revocation", "invalidate credentials when leases expire or are revoked"),
            (
                "Static-role credential rotation",
                "rotate credentials automatically where applications cannot yet use dynamic credentials",
            ),
        ],
    },
    "rotation: manual-schedule": {
        "Vault": [
            ("Automated static credential rotation", "scheduled or periodic rotation for retained accounts"),
            ("Dynamic secrets", "issue unique credentials per client or workload"),
            ("Leases and TTLs", "constrain lifetime"),
            ("Renewal and revocation", "manage credential expiry automatically"),
            ("Workload authentication", "let applications obtain credentials when required"),
        ],
    },
    "certificates: by-hand": {
        "Vault": [
            ("PKI secrets engine", "managed root and intermediate CA capability"),
            ("Automated certificate issuance", ""),
            ("Short-lived certificates", ""),
            ("Certificate renewal and revocation", ""),
            ("ACME support", "a standard protocol for automated certificate lifecycle"),
            ("Integrations such as cert-manager", "where Kubernetes or OpenShift workloads need automated issuance"),
        ],
    },
    "certificates: partly-automated": {
        "Vault": [
            ("A central Vault PKI service", "a common CA and issuance layer"),
            ("PKI roles", "define certificate issuance policy by workload or use case"),
            ("ACME", "standardised automated enrolment and renewal"),
            ("Short-lived certificates", "reduce dependence on manual renewal"),
            ("Platform integrations such as cert-manager", "extend automation consistently"),
        ],
    },
    "access path: direct": {
        "Boundary": [
            ("Targets", "represent individual systems and services in place of granting network access"),
            ("Identity-aware authorisation", ""),
            ("Roles and grants", "define who can access which targets"),
            ("Workers", "proxy connections to private targets without exposing the wider network"),
            ("OIDC and identity provider authentication", "tie access to organisational identity"),
        ],
    },
    "access path: vpn": {
        "Boundary": [
            ("Target-specific access", "in place of broad network reachability"),
            ("Roles and grants", "target authorisation based on identity and role"),
            ("OIDC and identity provider integration", "organisational identity"),
            ("Workers", "connectivity into private networks while users stay outside them"),
        ],
    },
    "access path: bastion": {
        "Boundary": [
            ("Control plane", "central access policy and authorisation"),
            ("Distributed workers", "reach targets across data centres, clouds and network zones"),
            ("Targets and host sets", "a common resource model"),
            ("Roles and grants", "consistent access policy across environments"),
        ],
    },
    "access credentials: shared": {
        "Boundary": [
            ("Identity-based authorisation", "attribute access to individuals"),
            ("Credential stores and credential libraries", "central credential sources"),
            ("Credential brokering", "retrieve credentials centrally for the session"),
            ("Credential injection", "place credentials into SSH and RDP sessions without exposing them to users"),
        ],
        "Vault": [
            ("Vault credential store integration", "obtain static or dynamic Vault credentials"),
            ("Dynamic credentials", "short-lived target credentials where supported"),
        ],
    },
    "access credentials: personal-long-lived": {
        "Boundary": [
            ("OIDC and organisational identity authentication", ""),
            ("Roles and grants", ""),
            ("Time-bounded sessions", ""),
            (
                "Credential brokering and injection",
                "credentials are issued only when a session is authorised and need not be managed by the user",
            ),
        ],
        "Vault": [
            ("Vault-backed credential libraries", ""),
            ("Dynamic credentials", ""),
        ],
    },
    "visibility: none": {
        "Boundary": [
            ("Centralised session model", "associate user, target and session"),
            ("Session metadata", "who connected to which target, and when"),
            ("Audit logging", "administrative and control-plane events"),
            ("Worker-proxied access", "route privileged connections through a controlled path"),
        ],
    },
    "visibility: who-only": {
        "Boundary": [
            ("Session recording", "record supported privileged sessions"),
            ("Recording storage and playback", "retain activity for investigation and review"),
            ("Session metadata", "tie the recording to its user and target"),
        ],
    },
    "discovery: fixed-addresses": {
        "Consul": [
            ("Service catalogue", "a registry of service instances and locations"),
            ("Service registration and deregistration", "maintain membership dynamically"),
            ("Health checks", "return healthy instances"),
            ("DNS and API discovery", "address services by name in place of fixed IP and port"),
            ("Health-aware failover and load balancing", ""),
        ],
    },
    "discovery: per-environment": {
        "Consul": [
            (
                "Service discovery across heterogeneous runtimes",
                "a common catalogue for VM, Kubernetes, OpenShift and other environments",
            ),
            ("DNS and API discovery", "a common consumption model"),
            (
                "Cluster peering and cross-cluster service discovery",
                "where environments are separate Consul clusters",
            ),
            ("Mesh gateways", "where connectivity across networks is also required"),
        ],
    },
    "service-to-service security: network-location": {
        "Consul": [
            ("Service mesh", ""),
            ("Service identities", ""),
            ("Automatic mTLS", "authenticate and encrypt traffic between workloads"),
            ("Intentions", "explicitly allow or deny communication by service identity, not IP or location"),
            ("Transparent proxy", "where applications should adopt the mesh without code changes"),
        ],
        "Vault": [
            ("PKI secrets engine", "issue and renew the certificates that identify workloads"),
            ("PKI roles", "define issuance policy by workload or use case"),
            ("Short-lived certificates", "automated renewal in place of long-lived credentials"),
        ],
    },
    "service-to-service security: manual-rules": {
        "Consul": [
            ("Intentions", "L4 and L7 identity-based service authorisation"),
            ("Service identity through mTLS certificates", ""),
            ("Service mesh data plane", "enforce rules dynamically as endpoints change"),
            (
                "Central policy configuration",
                "decouple policy from individual IP addresses and firewall tickets",
            ),
        ],
        "Vault": [
            ("PKI secrets engine", "issue and renew the certificates that identify workloads"),
            ("PKI roles", "define issuance policy by workload or use case"),
            ("Short-lived certificates", "automated renewal in place of long-lived credentials"),
        ],
    },
    "service-to-service security: per-environment": {
        "Consul": [
            ("Intentions", "common policy semantics between services"),
            ("Service identities and mTLS", "consistent workload identity"),
            ("Service mesh across heterogeneous platforms", ""),
            (
                "Cluster peering and mesh gateways",
                "policy-aware connectivity across clusters and network zones where required",
            ),
        ],
    },
    "deployment: by-hand": {
        "Nomad": [
            ("Job specifications", "declarative workload definition"),
            ("Service, batch, system and system-batch schedulers", "model different workload lifecycles"),
            ("Scheduler placement and bin packing", "place workloads automatically"),
            ("Restart policies", "recover failed tasks locally"),
            ("Reschedule policies", "place failed allocations elsewhere"),
            ("Rolling and canary deployment strategies", "controlled application rollout"),
        ],
    },
    "deployment: per-platform": {
        "Nomad": [
            ("A common job specification and workflow", "across supported workload classes"),
            ("Task-driver model", "Docker, isolated exec, Java, QEMU, raw exec and extensible drivers"),
            (
                "Service, batch and system scheduling",
                "one orchestration model for differing workload behaviours",
            ),
            (
                "Constraints, affinities and spread",
                "meet platform-specific placement requirements without separate deployment tooling",
            ),
        ],
    },
    "non-standard workloads: individual-servers": {
        "Nomad": [
            (
                "Heterogeneous task drivers",
                "run containers, binaries, Java workloads, QEMU virtual machines and other supported runtimes "
                "without mandatory containerisation",
            ),
            ("Service, batch and system schedulers", ""),
            ("Bin packing and resource-aware placement", ""),
            ("Restart and reschedule", "automated recovery"),
            ("Constraints, affinities and spread", "place workloads according to host requirements"),
            ("Periodic jobs", "for scheduled and batch workloads"),
        ],
    },
    "non-standard workloads: separate-platforms": {
        "Nomad": [
            ("Task-driver architecture", "a common scheduler across heterogeneous workload runtimes"),
            (
                "Service, batch, system and system-batch schedulers",
                "a common lifecycle model for long-running, batch and node-wide workloads",
            ),
            ("Shared scheduling and resource pool", "bin-pack workloads across common capacity"),
            ("Job specifications", "a common declarative operating model"),
            (
                "Restart, reschedule and deployment controls",
                "consistent day-two operations across workload types",
            ),
        ],
    },
}
