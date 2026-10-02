# HashiCorp Snapshot: Design

The design of the HashiCorp Snapshot questionnaire and of the readout derived from it. What the assessment is for and how to install and run it are in the [README](../README.md).

## 1. Principles

1. Questions ask about the respondent's operating model, never about HashiCorp products. A respondent who has never heard of HashiCorp can answer every question.
2. Answers describe observable states, not opinions of maturity or intent.
3. Respondent-facing text calls a result a signal: "signal", "area to explore", "further discussion".
4. A capability may produce no signal.
5. Risk colour and capability are separate: colour is the degree of gap, the tag is the area the gap relates to.
6. Risk reflects what an answer directly establishes, not a plausible problem that might sit behind it. Where an answer is ambiguous it takes the lower risk, and another question or a pattern establishes the gap.
7. Product names appear only in the readout, which is for the follow-up team. No question, answer, explanation, rationale or mitigation contains one. The questionnaire's name is the one place the company is named.

## 2. Capability model

| Abbreviation | Capability | Associated product |
|---|---|---|
| IL | Infrastructure Lifecycle | Terraform |
| MIS | Machine Identity and Secrets | Vault |
| HA | Human Access | Boundary |
| SN | Service Networking | Consul |
| WL | Workload Lifecycle | Nomad |

The association is where a follow-up conversation starts.

## 3. MTA behaviour the design depends on

