# Konveyor HashiCorp Surveys

## The 5 Minute HashiCorp Healthcheck

An 18-question Konveyor questionnaire for a booth or introductory session. A technical practitioner answers it in around five minutes. No knowledge of HashiCorp products is needed.

It indicates whether a deeper discovery session is warranted, and in which of six capability areas it should start: infrastructure lifecycle, image lifecycle, machine identity and secrets, human access, service networking and workload lifecycle.

It is not an architecture assessment or a lead score. Its results are signals for a follow-up. The readout names the product associated with each area as the starting point for that follow-up.

It runs on upstream Konveyor, on a laptop with kind, or on Migration Toolkit for Applications (MTA) on OpenShift. Validated against Konveyor v0.11.0 and MTA 8.3.0. The design is in [hashicorp-healthcheck/DESIGN.md](hashicorp-healthcheck/DESIGN.md).

## Components

- `hashicorp-healthcheck/`: the questionnaire, its tests and its design.
- `healthcheck-console/`: a small Python service served on MTA's own host at `/console/`. Its page starts an assessment from an organisation and a contact email, generates readouts, serves each respondent's executive summary and has a maintenance tab. It is styled with Helios, the HashiCorp design system, whose stylesheet and icons the image build fetches. Sharing MTA's host keeps a logged-in browser tab logged in when the page sends it on to the questionnaire.
- `healthcheck-readout/`: an MTA addon. It derives the readout from a completed assessment and writes it to the application as Issues, Insights, facts, product tags and an executive summary in PDF. For each highlighted aspect the summary gives the response, what it means, a suggested change and the business impact of making it, in terms of speed, cost and risk. Running it again replaces its previous output.

## Install on kind

Two Ansible playbooks stand the whole environment up on a laptop, with upstream Konveyor, and remove it again. Once it is up it needs no network connection. This is the usual way to run the healthcheck; OpenShift is covered below.

Prerequisites:

- Podman or Docker with at least 6 GB of memory available to it.
- `kind`, `helm`, `git` and `ansible`, with the collections in `kind/requirements.yml`.
- An A4 cover for the summary's title page at `healthcheck-readout/cover.pdf`, at most 500 KB. The file is not tracked. Without it the title page is plain.
- Outbound access during `kind/up.yml`, which fetches the Konveyor operator, the ingress controller, the base image from `registry.access.redhat.com`, releases from `github.com`, Helios assets from `unpkg.com`, two packages from PyPI and a TeX distribution. After that the environment runs offline.

```sh
ansible-galaxy collection install -r kind/requirements.yml
ansible-playbook kind/up.yml
```

The first run takes about ten minutes, most of it building the readout image. Running it again rebuilds only what changed.

The playbooks use Podman when it answers and Docker otherwise. To name one, add `-e engine=podman` or `-e engine=docker` to both. The steps that differ by engine are in `kind/podman/` and `kind/docker/`, each written with that engine's collection.

The playbook creates a kind cluster, installs an ingress controller and the Konveyor operator, builds the two images from their Containerfiles and loads them into the cluster, installs this chart and waits until Healthcheck Console can reach Konveyor. It ends by printing the two addresses below. On a cluster without OpenShift builds the chart uses those images and an Ingress in place of the builds and the Route.

- Konveyor: `https://localhost:8443/`
- Healthcheck Console: `https://localhost:8443/console/`
- Kubeconfig: `kind/kubeconfig`

Upstream Konveyor does not require a login by default, so the questionnaire opens without one and no credentials are configured.

To serve a trusted certificate, put a certificate for `localhost` with its chain in `kind/tls.crt` and its key in `kind/tls.key` before running the playbook. Neither file is tracked. Without them the ingress controller serves its self-signed certificate.

After a restart of the laptop, start the container engine and then the cluster's container, with `podman` or `docker`:

```sh
podman start healthcheck-control-plane
```

To remove the cluster, its kubeconfig and the two local images:

```sh
ansible-playbook kind/down.yml
```

## Install on OpenShift

The repository root is a Helm chart, the same one the kind playbook installs. On OpenShift it takes a namespace that holds only the MTA or Konveyor operator to a working environment: the instance, the questionnaire and its tags, Healthcheck Console on the UI's host and the readout addon, with the two images built on the cluster.

Prerequisites:

