# HashiCorp Healthcheck: Design

The design of the HashiCorp Healthcheck questionnaire and of the readout derived from it. What the assessment is for and how to install and run it are in the [README](../README.md).

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
| IM | Image Lifecycle | Packer |
| MIS | Machine Identity and Secrets | Vault |
| HA | Human Access | Boundary |
| SN | Service Networking | Consul |
| WL | Workload Lifecycle | Nomad |

The association is where a follow-up conversation starts.

Infrastructure Lifecycle and Image Lifecycle are assessed separately. Provisioning as code and image management are distinct operating concerns, and an organisation that does not maintain machine images answers so and has no Image Lifecycle gap.

## 3. MTA behaviour the design depends on

Verified on Migration Toolkit for Applications (MTA) 8.3.0, the Red Hat build of Konveyor. The questionnaire format is documented in [questionnaire-yaml.md](https://github.com/konveyor/tackle2-hub/blob/main/docs/questionnaire-yaml.md).

- Overall risk is `count / total >= threshold / 100`, evaluated red, then yellow, then unknown, else green. `total` is every question. An unanswered question counts as unknown. A threshold of 0 always fires.
- There is no per-section or per-tag risk rollup.
- An `applyTags` entry whose category or tag does not exist in MTA is left off the application without error. It stays in the assessment.
- An assessment stores a copy of the questionnaire as it was when the assessment was created.
- Assessment tags reach the application only for a questionnaire marked required. Import honours `required: true`.
- An application has at most one assessment per questionnaire.
- An analysis entry with an effort appears under Issues. One without appears under Insights. An entry's description is rendered as Markdown, and its target technologies come from its labels.
- An addon's task token cannot read assessments ([addon guide](https://github.com/konveyor/tackle2-hub/blob/main/docs/addon-guide.md)).
- The hub mints an API key for a login presented with basic authentication. Upstream Konveyor does not require authentication by default, and then ignores the key.
- The UI keeps its login per browser tab and per host.
- The UI opens its assessment wizard as a modal from the application's assessment-actions page; the assessment route in its path table is not mounted. The wizard's button reads "Take" when no assessment exists and "Retake" otherwise, and a wizard opened by "Take" starts with no stakeholder, while one opened on an existing assessment carries that assessment's stakeholders.

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

Every answer to Q1 also applies a tag in the category `Questionnaire Version`, whose value is the questionnaire's version. The readout records it with each result as `questionnaire_version`, beside its own `readout_version`, so a result says which wording the answers were given under and which rules interpreted them. The readout does not reject an older questionnaire: an assessment stays interpretable while its answer keys exist.

The `Answer Key` and `Questionnaire Version` categories are never created in MTA. The keys therefore stay off applications but remain in each assessment, which is where the readout reads them. An assessment taken with a questionnaire that has no keys cannot be read out and must be taken again.

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
- A capability with an adjacent signal is not reported as having no signal.
- Adjacent tags do not change answer colours or the overall result.
- Every adjacent signal is reported, with its source capabilities and the answers behind it, under the headline "Adjacent signal: Machine Identity and Secrets" with the line "Derived from responses given under Human Access".
- Adjacent signals are for the facilitator. They appear in MTA and not in the executive summary.

The cross-tag table is exhaustive.

| Source answer | Adjacent | Justification |
|---|---|---|
| `access credentials: shared` | MIS | Shared credentials need issuing and rotating |

Product integration is not evidence. The service-to-service security answers establish a Service Networking concern; that service identity can be issued from a certificate authority is an implementation relationship, so they carry no Machine Identity and Secrets tag. A certificate lifecycle concern comes only from the certificates question, and the patterns combine the two where both are present. Several deployment toolchains establish fragmented delivery, not a need for shared discovery or connectivity, so `deployment: per-platform` carries no adjacent tag either.

### 4.5 Solution adjacency

Infrastructure Lifecycle is how the remedy for a gap in any other capability is usually delivered: the platform components it introduces or consolidates have to be provisioned and managed as code.

- When another capability has a direct signal and IL has none, the readout notes IL as related to implementation, with its sources.
- It is not a signal. It does not count towards the areas presented.
- When no capability has a direct signal, it does not appear.

Image Lifecycle has the same relationship with Infrastructure Lifecycle: provisioning consumes the images that image management produces. That integration creates no adjacent signal in either direction. Where answers to both establish something together, a pattern says so.

### 4.6 Overall result

{{THRESHOLDS}}

`riskMessages` carries these in signal language. Each threshold is a percentage of the questionnaire, so the counts follow from its length. Q1 is unscored but counts in the denominator. A capability's own signal does not depend on the overall result.

The overall result is a triage status in MTA. One yellow answer leaves it green while its capability has a moderate signal, so the executive summary does not show it and leads with the capability signals.

### 4.7 Presentation

1. Strong signals, then moderate.
2. Within a tier, the capability with more red answers first, then more yellow answers, then the order IL, IM, MIS, HA, SN, WL.
3. The areas with a strong signal. When none is strong, the areas with a moderate signal. Moderate areas beside a strong one are named in the summary's introduction and left for a later discussion.
4. Adjacent areas, only for capabilities with no direct signal, in the order above. They are facilitator guidance and are not presented to the respondent.
5. The solution adjacency note, if it applies, after the areas.

### 4.8 Patterns

A pattern is a combination of answers that says something neither answer says alone. Its name and detail state only what every combination of answers that triggers it establishes. Two gaps occurring together are not a pattern. The list is fixed, and a readout reports each pattern whose conditions hold. Patterns are prompts for the follow-up conversation. They do not affect risk, tags or signal strength.

A pattern's capabilities, and so its products, are derived from the answers that matched it: the union of their direct and adjacent capability tags. A definition carries no capability list of its own, so a green answer that takes part in a pattern contributes no capability, and a pattern that fires on a subset of its answers names only the capabilities those answers establish. What the combination adds belongs in the pattern's text. For example:

- "Network-centric controls without internal certificates" names Service Networking only, because the certificates answer that triggers it is green.
- "Controlled path, shared or long-lived credentials" names Human Access, and Machine Identity and Secrets as well only when the credentials are shared, through that answer's adjacent tag.
- The image patterns name Infrastructure Lifecycle only when provisioning is `fragmented-code`, the yellow answer; with `shared-code`, which is green, they name Image Lifecycle alone.
- "Distributed estate, fragmented control planes" names only the capabilities of the two or three answers that matched.

{{PATTERNS}}

A spread estate served by one platform is not a pattern: one platform can span environments.

### 4.9 Capability pointers

Each red or yellow answer has capability pointers: the features of its direct capability's product, and of an adjacent capability's product where the answer carries an adjacent tag, that a facilitator can discuss if the respondent asks what an improvement would look like. A product the answer does not establish has no pointers, however well it integrates with one that does. They are held in `healthcheck-readout/pointers.py` by answer key, as feature names. Each product also has a short talk track, in `FOLLOW_UP` in `healthcheck-readout/readout.py`.

Every feature a pointer names is in the feature catalogue in the same file: its name as the documentation uses it, one sentence saying what it does, and the page on developer.hashicorp.com that documents it. The sentence is neutral, present tense and names the edition where a feature is not in every edition of its product. A feature with no HashiCorp documentation page is not catalogued. The catalogue is the only description of a feature: the summary and the Insights print the same sentence and link.

A pattern's pointers are those of the answers behind it.

### 4.10 Readout

The `healthcheck-readout` addon derives the readout from a completed assessment. `healthcheck-readout/readout.py` is the single implementation of sections 4.3 to 4.5 and 4.7 to 4.9. The overall result (4.6) is MTA's own.

The addon cannot read the assessment itself. The Healthcheck Console service reads it, with the message for its overall result, and submits them to the addon as the task's data.

`VERSION` in `readout.py` names the interpretation and rendering rules in force and is raised when they change. The questionnaire's version is raised when its wording or tags change. Each result carries both, because an assessment keeps the questionnaire it was answered with and a readout can be generated long after.

Running the addon again replaces its previous output. The addon writes to the application:

- an analysis with one entry per red or yellow answer, one per pattern and one per adjacent signal. Each answer is entered twice, with an effort of 1 for Issues and with none for Insights. Patterns and adjacent signals are entered for Insights only. An adjacent signal's entry is in the category `Adjacent`, names its source capabilities and says that it is not a direct finding. An application's effort is therefore its number of gaps. An entry's target technologies are the capabilities and products it relates to. Its description carries the rationale, the suggested change and, for each feature its pointers name, the catalogue sentence and documentation link, under the feature's product; for a pattern it also carries the answers behind it;
- facts under the source `healthcheck-readout`: `questionnaire_version`, `readout_version`, `environment`, `verdict`, `direct`, `areas` (every area with a signal, ranked, with its product, strength, facets and evidence), `presented`, `adjacent`, `implementation`, `patterns`, `in_good_shape`, `unknowns`, `follow_up` (topics, roles, product and talk track for each presented area) and `generated`;
- an executive summary as a PDF, `healthcheck-summary.pdf` in the application's bucket (section 4.11);
- one tag per capability with a direct signal, named for the product and the strength, such as `Vault: strong`. Each product has its own tag category, in the product's brand colour. The addon creates these categories on first use.

### 4.11 Executive summary

The summary is the document sent to the respondent after the session. `healthcheck-readout/summary.py` writes it from the readout as Pandoc Markdown, and renders it to A4 PDF with Pandoc, the Tectonic TeX engine, the Eisvogel template and IBM Plex Sans. The addon's image is built on the UBI Python image. Its build downloads those four from their GitHub releases, the product marks from the Flight icons package and the TeX files the summary needs, and installs svglib and reportlab to render the marks, so the addon needs no network to render.

It contains:

1. a title page with the organisation as its title, the healthcheck's name as its subtitle and the date the readout was generated;
2. an introduction that states the purpose and says that the highest priority areas are the ones the report covers, with a table of the environment, the areas highlighted and the areas not highlighted;
3. one section per presented area (section 4.7), in ranked order, with a row per red or yellow answer: the aspect, the response, what it means (the rationale) and the suggested change (the mitigation), in four columns. The section's heading and table are kept on one page by an estimate of the table's height. The first section's heading is followed by a paragraph saying which tier the sections cover: the strong areas as the highest priority with the moderate ones left for a later discussion, every area when all are strong, or the moderate areas when none is strong;
4. the patterns that hold;
5. the questions answered "unknown";
6. a next step per presented area, with the product's mark: a recommendation of a follow-up session on the product, then one paragraph per red or yellow answer made of the catalogue sentences of its pointers, each with its documentation page as a footnote, then the roles worth involving. A feature appears once per area, and a documentation page is footnoted once per summary; a later mention repeats the footnote's number;
7. when the solution adjacency note applies (section 4.5), a closing sentence naming Infrastructure Lifecycle's product as relevant to those sessions.

When no area has a signal, the introduction says so, and the summary has no next steps and makes no claim that further discussion would help.

Every area with a signal remains in MTA. The summary names products only in its next steps and the closing sentence, and features only through the catalogue sentences there. It carries no talk tracks, which are for the facilitator.

The title page uses `healthcheck-readout/cover.pdf` as its background when the file is present at build time. The file is not in the repository.

## 5. Questions

Every question is single choice and has an explanation shown to the respondent. There is no branching: `includeFor`, `excludeFor` and `autoAnswerFor` are not used. "Direct" and "Adjacent" list the capability tags an answer applies.

Eighteen questions is the limit, and the questionnaire is at it: at 15 to 20 seconds each, eighteen take between four and a half and six minutes, which is the "5 Minute" of the name. A further question must replace one.

{{QUESTIONS}}
### Rationale and mitigation

- Every red and yellow answer has a rationale of one or two sentences that says why the operating condition matters.
- Every red and yellow answer has a mitigation that describes the capability improvement.
- Green and unknown answers have neither.

## 6. Tests

`test_questionnaire.py` needs no MTA instance. It uses the standard library's `unittest` and PyYAML.

Structure of the questionnaire:

- Required schema fields are present, orders are sequential, every `risk` is one of the four values and every question has an explanation.
- Eighteen questions, each with 4 to 6 answers, and no branching.
- Every answer has exactly one key, keys are unique, and each question has one facet of its own.
- Each red or yellow answer applies exactly one `Capability Signal` tag, and all such answers to a question apply the same one. No other answer applies a capability tag.
- Each scored question has at least one green answer and exactly one unknown answer. Q1 answers are all green.
- Each capability is the direct tag of at least two questions.
- Adjacent tags equal the cross-tag table in section 4.4.
- Every Q1 answer carries the same questionnaire version, and no other answer carries one.
- Red and yellow answers have a rationale and a mitigation. Green and unknown answers have neither.
- Every key a pattern refers to exists.
- Capability pointers exist for exactly the red and yellow answers, each lists its capability's own product first, and each names exactly the products of the answer's direct and adjacent capabilities.
- Every feature a pointer names is catalogued, and every catalogued feature is named by a pointer, with a one-sentence description and a documentation page on developer.hashicorp.com.
- No string in the questionnaire contains Terraform, Packer, Vault, Boundary, Consul, Nomad or HashiCorp, apart from the questionnaire's name.
- `DESIGN.md` equals the output of `gen_design.py`.

Personas, in `personas.yaml`: ten reference respondents, each with its answers and its expected direct signals, presented areas, adjacent signal, solution adjacency, patterns and overall result.

- Every persona's readout equals its expected values. The overall result is computed with the threshold rule in section 3.
- Every pattern holds for at least one persona.
- For every persona, the gaps reported are exactly its red and yellow answers, with their wording.
- For every persona, the executive summary has a section for each presented area and a row for each of its answers.
- For every persona, no area with a direct or adjacent signal is reported as having no signal.
- For every persona, the summary says further discussion would benefit the organisation, and lists next steps, only when an area is highlighted.
- The three image questions signal Image Lifecycle on red and yellow answers only, each has a not-applicable answer, and choosing not-applicable for all three creates no signal, pattern or product.
- No service-to-service security answer carries an adjacent tag, and the certificate pattern still holds when a certificates answer supplies the evidence.
- The drift answer "found and fixed by hand" is yellow, Infrastructure Lifecycle, and its mitigation claims no automatic reconciliation.
- Patterns do not change direct signals or evidence.
- For every pattern a persona triggers, its capabilities equal the union of the direct and adjacent tags of its matched answers, and its products are those capabilities' products.
- Service Networking evidence alone, with or without "certificates are not used", surfaces no Vault pointer and no Vault pattern product.
- The summary does not contain the overall result's message.
- The summary shows exactly the presented areas: the strong areas, or the moderate ones when none is strong; persona A has six areas with a signal and four sections and next steps. Each presented area's next step carries the catalogue sentence of every feature its pointers name, and each documentation page once.
- The summary's metadata carries the versions in the readout it renders, not the running code's.
- The sample readout the image build renders is accepted by the summary.
- Single-gap matrix: from an all-green baseline, each red or yellow answer on its own gives exactly its capability's signal, its own evidence, its own adjacency and no pattern that does not involve it.

{{PERSONAS}}

## 7. Repository layout

The repository root is a Helm chart, so that the chart can package the sources below.

```text
.github/workflows/e2e.yml
README.md
Chart.yaml
values.yaml
templates/
hashicorp-healthcheck/
├── DESIGN.md
├── design.tmpl.md
├── gen_design.py
├── questionnaire.yaml
├── setup.py
├── personas.yaml
└── test_questionnaire.py
healthcheck-readout/
├── Containerfile
├── app.py
├── readout.py
├── pointers.py
├── summary.py
└── fetch.py
healthcheck-console/
├── Containerfile
├── app.py
├── fetch.py
└── index.html
kind/
├── cluster.yaml
├── requirements.yml
├── up.yml
├── down.yml
├── podman/
├── docker/
├── e2e.py
└── smoke.py
```

On OpenShift the chart builds the two images on the cluster from their Containerfiles. Elsewhere they are built locally; `kind/` holds the playbooks that do so for a kind cluster on Podman or Docker, with each engine's own steps in its directory, `kind/e2e.py`, which checks a live environment persona by persona, and `kind/smoke.py`, which drives the console's page in a browser. The workflow in `.github/workflows/` runs the tests, lints the chart and runs both checks on a kind cluster.

`setup.py` runs as the chart's setup job: on OpenShift it starts the image builds, and everywhere it mints the service's API key, seeds the signal tag categories and imports the questionnaire.

`DESIGN.md` is generated: `gen_design.py` fills `design.tmpl.md` with the question and pattern tables from `questionnaire.yaml` and `readout.py`. Edit the template and run the script; a test fails when the two differ.

## 8. Out of scope

The deeper discovery assessment, product-specific discovery beyond the capability pointers in section 4.9, pricing, solution architecture, numerical scoring, sales qualification, CRM integration and any change to MTA itself.

### Coverage boundaries

Conditions reviewed and left out of the questionnaire. Each stays out until a question can establish it directly within the time budget.

- Identity for workloads that never obtain a credential. The workload identity question asks how an application proves itself to the systems it depends on; a workload with no such dependency is not covered.
- Delegated, transaction-scoped authority for agents acting independently or for a user. Few respondents can report an operating condition yet; the Vault talk track raises it after workload identity.
- Policy frameworks in beta. The guardrail answers point at production policy mechanisms only; a beta framework joins the pointers when it leaves beta.
- Multi-port service configuration and certificate telemetry in a service mesh. No answer establishes that the respondent runs a mesh, so neither is attributed; both are facilitator knowledge.
- Workload identity issued by a scheduler. Orchestration fragmentation establishes no identity problem; the Nomad talk track links the two conversations and the workload identity question carries the evidence.
- Whether credentials pass through infrastructure-as-code plan and state. No answer establishes it; the Terraform talk track covers ephemeral values and write-only arguments as implementation guidance.
