# DESIGN.md section 4.9. Each product feature a pointer can name: the sentence the summary and the
# Insights print for it, and its documentation page.
FEATURES = {
    "Infrastructure as code": (
        "Terraform describes infrastructure in configuration files that declare the desired end state, and works out "
        "the changes needed to reach it.",
        "https://developer.hashicorp.com/terraform/intro",
    ),
    "Remote operations": (
        "Remote operations run plan and apply centrally, so a change passes through a recorded workflow with shared "
        "state, credentials and approvals.",
        "https://developer.hashicorp.com/terraform/cloud-docs/workspaces/run/remote-operations",
    ),
    "Private registry": (
        "The private registry publishes an organisation's own modules and providers for teams to consume, alongside "
        "the public ones.",
        "https://developer.hashicorp.com/terraform/cloud-docs/registry",
    ),
    "Module versioning": (
        "Modules in the private registry carry a version with each release, so consumers pin the version they use and "
        "adopt a new one deliberately.",
        "https://developer.hashicorp.com/terraform/cloud-docs/registry/publish-modules",
    ),
    "No-code provisioning": (
        "No-code provisioning lets a team deploy an approved module from the registry by filling in its variables, "
        "without writing Terraform.",
        "https://developer.hashicorp.com/terraform/cloud-docs/workspaces/no-code-provisioning/provisioning",
    ),
    "Terraform Search": (
        "Terraform Search queries existing infrastructure for resources that no configuration manages and generates "
        "the configuration to import what it finds.",
        "https://developer.hashicorp.com/terraform/cloud-docs/workspaces/import",
    ),
    "Config-driven import": (
        "An import block brings an existing resource under Terraform management as part of a normal plan and apply, "
        "and can generate the configuration for it.",
        "https://developer.hashicorp.com/terraform/language/import",
    ),
    "VCS-driven workflows": (
        "A workspace connected to a version control repository plans each pull request and starts a run when changes "
        "merge, so infrastructure changes follow the same review as other code.",
        "https://developer.hashicorp.com/terraform/cloud-docs/workspaces/run/ui",
    ),
    "Projects and workspaces": (
        "Workspaces hold the state and runs of one configuration, and projects group workspaces so that access and "
        "policy sets are scoped across the group.",
        "https://developer.hashicorp.com/terraform/cloud-docs/workspaces",
    ),
    "Policy as code": (
        "Policy as code evaluates each applicable run against rules written down centrally, before the change "
        "proceeds.",
        "https://developer.hashicorp.com/terraform/cloud-docs/policy-enforcement",
    ),
    "Policy sets": (
        "A policy set groups policies and applies them globally or to selected projects and workspaces.",
        "https://developer.hashicorp.com/terraform/cloud-docs/policy-enforcement/manage-policy-sets",
    ),
    "Enforcement levels": (
        "An enforcement level decides whether a failing policy warns, needs an override from an authorised user or "
        "stops the run, with the levels available depending on the policy framework.",
        "https://developer.hashicorp.com/terraform/cloud-docs/policy-enforcement/manage-policy-sets#policy-enforcement-levels",
    ),
    "Run tasks": (
        "A run task calls an external service, such as a security scanner or cost tool, at a stage of the run and can "
        "block the apply on its result.",
        "https://developer.hashicorp.com/terraform/cloud-docs/workspaces/settings/run-tasks",
    ),
    "Terraform Actions": (
        "Actions define day-two operations in configuration, such as invalidating a cache or restarting a service, and "
        "run them through the Terraform workflow.",
        "https://developer.hashicorp.com/terraform/language/block/action",
    ),
    "Drift detection": (
        "Drift detection compares the resources a workspace manages with its configuration on a schedule and reports "
        "where the two have diverged.",
        "https://developer.hashicorp.com/terraform/cloud-docs/workspaces/health#drift-detection",
    ),
    "Continuous validation": (
        "Continuous validation re-runs the checks and conditions written in a configuration after deployment and "
        "reports when one no longer holds.",
        "https://developer.hashicorp.com/terraform/cloud-docs/workspaces/health#continuous-validation",
    ),
    "Explorer": (
        "Explorer lists workspaces, modules, providers and health results across an organisation in one view, so "
        "drifted or failing workspaces are found without opening each.",
        "https://developer.hashicorp.com/terraform/cloud-docs/workspaces/explorer",
    ),
    "Image templates": (
        "A Packer template describes an image in HCL, so the build is repeatable and the definition is reviewed and "
        "versioned like other code.",
        "https://developer.hashicorp.com/packer/docs/templates/hcl_templates",
    ),
    "Builders and provisioners": (
        "A builder creates the image on a given platform and provisioners install and configure its contents, in an "
        "order the template sets.",
        "https://developer.hashicorp.com/packer/docs/templates/hcl_templates/blocks/build",
    ),
    "Multi-platform builds": (
        "One build block can target several sources at once, so the same provisioning steps produce images for every "
        "supported platform in parallel.",
        "https://developer.hashicorp.com/packer/docs/templates/hcl_templates/blocks/source",
    ),
    "Golden image pipeline": (
        "A golden image pipeline builds a hardened base image and layers application images on it, so each team starts "
        "from the same approved baseline.",
        "https://developer.hashicorp.com/packer/tutorials/cloud-production/golden-image-with-hcp-packer",
    ),
    "HCP Packer registry": (
        "HCP Packer records the metadata of each image Packer publishes to it, with platform identifiers, so there is "
        "one central record of registered artefacts.",
        "https://developer.hashicorp.com/hcp/docs/packer",
    ),
    "Metadata and ancestry": (
        "Each registered version carries its build metadata and the parent image it was built from, so the lineage of "
        "an image is known.",
        "https://developer.hashicorp.com/hcp/docs/packer/manage/ancestry",
    ),
    "Channels": (
        "A channel is a named pointer to an approved version, so consumers reference the channel and receive a new "
        "version when it is promoted.",
        "https://developer.hashicorp.com/hcp/docs/packer/manage/channel",
    ),
    "Revocation": (
        "Revoking a version marks it as no longer approved, and Packer refuses to build from it.",
        "https://developer.hashicorp.com/hcp/docs/packer/manage/revoke-restore",
    ),
    "HCP Packer Registry data sources": (
        "Terraform data sources read artefact metadata from an HCP Packer channel, so provisioning references the "
        "version currently assigned to it.",
        "https://developer.hashicorp.com/hcp/docs/packer/store/reference",
    ),
    "HCP Packer run task": (
        "The HCP Packer run task checks the image artefacts an HCP Terraform or Terraform Enterprise plan references "
        "and reports any that are revoked or scheduled for revocation, and can flag images the registry does not "
        "track.",
        "https://developer.hashicorp.com/hcp/docs/packer/store/validate-version",
    ),
    "SBOM association": (
        "A Standard edition HCP Packer registry associates a software bill of materials with an artefact version, so "
        "its package inventory is recorded alongside the build metadata.",
        "https://developer.hashicorp.com/hcp/docs/packer/store/sbom",
    ),
    "KV secrets engine": (
        "The KV secrets engine stores static secrets centrally, with versioning and access controlled by policy, in "
        "place of files and configuration.",
        "https://developer.hashicorp.com/vault/docs/secrets/kv",
    ),
    "Central secrets management": (
        "Vault gives one control plane for storing, issuing and auditing secrets across the platforms that consume "
        "them.",
        "https://developer.hashicorp.com/vault/docs/about-vault/what-is-vault",
    ),
    "Policies": (
        "Policies grant each identity the paths and operations it needs and nothing else.",
        "https://developer.hashicorp.com/vault/docs/concepts/policies",
    ),
    "Auth methods": (
        "Auth methods let people and workloads authenticate with an identity they already hold, such as a cloud role, "
        "Kubernetes service account or OIDC login.",
        "https://developer.hashicorp.com/vault/docs/auth",
    ),
    "Audit devices": (
        "Audit devices record requests to Vault and their responses, so secret access is attributable.",
        "https://developer.hashicorp.com/vault/docs/audit",
    ),
    "HCP Vault Radar": (
        "HCP Vault Radar scans source code, configuration and collaboration tools for secrets that are exposed or "
        "unmanaged.",
        "https://developer.hashicorp.com/vault-radar/cloud",
    ),
    "Namespaces": (
        "Namespaces in Vault Enterprise and HCP Vault Dedicated create isolated environments within one Vault cluster, "
        "each with its own policies, auth methods and secrets engines under common operation.",
        "https://developer.hashicorp.com/vault/docs/enterprise/namespaces",
    ),
    "Secrets sync": (
        "Secrets sync in Vault Enterprise and HCP Vault Dedicated copies secrets from Vault into cloud secret stores, "
        "so applications that read from those stores keep working while Vault remains the source.",
        "https://developer.hashicorp.com/vault/docs/sync",
    ),
    "AppRole": (
        "AppRole authenticates a workload with a role identifier and a secret, for cases where the platform gives it "
        "no identity of its own.",
        "https://developer.hashicorp.com/vault/docs/auth/approle",
    ),
    "SPIFFE auth method": (
        "The SPIFFE auth method, which needs a Vault Enterprise licence, lets a workload authenticate with an X.509 or "
        "JWT SVID issued by a SPIFFE identity system, giving one identity model across platforms.",
        "https://developer.hashicorp.com/vault/docs/auth/spiffe",
    ),
    "Dynamic secrets": (
        "A Vault dynamic secrets engine creates a credential when a client asks for it, unique to that client and "
        "valid for a set time.",
        "https://developer.hashicorp.com/vault/tutorials/get-started/understand-static-dynamic-secrets",
    ),
    "Static roles": (
        "A static role keeps an account's fixed credential in Vault, which rotates it on a schedule and serves the "
        "current value to clients.",
        "https://developer.hashicorp.com/vault/docs/secrets/databases#static-roles",
    ),
    "Leases, renewal and revocation": (
        "Every dynamic secret carries a lease with a time to live; clients renew it while in use and Vault revokes the "
        "credential when it expires.",
        "https://developer.hashicorp.com/vault/docs/concepts/lease",
    ),
    "PKI secrets engine": (
        "The PKI secrets engine acts as a certificate authority, holding root and intermediate CAs and issuing "
        "certificates through an API.",
        "https://developer.hashicorp.com/vault/docs/secrets/pki",
    ),
    "PKI roles": (
        "A PKI role sets what a certificate request may ask for, such as allowed domains, key types and maximum "
        "lifetime, per workload or use case.",
        "https://developer.hashicorp.com/vault/docs/secrets/pki/setup",
    ),
    "Short-lived certificates": (
        "Short-lived certificates limit how long a compromised certificate stays valid, and clients such as Vault "
        "Agent obtain replacements before expiry.",
        "https://developer.hashicorp.com/vault/docs/secrets/pki/considerations",
    ),
    "Certificate revocation": (
        "Vault revokes certificates it has issued and publishes CRLs and OCSP responses for relying parties.",
        "https://developer.hashicorp.com/vault/docs/secrets/pki/considerations#spectrum-of-revocation-support",
    ),
    "ACME": (
        "Vault serves certificates over ACME, so standard clients enrol and renew without Vault-specific tooling.",
        "https://developer.hashicorp.com/vault/docs/secrets/pki/acme",
    ),
    "Vault Secrets Operator": (
        "Vault Secrets Operator issues certificates from Vault PKI to Kubernetes workloads as native secrets and "
        "renews them before they expire.",
        "https://developer.hashicorp.com/vault/docs/deploy/kubernetes/vso",
    ),
    "Targets": (
        "A target represents one system or service a user may connect to, so access is granted to that target rather "
        "than to a network.",
        "https://developer.hashicorp.com/boundary/docs/domain-model/targets",
    ),
    "Roles and grants": (
        "Roles bind users and groups to grants that name the targets and actions they are allowed, so authorisation "
        "follows identity.",
        "https://developer.hashicorp.com/boundary/docs/domain-model/roles",
    ),
    "Workers": (
        "Workers proxy each session to its target, so private networks are reached without exposing them or placing "
        "users inside them.",
        "https://developer.hashicorp.com/boundary/docs/concepts/workers",
    ),
    "OIDC authentication": (
        "The OIDC auth method signs users in through the organisation's identity provider, so access and offboarding "
        "follow the directory.",
        "https://developer.hashicorp.com/boundary/docs/domain-model/auth-methods",
    ),
    "Credential stores": (
        "A credential store holds or fetches the credentials used for targets, from Vault or from Boundary itself, so "
        "they are managed centrally rather than by each user.",
        "https://developer.hashicorp.com/boundary/docs/domain-model/credential-stores",
    ),
    "Credential brokering": (
        "Credential brokering hands the user a credential for the target when the session starts, so none is held in "
        "advance.",
        "https://developer.hashicorp.com/boundary/docs/concepts/credential-management",
    ),
    "Credential injection": (
        "Credential injection in Boundary Enterprise and HCP Boundary places the credential into an SSH or RDP session "
        "on the user's behalf, so the user never sees it.",
        "https://developer.hashicorp.com/boundary/docs/concepts/credential-management#credential-injection",
    ),
    "Sessions": (
        "Every connection is a session that records the user, target and time, with limits on how long it lasts and "
        "how many connections it may open.",
        "https://developer.hashicorp.com/boundary/docs/domain-model/sessions",
    ),
    "Audit events": (
        "Boundary emits audit events for administrative and session activity, for forwarding to a log or SIEM.",
        "https://developer.hashicorp.com/boundary/docs/monitor/events/events",
    ),
    "Session recording": (
        "Session recording in Boundary Enterprise and HCP Boundary Plus captures SSH and RDP sessions to storage the "
        "organisation controls.",
        "https://developer.hashicorp.com/boundary/docs/session-recording",
    ),
    "SSH recording playback": (
        "Recorded SSH sessions in Boundary Enterprise and HCP Boundary Plus are played back from the Boundary "
        "interface for investigation and review.",
        "https://developer.hashicorp.com/boundary/docs/session-recording/configuration/manage-recorded-sessions",
    ),
    "Service catalogue": (
        "The catalogue holds every registered service instance and where it runs, across Kubernetes, virtual machines, "
        "Nomad and other runtimes.",
        "https://developer.hashicorp.com/consul/docs/concept/catalog",
    ),
    "Service registration": (
        "Services register their address and health checks with Consul, so the catalogue records the instances "
        "available for discovery.",
        "https://developer.hashicorp.com/consul/docs/register/service/vm",
    ),
    "Health checks": (
        "Health checks report the state of each instance, so discovery leaves out instances that are failing.",
        "https://developer.hashicorp.com/consul/docs/register/health-check/vm",
    ),
    "DNS interface": (
        "Applications look services up by name over DNS or the HTTP API, in place of configured addresses.",
        "https://developer.hashicorp.com/consul/docs/discover/dns",
    ),
    "Service failover": (
        "Failover rules send callers to instances in another datacentre or partition when the local ones are "
        "unhealthy.",
        "https://developer.hashicorp.com/consul/docs/manage-traffic/failover",
    ),
    "Cluster peering": (
        "Cluster peering connects separate Consul clusters so that services in one discover and reach services in "
        "another.",
        "https://developer.hashicorp.com/consul/docs/east-west/cluster-peering",
    ),
    "Mesh gateways": (
        "Mesh gateways carry service traffic between networks that cannot route to each other directly.",
        "https://developer.hashicorp.com/consul/docs/east-west/mesh-gateway",
    ),
    "Service mesh": (
        "The service mesh places a proxy beside each service and routes traffic through it, so identity, encryption "
        "and policy apply without application changes.",
        "https://developer.hashicorp.com/consul/docs/use-case/service-mesh",
    ),
    "Service identity and mTLS": (
        "Each service holds a certificate that names it, and the mesh uses it to authenticate and encrypt every "
        "connection between services.",
        "https://developer.hashicorp.com/consul/docs/secure-mesh",
    ),
    "Intentions": (
        "Intentions state which services may call which, by service identity, and the mesh enforces them wherever the "
        "services run.",
        "https://developer.hashicorp.com/consul/docs/secure-mesh/intention",
    ),
    "Transparent proxy": (
        "Transparent proxy redirects a service's traffic through its sidecar automatically, so an application "
        "communicates through the mesh without changes to its own configuration.",
        "https://developer.hashicorp.com/consul/docs/connect/proxy/transparent-proxy",
    ),
    "Job specification": (
        "A job specification declares what to run, with its resources, networking and lifecycle, and Nomad keeps the "
        "cluster matching it.",
        "https://developer.hashicorp.com/nomad/docs/job-specification",
    ),
    "Schedulers": (
        "The service, batch, system and system batch schedulers each handle a workload lifecycle, from long-running "
        "services to one-off and node-wide tasks.",
        "https://developer.hashicorp.com/nomad/docs/concepts/scheduling/schedulers",
    ),
    "Bin packing": (
        "The scheduler places tasks onto nodes by their resource needs, filling capacity across a shared pool.",
        "https://developer.hashicorp.com/nomad/docs/concepts/scheduling/how-scheduling-works",
    ),
    "Restart policies": (
        "A restart policy sets how a failed task is retried on the same node before it counts as failed.",
        "https://developer.hashicorp.com/nomad/docs/job-specification/restart",
    ),
    "Reschedule policies": (
        "A reschedule policy moves a failed allocation to another node, so recovery does not wait for an operator.",
        "https://developer.hashicorp.com/nomad/docs/job-specification/reschedule",
    ),
    "Update strategies": (
        "The update block controls a rollout, with rolling updates, canaries and automatic reversion when health "
        "checks fail.",
        "https://developer.hashicorp.com/nomad/docs/job-specification/update",
    ),
    "Task drivers": (
        "Task drivers run containers, plain executables, Java applications, QEMU virtual machines and other runtimes "
        "under one scheduler.",
        "https://developer.hashicorp.com/nomad/docs/job-declare/task-driver",
    ),
    "Constraints, affinities and spread": (
        "Constraints, affinities and spread tell the scheduler where a task must, should or should not run.",
        "https://developer.hashicorp.com/nomad/docs/concepts/scheduling/placement",
    ),
    "Periodic jobs": (
        "A periodic job runs on a cron schedule, for batch and housekeeping work.",
        "https://developer.hashicorp.com/nomad/docs/job-specification/periodic",
    ),
}