- An OpenShift cluster with the MTA or Konveyor operator installed in the target namespace, and no instance in it. The chart creates the instance.
- `oc` and `helm`, logged in as an admin of that namespace who can also create `tackle.konveyor.io` resources (the `Tackle` instance and the `Addon`).
- The cover file described under kind, at most 500 KB because the chart ships it in a ConfigMap.
- Outbound access for build pods to the same hosts the kind playbook fetches from: `registry.access.redhat.com`, `github.com`, `unpkg.com`, PyPI and the TeX distribution's host.
- MTA requires a login by default. Set `admin.password` to the MTA admin's current password; MTA's initial password has to be changed at first login, and the chart's default of `admin` matches only an instance whose password was set to that.

Steps:

1. Install the chart:

   ```sh
   helm install hashicorp-healthcheck . -n openshift-mta --set admin.password=<MTA admin password>
   ```

2. Wait for the setup job and the two builds to complete. The instance takes a few minutes to come up and the readout build about five more:

   ```sh
   oc -n openshift-mta get jobs,builds
   ```

   The setup job starts the builds, waits for the hub, mints the service's API key, seeds the tag categories and imports the questionnaire.

3. Log in to MTA once in a browser, then open the Healthcheck Console address that the install notes print in the same tab.

`helm upgrade` runs the setup job again, which rebuilds the images and updates the questionnaire.

`helm uninstall` removes everything the chart created, including the `Tackle` instance and so every application, assessment and readout in it. The operator stays.

### Values

| Value | Default | Purpose |
|---|---|---|
| `appName` | `mta` | The operator's application name. The hub service is `<appName>-hub` and the UI route is `<appName>`. Upstream Konveyor uses `tackle`. |
| `tackle.spec` | `{}` | Spec of the instance the operator creates. |
| `admin.username`, `admin.password` | `admin`, `admin` | A hub login allowed to create API keys. Used once, to mint the key Healthcheck Console uses. Not used on upstream Konveyor. |
| `host` | the UI route's host | Host of the Healthcheck Console route. |
| `pythonImage` | `registry.access.redhat.com/ubi9/python-312-minimal` | Image for the setup job. |
| `images.console`, `images.readout` | `localhost/healthcheck-console:latest`, `localhost/healthcheck-readout:latest` | The two images on a cluster without OpenShift builds. |

Healthcheck Console has no login of its own and acts on MTA with its API key. Anyone who can reach MTA's host can list respondents and their contact emails, start assessments, generate readouts, download summaries and delete respondents. Expose it only on a trusted network.

## Using the assessment tool

The facilitator works from Healthcheck Console; the respondent answers the questionnaire in Konveyor or MTA. One browser tab carries both, since the console sends the tab on to the questionnaire and the two share a host.

### 1. Start

Open the console: `https://localhost:8443/console/` on kind, or `/console/` on MTA's host in a tab that is logged in to MTA. On the "Start an assessment" tab enter:

- **Organisation**: the respondent's organisation. It names the respondent everywhere afterwards, including on the summary's cover, so write it as it should appear there. Entering an organisation that already exists reopens its assessment.
- **Contact email**: where the summary will be sent after the session.

Press **Start assessment**.

### 2. The questionnaire

The console creates the respondent in the platform and moves the tab to the application's assessment page there. The page lists the questionnaire with a **Retake** button; it reads "Retake" because the console has already created the assessment with the contact as its stakeholder. Press it.

The wizard opens with the stakeholder filled in. Press **Next**, then hand over to the respondent or read the questions out. There are eighteen questions in four steps: Environment, Infrastructure Delivery, Security and Access, and Runtime and Connectivity. Each is single choice and has an explanation under it; a respondent who cannot say picks the "I don't know" answer. **Save as draft** keeps a partly answered assessment to resume later from the same page.

On the last step press **Save and review**. The platform saves the assessment and shows its own review page, which the facilitator can ignore.

### 3. Back to the console

The platform has no link back. Return to the console with the browser's Back button, or by opening `/console/` on the same host again. The respondent now appears on the Maintenance tab with its assessment marked "Completed".

### 4. The readout

On the "Generate a readout" tab choose the organisation and press **Generate readout**. It usually takes under a minute. The tab then reports what was stored: the overall result, each area with a signal and its strength, the number of issues and the patterns, with a link to the respondent's record in the platform and a link to the executive summary, a PDF.