Verified on Migration Toolkit for Applications (MTA) 8.3.0, the Red Hat build of Konveyor. The questionnaire format is documented in [questionnaire-yaml.md](https://github.com/konveyor/tackle2-hub/blob/main/docs/questionnaire-yaml.md).

- Overall risk is `count / total >= threshold / 100`, evaluated red, then yellow, then unknown, else green. `total` is every question. An unanswered question counts as unknown. A threshold of 0 always fires.
- There is no per-section or per-tag risk rollup.
- An `applyTags` entry whose category or tag does not exist in MTA is left off the application without error. It stays in the assessment.
- An assessment stores a copy of the questionnaire as it was when the assessment was created.
- Assessment tags reach the application only for a questionnaire marked required. Import honours `required: true`.
- An application has at most one assessment per questionnaire.
- An analysis entry with an effort appears under Issues. One without appears under Insights. An entry's description is rendered as Markdown, and its target technologies come from its labels.
- An addon's task token cannot read assessments.
- The hub mints an API key for a login presented with basic authentication. Upstream Konveyor does not require authentication by default, and then ignores the key.
- The UI keeps its login per browser tab and per host.

## 4. Signal model

### 4.1 Answer risk

| Risk | Meaning |
|---|---|
| red | Manual, shared, static or unmanaged practice that is hard to scale or carries clear exposure |
| yellow | The capability exists but is fragmented, inconsistent or partly manual |
| green | This answer does not itself indicate a material gap |
| unknown | The respondent cannot say |

Unknown is never treated as red.

### 4.2 Answer keys

Every answer applies one tag in the category `Answer Key`, of the form `facet: key`, for example `rotation: rarely`. The facet is the same for every answer to a question and names what the question covers. The keys are listed in section 5.

Sections 4.4 and 4.8 and the readout refer to answers by key, never by position, so questions and answers can be reordered or added without changing them.

The `Answer Key` category is never created in MTA. The keys therefore stay off applications but remain in each assessment, which is where the readout reads them. The chart's setup job does not seed it. An assessment taken with a questionnaire that has no keys cannot be read out and must be taken again.

### 4.3 Direct signal

Each capability has two or three questions, each covering one facet. A capability's direct signal is the worst colour among them.

| Worst colour | Direct signal |
|---|---|
| red | strong |
| yellow | moderate |
| green or unknown | none |

Red and yellow answers apply the capability's tag in category `Capability Signal`. Green and unknown answers apply no capability tag.

### 4.4 Adjacent signal

An adjacent signal is evidence from another capability's question that also exposes a gap in this capability. It is recorded in category `Adjacent Capability Signal`, using the same capability names.

- Adjacent ranks below moderate.
- A capability with a direct signal absorbs its adjacent signal.
- Adjacent tags do not change answer colours or the overall result.
- An adjacent signal is reported with its source capabilities, for example "Machine Identity and Secrets: adjacent, via Human Access".

The cross-tag table is exhaustive.

| Source answer | Adjacent | Justification |
|---|---|---|
| `access credentials: shared` | MIS | Shared credentials need issuing and rotating |
| `service-to-service security: network-location` and `service-to-service security: manual-rules` | MIS | Service identity depends on certificate issuance |
| `deployment: per-platform` | SN | Workloads on different platforms need common discovery and connectivity |

### 4.5 Solution adjacency

Infrastructure Lifecycle is how the remedy for a gap in any other capability is usually delivered: the platform components it introduces or consolidates have to be provisioned and managed as code. That is an implementation relationship, not evidence that infrastructure delivery is deficient.

- When another capability has a direct signal and IL has none, the readout notes IL as related to implementation, with its sources.
- It is not a signal. It does not count towards the areas presented.
- When no capability has a direct signal, it does not appear.

### 4.6 Overall result

```yaml
thresholds:
  red: 5
  yellow: 12
  unknown: 25
```

With 14 to 16 questions this gives:

| Overall | Condition | Message intent |
|---|---|---|
| red | one or more red answers | Follow-up discussion indicated |
| yellow | no red, two or more yellow | Areas worth exploring |
| unknown | neither of the above, four or more unknown | Not enough information for a signal |
| green | otherwise | No deeper session indicated by this snapshot |

`riskMessages` carries these in signal language. One red answer makes the overall result red. Q1 is unscored but counts in the denominator.

### 4.7 Presentation

1. Strong signals, then moderate.
2. Within a tier, the capability with more red answers first, then more yellow answers, then the order IL, MIS, HA, SN, WL.
3. At most three direct areas.
4. At most one adjacent area, only for a capability with no direct signal. Where several qualify, the one with the most source capabilities, ties broken by the order above.
5. The solution adjacency note, if it applies, after the areas.

### 4.8 Patterns

A pattern is a combination of answers that says something neither answer says alone. Two gaps occurring together are not a pattern. The list is fixed, and a readout reports each pattern whose conditions hold. Patterns are prompts for the follow-up conversation. They do not affect risk, tags or signal strength.

| Pattern | Holds when | Meaning | Areas |
|---|---|---|---|
| Automation stops at day one | `provisioning` is `fragmented-code` or `shared-code`, and `change and drift` is `by-hand` or `mixed` | Infrastructure is provisioned as code, but later changes are made by hand. | IL |
| Automated delivery without guardrails | `provisioning` is `fragmented-code` or `shared-code`, and `guardrails` is `after-the-fact` or `per-team` | Infrastructure is delivered as code, but standards are checked by hand or team by team. | IL |
| Automated delivery with a human gate | `provisioning` is `fragmented-code` or `shared-code`, and `guardrails` is `central-approval` | Infrastructure delivery is automated, but every change still waits for a central team to approve it by hand. | IL |
| Centralised but static | `secret storage` is `central-store`, and `rotation` is `manual-schedule` or `rarely` | Secrets are held in one central store, but credentials are long-lived or rotated by hand. | MIS |
| Controlled path, uncontrolled credentials | `access path` is `brokered`, and `access credentials` is `personal-long-lived` or `shared` | Access is brokered to specific systems, but the credentials used are shared or long-lived. | MIS, HA |
| Identity without session accountability | `access credentials` is `per-session` or `single-sign-on`, and `visibility` is `none` or `who-only` | Access is tied to an individual or issued per session, but what was done in a session cannot be fully shown afterwards. | HA |
| Trust by network location | `access path` is `direct` or `vpn`, and `service-to-service security` is `network-location` | Engineer access and traffic between services both rest on being inside the network. | HA, SN |
| Distributed estate, fragmented control planes | `environment` is `hybrid` or `several-clouds`, and at least two of: `discovery` is `per-environment`; `service-to-service security` is `per-environment`; `deployment` is `per-platform` | Workloads span several environments, and discovery, traffic policy or deployment is done differently in each. | SN, WL |
| Deployment is standardised, networking is not | `deployment` is `one-workflow`, and one of: `discovery` is `per-environment`; `service-to-service security` is `per-environment` | Workloads are deployed through one consistent workflow across platforms, but discovery or traffic policy still differs by environment. | SN |
| Non-standard workloads sit outside the main platform | `deployment` is `one-platform`, and `non-standard workloads` is `individual-servers` or `separate-platforms` | The main platform meets most needs, but batch, legacy or non-containerised workloads are run by hand or on separate tooling. | WL |
| Network rules without service identity | `service-to-service security` is `manual-rules` or `network-location`, and `certificates` is `by-hand` or `not-used` or `partly-automated` | Traffic between services is controlled by network location or hand-maintained rules, and certificate-based service identity is absent, uneven or manual. | MIS, SN |

A spread estate served by one platform is not a pattern: one platform can span environments.

### 4.9 Capability pointers

Each red or yellow answer has capability pointers: the capabilities of the associated product, and of a second product where the answer spans two, that a facilitator can discuss if the respondent asks what an improvement would look like. They are held in `snapshot-readout/pointers.py` by answer key. Each product also has a short talk track.

A pattern's pointers are those of the answers behind it.

Pointers are never part of the questionnaire. Its mitigation text stays product-neutral.

### 4.10 Readout

The `snapshot-readout` addon derives the readout from a completed assessment. `snapshot-readout/readout.py` is the single implementation of sections 4.3 to 4.5 and 4.7 to 4.9. The overall result (4.6) is MTA's own.

The addon cannot read the assessment itself. The Snapshot Console service reads it, with the message for its overall result, and submits them to the addon as the task's data.

Running the addon again replaces its previous output. The addon writes to the application:

- an analysis with one entry per red or yellow answer and one per pattern. Each answer is entered twice, with an effort of 1 for Issues and with none for Insights. Patterns are entered for Insights only. An application's effort is therefore its number of gaps. An entry's target technologies are the capabilities and products it relates to. Its description carries the rationale, the mitigation and the capability pointers, and for a pattern the answers behind it;
- facts under the source `snapshot-readout`: `environment`, `verdict`, `direct`, `areas` (every area with a signal, ranked, with its product, strength, facets and evidence), `presented`, `adjacent`, `implementation`, `patterns`, `in_good_shape`, `unknowns`, `follow_up` (topics, roles, product and talk track for each presented area) and `generated`;
- one tag per capability with a direct signal, named for the product and the strength, such as `Vault: strong`. Each product has its own tag category, in the product's brand colour. The addon creates these categories on first use.

## 5. Questions

Every question is single choice and has an explanation shown to the respondent. There is no branching: `includeFor`, `excludeFor` and `autoAnswerFor` are not used. "Direct" and "Adjacent" list the capability tags an answer applies.

Sixteen questions is the limit: at about 20 seconds each, fourteen already fill five minutes.

### Section 1: Environment

**Q1 (environment). Where do most of your workloads run today?**

| # | Answer | Key | Risk | Direct | Adjacent |
|---|---|---|---|---|---|
| 1 | Mostly in one public cloud | `one-cloud` | green |  |  |
| 2 | Across several public clouds | `several-clouds` | green |  |  |
| 3 | Mostly in our own data centres | `own-data-centres` | green |  |  |
| 4 | A mix of our own data centres and public cloud | `hybrid` | green |  |  |

Q1 is context. It opens the conversation and helps the facilitator read the later answers. Its answers are green and carry no signal tag.

### Section 2: Infrastructure Delivery

**Q2 (provisioning). How is most infrastructure provisioned today?**

| # | Answer | Key | Risk | Direct | Adjacent |
|---|---|---|---|---|---|
| 1 | Through cloud consoles, tickets or other manual steps | `manual` | red | IL |  |
| 2 | With scripts or automation that each team maintains for itself | `team-scripts` | yellow | IL |  |
| 3 | With infrastructure as code, but tools and patterns differ between teams | `fragmented-code` | yellow | IL |  |
| 4 | With infrastructure as code built from shared, reusable patterns | `shared-code` | green |  |  |
| 5 | I don't know | `unknown` | unknown |  |  |

**Q3 (guardrails). How are your organisation's standards and policies applied to new infrastructure?**

| # | Answer | Key | Risk | Direct | Adjacent |
|---|---|---|---|---|---|
| 1 | By manual review, or after the fact when a problem is found | `after-the-fact` | red | IL |  |
| 2 | Each team applies its own checks | `per-team` | yellow | IL |  |
| 3 | A central team reviews and approves changes by hand | `central-approval` | yellow | IL |  |
| 4 | Automated checks run on every change, and teams self-serve within them | `automated` | green |  |  |
| 5 | I don't know | `unknown` | unknown |  |  |

**Q4 (change and drift). Once infrastructure is built, how are changes made to it?**

| # | Answer | Key | Risk | Direct | Adjacent |
|---|---|---|---|---|---|
| 1 | Mostly by hand; records often don't match what is running | `by-hand` | red | IL |  |
| 2 | A mix of automation and manual changes; differences surface when something breaks | `mixed` | yellow | IL |  |
| 3 | Through automation, but differences are found and fixed by hand | `fixed-by-hand` | yellow | IL |  |
| 4 | Through the same automated workflow that built it; differences are detected and corrected | `reconciled` | green |  |  |
| 5 | I don't know | `unknown` | unknown |  |  |

### Section 3: Security and Access

**Q5 (secret storage). How do applications typically obtain credentials such as database passwords or API keys?**

| # | Answer | Key | Risk | Direct | Adjacent |
|---|---|---|---|---|---|
| 1 | From configuration files, source code or settings maintained by hand | `in-files` | red | MIS |  |
| 2 | From several secret stores, depending on the platform or team | `several-stores` | yellow | MIS |  |
| 3 | From one central secrets store | `central-store` | green |  |  |
| 4 | They are issued automatically, based on the application's own identity | `identity-issued` | green |  |  |
| 5 | I don't know | `unknown` | unknown |  |  |

**Q6 (rotation). How long do application credentials usually stay valid?**

| # | Answer | Key | Risk | Direct | Adjacent |
|---|---|---|---|---|---|
| 1 | Until someone changes them by hand; they are rarely rotated | `rarely` | red | MIS |  |
| 2 | They are rotated on a schedule, mostly by a manual process | `manual-schedule` | yellow | MIS |  |
| 3 | They are rotated automatically on a schedule | `automatic` | green |  |  |
| 4 | They are short-lived and issued on demand | `short-lived` | green |  |  |
| 5 | I don't know | `unknown` | unknown |  |  |

**Q7 (certificates). How are certificates for internal services issued and renewed?**

| # | Answer | Key | Risk | Direct | Adjacent |
|---|---|---|---|---|---|
| 1 | Requested and renewed by hand; expiries have caused outages | `by-hand` | red | MIS |  |
| 2 | Partly automated; it varies by team or platform | `partly-automated` | yellow | MIS |  |
| 3 | Issued and renewed automatically for most services | `automated` | green |  |  |
| 4 | Certificates are not commonly used for internal services | `not-used` | green |  |  |
| 5 | I don't know | `unknown` | unknown |  |  |

This question covers certificate lifecycle where certificates exist. Whether their absence is a gap is left to the service-to-service security question and to the pattern "Network rules without service identity".

**Q8 (access path). How do engineers connect to servers, databases and clusters to administer them?**

| # | Answer | Key | Risk | Direct | Adjacent |
|---|---|---|---|---|---|
| 1 | Directly from the corporate network, with nothing in between | `direct` | red | HA |  |
| 2 | Through a VPN that gives broad network access once connected | `vpn` | yellow | HA |  |
| 3 | Through bastion or jump hosts managed separately per environment | `bastion` | yellow | HA |  |
| 4 | Through an access service that connects them only to the systems they are approved for | `brokered` | green |  |  |
| 5 | I don't know | `unknown` | unknown |  |  |

**Q9 (access credentials). What credentials are used to get into the systems engineers administer?**

| # | Answer | Key | Risk | Direct | Adjacent |
|---|---|---|---|---|---|
| 1 | Shared accounts, keys or passwords | `shared` | red | HA | MIS |
| 2 | Personal keys or passwords that each engineer manages and that rarely expire | `personal-long-lived` | yellow | HA |  |
| 3 | Their single sign-on identity, with access granted by role | `single-sign-on` | green |  |  |
| 4 | Credentials issued or injected for the session that expire automatically; engineers may never see them | `per-session` | green |  |  |
| 5 | I don't know | `unknown` | unknown |  |  |

**Q10 (visibility). Could you show who accessed a given production system last week, and what they did?**

| # | Answer | Key | Risk | Direct | Adjacent |
|---|---|---|---|---|---|
| 1 | No, or only by piecing together logs from several places | `none` | red | HA |  |
| 2 | Who connected, yes; what they did, no | `who-only` | yellow | HA |  |
| 3 | Yes; sessions are centrally logged or recorded | `recorded` | green |  |  |
| 4 | I don't know | `unknown` | unknown |  |  |

### Section 4: Runtime and Connectivity

**Q11 (discovery). How do applications find each other across your environments?**

| # | Answer | Key | Risk | Direct | Adjacent |
|---|---|---|---|---|---|
| 1 | Fixed addresses or host files maintained by hand | `fixed-addresses` | red | SN |  |
| 2 | A different mechanism in each environment | `per-environment` | yellow | SN |  |
| 3 | Everything runs on one platform and its built-in discovery is enough | `one-platform` | green |  |  |
| 4 | One discovery layer spans all environments | `spanning-layer` | green |  |  |
| 5 | I don't know | `unknown` | unknown |  |  |

**Q12 (service-to-service security). How is traffic between applications controlled?**

| # | Answer | Key | Risk | Direct | Adjacent |
|---|---|---|---|---|---|
| 1 | Mostly by network location; once inside, services can reach each other freely | `network-location` | red | SN | MIS |
| 2 | Firewall rules or address lists updated by ticket or by hand | `manual-rules` | yellow | SN | MIS |
| 3 | Each environment has its own policy mechanism, managed separately | `per-environment` | yellow | SN |  |
| 4 | Everything runs on one platform and its built-in policies are enough | `one-platform` | green |  |  |
| 5 | Services authenticate each other and traffic is encrypted, with one set of rules per service | `service-identity` | green |  |  |
| 6 | I don't know | `unknown` | unknown |  |  |

**Q13 (deployment). How are application workloads deployed and run?**

| # | Answer | Key | Risk | Direct | Adjacent |
|---|---|---|---|---|---|
| 1 | Mostly installed and started on servers by hand or with ad-hoc scripts | `by-hand` | red | WL |  |
| 2 | On several platforms, each with its own deployment tooling | `per-platform` | yellow | WL | SN |
| 3 | Mostly on one platform, such as Kubernetes or OpenShift, which meets our needs | `one-platform` | green |  |  |
| 4 | On several platforms, through one consistent deployment workflow | `one-workflow` | green |  |  |
| 5 | I don't know | `unknown` | unknown |  |  |

**Q14 (non-standard workloads). How do you run workloads that don't fit your main platform, such as batch jobs, legacy applications or software that isn't containerised?**

| # | Answer | Key | Risk | Direct | Adjacent |
|---|---|---|---|---|---|
| 1 | On individually managed servers, by hand or with scheduled scripts | `individual-servers` | red | WL |  |
| 2 | On separate platforms or tools for each type | `separate-platforms` | yellow | WL |  |
| 3 | We have few or none of these | `few` | green |  |  |
| 4 | The same platform and workflow handles them | `same-platform` | green |  |  |
| 5 | I don't know | `unknown` | unknown |  |  |

### Rationale and mitigation

- Every red and yellow answer has a rationale of one or two sentences that says why the operating condition matters.
- Every red and yellow answer has a mitigation that describes the capability improvement.
- Green and unknown answers have neither.

## 6. Tests

`test_questionnaire.py` needs no MTA instance. It uses the standard library's `unittest` and PyYAML.

Structure of the questionnaire:

- Required schema fields are present, orders are sequential, every `risk` is one of the four values and every question has an explanation.
- 14 to 16 questions, each with 4 to 6 answers, and no branching.
- Every answer has exactly one key, keys are unique, and each question has one facet of its own.
- Each red or yellow answer applies exactly one `Capability Signal` tag, and all such answers to a question apply the same one. No other answer applies a capability tag.
- Each scored question has at least one green answer and exactly one unknown answer. Q1 answers are all green.
- Each capability is the direct tag of at least two questions.
- Adjacent tags equal the cross-tag table in section 4.4.
- Red and yellow answers have a rationale and a mitigation. Green and unknown answers have neither.
- Every key a pattern refers to exists.
- Capability pointers exist for exactly the red and yellow answers, and each lists its capability's own product first.
- No string in the questionnaire contains Terraform, Vault, Boundary, Consul, Nomad or HashiCorp, apart from the questionnaire's name.

Personas, in `personas.yaml`: nine reference respondents, each with its answers and its expected direct signals, presented areas, adjacent signal, solution adjacency, patterns and overall result.

- Every persona's readout equals its expected values. The overall result is computed with the threshold rule in section 3.
- Every pattern holds for at least one persona.
- For every persona, the gaps reported are exactly its red and yellow answers, with their wording.

| Persona | Shows |
|---|---|
| A: highly manual enterprise | Signals in all five capabilities; three presented |
| B: mature OpenShift platform, static secrets | One strong signal; IL as a solution adjacency note only |
| C: fragmented infrastructure as code | A moderate signal and an overall result of yellow |
| D: mature platform organisation | No signal in any capability; overall green |
| E: respondent lacks visibility | Four unknown answers; overall unknown |
| F: mature platform, shared admin accounts | An adjacent signal that is not absorbed |
| G: capable platform with contradictions | Four patterns; ordering within the strong tier |
| H: hybrid estate, partly standardised | Three moderate signals and three patterns |
| I: consistent deployment, uneven networking | One yellow answer: a moderate signal with an overall result of green |

## 7. Repository layout

The repository root is a Helm chart, so that the chart can package the sources below.

```text
README.md
Chart.yaml
values.yaml
templates/
hashicorp-snapshot/
├── DESIGN.md
├── questionnaire.yaml
├── setup.py
├── personas.yaml
└── test_questionnaire.py
snapshot-readout/
├── Containerfile
├── app.py
├── readout.py
└── pointers.py
snapshot-console/
├── Containerfile
├── app.py
└── index.html
kind/
├── cluster.yaml
├── up.yml
└── down.yml
```

On OpenShift the chart builds the two images on the cluster from their Containerfiles. Elsewhere they are built locally; `kind/` holds the playbooks that do so for a kind cluster.

`setup.py` runs as the chart's setup job: on OpenShift it starts the image builds, and everywhere it mints the service's API key, seeds the signal tag categories and imports the questionnaire.

## 8. Out of scope

The deeper discovery assessment, product-specific discovery beyond the capability pointers in section 4.9, pricing, solution architecture, numerical scoring, sales qualification, CRM integration and any change to MTA itself.