# DESIGN.md section 4.9. For each red or yellow answer, by answer key: the product features a
# facilitator can discuss if the respondent wants to go deeper. The first product listed is the
# one associated with the answer's capability.
POINTERS = {
    "provisioning: manual": {
        "Terraform": [
            "Infrastructure as code",
            "Remote operations",
            "Private registry",
            "No-code provisioning",
            "Terraform Search",
            "Config-driven import",
        ],
    },
    "provisioning: team-scripts": {
        "Terraform": ["Private registry", "VCS-driven workflows", "Remote operations", "Projects and workspaces"],
    },
    "provisioning: fragmented-code": {
        "Terraform": ["Private registry", "Module versioning", "Remote operations", "No-code provisioning"],
    },
    "guardrails: after-the-fact": {
        "Terraform": ["Policy as code", "Policy sets", "Run tasks", "Enforcement levels"],
    },
    "guardrails: per-team": {
        "Terraform": ["Policy sets", "Run tasks"],
    },
    "guardrails: central-approval": {
        "Terraform": ["Policy as code", "Enforcement levels", "Policy sets", "Run tasks", "No-code provisioning"],
    },
    "image build: manual": {
        "Packer": ["Image templates", "Builders and provisioners"],
    },
    "image build: fragmented-automation": {
        "Packer": ["Multi-platform builds"],
    },
    "image build: team-patterns": {
        "Packer": ["Golden image pipeline", "HCP Packer registry"],
    },
    "image lifecycle: unmanaged-versions": {
        "Packer": ["HCP Packer registry", "Metadata and ancestry", "Channels"],
    },
    "image lifecycle: manual-governance": {
        "Packer": ["Channels", "Revocation", "HCP Packer Registry data sources"],
    },
    "image lifecycle: central-no-validation": {
        "Packer": ["HCP Packer run task", "Revocation"],
    },
    "image composition: unknown-contents": {
        "Packer": ["Metadata and ancestry", "SBOM association"],
    },
    "image composition: build-steps-only": {
        "Packer": ["Metadata and ancestry", "SBOM association"],
    },
    "change and drift: by-hand": {
        "Terraform": [
            "Terraform Actions",
            "Drift detection",
            "Continuous validation",
            "Remote operations",
            "Terraform Search",
            "Config-driven import",
        ],
    },
    "change and drift: mixed": {
        "Terraform": ["Terraform Actions", "Drift detection", "Continuous validation", "Explorer", "Remote operations"],
    },
    "change and drift: fixed-by-hand": {
        "Terraform": ["Terraform Actions", "Drift detection", "Continuous validation", "Remote operations"],
    },
    "secret storage: in-files": {
        "Vault": ["KV secrets engine", "Policies", "Auth methods", "Audit devices", "HCP Vault Radar"],
    },
    "secret storage: several-stores": {
        "Vault": [
            "Central secrets management",
            "Policies",
            "Auth methods",
            "Audit devices",
            "Namespaces",
            "Secrets sync",
        ],
    },
    "workload identity: static-credential": {
        "Vault": ["Auth methods", "AppRole", "SPIFFE auth method", "Dynamic secrets"],
    },
    "workload identity: service-account": {
        "Vault": ["Auth methods", "Dynamic secrets", "Static roles"],
    },
    "workload identity: partly-platform": {
        "Vault": ["Auth methods", "AppRole", "SPIFFE auth method"],
    },
    "rotation: rarely": {
        "Vault": ["Dynamic secrets", "Leases, renewal and revocation", "Static roles"],
    },
    "rotation: manual-schedule": {
        "Vault": ["Static roles", "Dynamic secrets", "Leases, renewal and revocation", "Auth methods"],
    },
    "certificates: by-hand": {
        "Vault": [
            "PKI secrets engine",
            "Short-lived certificates",
            "Certificate revocation",
            "ACME",
            "Vault Secrets Operator",
        ],
    },
    "certificates: partly-automated": {
        "Vault": ["PKI secrets engine", "PKI roles", "ACME", "Short-lived certificates", "Vault Secrets Operator"],
    },
    "access path: direct": {
        "Boundary": ["Targets", "Roles and grants", "Workers", "OIDC authentication"],
    },
    "access path: vpn": {
        "Boundary": ["Targets", "Roles and grants", "OIDC authentication", "Workers"],
    },
    "access path: bastion": {
        "Boundary": ["Roles and grants", "Workers", "Targets"],
    },
    "access credentials: shared": {
        "Boundary": ["Roles and grants", "Credential stores", "Credential brokering", "Credential injection"],
        "Vault": ["Dynamic secrets"],
    },
    "access credentials: personal-long-lived": {
        "Boundary": [
            "OIDC authentication",
            "Roles and grants",
            "Sessions",
            "Credential brokering",
            "Credential injection",
        ],
    },
    "visibility: none": {
        "Boundary": ["Sessions", "Audit events", "Workers"],
    },
    "visibility: who-only": {
        "Boundary": ["Session recording", "SSH recording playback", "Sessions"],
    },
    "discovery: fixed-addresses": {
        "Consul": ["Service catalogue", "Service registration", "Health checks", "DNS interface", "Service failover"],
    },
    "discovery: per-environment": {
        "Consul": ["Service catalogue", "DNS interface", "Cluster peering", "Mesh gateways"],
    },
    "service-to-service security: network-location": {
        "Consul": ["Service mesh", "Service identity and mTLS", "Intentions", "Transparent proxy"],
    },
    "service-to-service security: manual-rules": {
        "Consul": ["Intentions", "Service identity and mTLS", "Service mesh"],
    },
    "service-to-service security: per-environment": {
        "Consul": ["Intentions", "Service identity and mTLS", "Service mesh", "Cluster peering", "Mesh gateways"],
    },
    "deployment: by-hand": {
        "Nomad": [
            "Job specification",
            "Schedulers",
            "Bin packing",
            "Restart policies",
            "Reschedule policies",
            "Update strategies",
        ],
    },
    "deployment: per-platform": {
        "Nomad": ["Job specification", "Task drivers", "Schedulers", "Constraints, affinities and spread"],
    },
    "non-standard workloads: individual-servers": {
        "Nomad": [
            "Task drivers",
            "Schedulers",
            "Bin packing",
            "Restart policies",
            "Reschedule policies",
            "Constraints, affinities and spread",
            "Periodic jobs",
        ],
    },
    "non-standard workloads: separate-platforms": {
        "Nomad": [
            "Task drivers",
            "Schedulers",
            "Bin packing",
            "Job specification",
            "Restart policies",
            "Reschedule policies",
            "Update strategies",
        ],
    },
}