Download the PDF from that link, or later from the Maintenance tab, and send it to the contact. Generating a readout again replaces the previous one.

The facts behind the summary, the Issues and Insights for the follow-up team, and the product tags are on the application in the platform. The `presented` fact lists the areas the summary covers, in order.

## API

The page and any other client use the same API, under `/console/api/`.

Start an assessment:

```sh
curl -X POST "https://<MTA host>/console/api/assessments" \
  -H 'Content-Type: application/json' \
  -d '{"organisation": "Example Ltd", "email": "contact@example.com"}'
```

The response gives the application and assessment ids and the assessment's path in MTA. `questionnaire` is an optional third field, needed only when MTA holds more than one questionnaire besides its built-in one. `GET questionnaires` lists their names.

Generate a readout for an organisation with a completed assessment:

```sh
curl -X POST "https://<MTA host>/console/api/readouts" \
  -H 'Content-Type: application/json' \
  -d '{"organisation": "Example Ltd"}'
curl "https://<MTA host>/console/api/readouts/<task id>"
```

The first call returns the task id. The second gives the task's state and, once it has succeeded, what was stored in MTA. `GET organisations` lists the organisations in MTA.

Download the executive summaries of several respondents as one zip, by application id:

```sh
curl -o summaries.zip "https://<MTA host>/console/api/summaries.zip?applications=<id>,<id>"
```

Download an executive summary, by application id:

```sh
curl -o summary.pdf "https://<MTA host>/console/api/summaries/<application id>"
```

## Maintenance

The "Maintenance" tab lists every respondent with its contact, whether its assessment is complete, when its readout was generated and a link to its summary. A respondent with a summary can be selected, singly or with the select-all box for every respondent matching the filter, and the selected summaries download together as one zip. Each function is also in the API:

| Function | API |
|---|---|
| List respondents | `GET respondents` |
| Download respondents as CSV, with each result and signal | `GET respondents.csv` |
| Generate a readout for every completed assessment, four at a time | `POST readouts` for each organisation |
| Delete one respondent | `DELETE respondents/<application id>` |
| Delete all respondents: every application, stakeholder and readout task | `DELETE respondents` with `{"confirm": "delete all respondents"}` |

Deleting leaves the questionnaire and the tags in place. Neither delete can be undone.

## Tests

None of this is needed to install or run the healthcheck.

```sh
cd hashicorp-healthcheck && python3 -m unittest
```

The tests check the questionnaire's structure against the design, run the reference respondents in `personas.yaml` through the addon's readout logic, and check that `DESIGN.md` matches its generator. They do not need an MTA instance. They need Python 3 with PyYAML (`pip install pyyaml`).

An end-to-end check runs against a live environment. It creates a respondent per persona, and one per red or yellow answer on an all-green baseline, through Healthcheck Console; answers each through the hub; generates the readout; and checks that what lands in the facts, the Issues and Insights, the summary PDF, the respondents list and deletion follows from the answers chosen: every red or yellow answer with its rationale, suggested change and features, under its own area and in presentation order, with each feature's footnote resolving to its documentation page; every unknown question; and no green answer. The summary's text is checked when `pdftotext` (poppler) is installed:

```sh
BASE=https://localhost:8443 python3 kind/e2e.py
```

A browser check drives the console's page in headless Chrome with real clicks: it starts an assessment and lands on the application's assessment page in MTA, filters the respondents and works the delete-all dialog. It needs the `selenium` package and Chrome:

```sh
BASE=https://localhost:8443 python3 kind/smoke.py
```

With `E2E_CLEAR=1` both checks end by deleting every respondent, so set that only on a disposable environment. The GitHub Actions workflow in `.github/workflows/e2e.yml` runs the unit tests, `helm lint` and a register check on the Markdown on every push and pull request, then stands the kind environment up on the runner with `kind/up.yml` and runs the browser check and the end-to-end check with `E2E_CLEAR=1`. It does that once on Podman and once on Docker, then compares what the two produced: each respondent's facts, analysis entries and summary text must be identical.

## Links

* [Konveyor Project](https://www.konveyor.io/)
* [Questionnaire YAML documentation](https://github.com/konveyor/tackle2-hub/blob/main/docs/questionnaire-yaml.md)
