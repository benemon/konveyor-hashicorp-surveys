# Konveyor HashiCorp Surveys

## The 5 Minute HashiCorp Healthcheck

An 18-question Konveyor questionnaire for a booth or introductory session. A technical practitioner answers it in around five minutes. No knowledge of HashiCorp products is needed.

It indicates whether a deeper discovery session is warranted, and in which of six capability areas it should start: infrastructure lifecycle, image lifecycle, machine identity and secrets, human access, service networking and workload lifecycle.

It is not an architecture assessment or a lead score. Its results are signals for a follow-up. The readout names the product associated with each area as the starting point for that follow-up.

Validated against Migration Toolkit for Applications (MTA) 8.3.0. The design is in [hashicorp-healthcheck/DESIGN.md](hashicorp-healthcheck/DESIGN.md).

## Components

- `hashicorp-healthcheck/`: the questionnaire, its tests and its design.
- `healthcheck-console/`: a small Python service served on MTA's own host at `/console/`. Its page starts an assessment from an organisation and a contact email, generates readouts, serves each respondent's executive summary and has a maintenance tab. Sharing MTA's host keeps a logged-in browser tab logged in when the page sends it on to the questionnaire.
- `healthcheck-readout/`: an MTA addon. It derives the readout from a completed assessment and writes it to the application as Issues, Insights, facts, product tags and an executive summary in PDF. Running it again replaces its previous output.

## Install on OpenShift

The repository root is a Helm chart. It takes a namespace that holds only the MTA or Konveyor operator to a working environment: the instance, the questionnaire and its tags, Healthcheck Console on the UI's host and the readout addon.

Prerequisites:

- An OpenShift cluster with the MTA or Konveyor operator installed in the target namespace, and no instance in it.
- `oc` and `helm`, logged in with rights to create the resources in `templates/` in that namespace.

Steps:

1. Install the chart:

   ```sh
   helm install hashicorp-healthcheck . -n openshift-mta
   ```

2. Wait for the setup job and the two builds to complete:

   ```sh
   oc -n openshift-mta get jobs,builds
   ```

   The setup job waits for the hub, starts the builds, mints the service's API key, seeds the tag categories and imports the questionnaire.

3. Open the Healthcheck Console address that the install notes print.

`helm upgrade` runs the setup job again, which rebuilds the images and updates the questionnaire.

| Value | Default | Purpose |
|---|---|---|
| `appName` | `mta` | The operator's application name. The hub service is `<appName>-hub` and the UI route is `<appName>`. Upstream Konveyor uses `tackle`. |
| `tackle.spec` | `{}` | Spec of the instance the operator creates. |
| `admin.username`, `admin.password` | `admin`, `admin` | A hub login allowed to create API keys. Used once, to mint the key Healthcheck Console uses. |
| `host` | the UI route's host | Host of the Healthcheck Console route. |
| `pythonImage` | `registry.access.redhat.com/ubi9/python-312-minimal` | Image for the setup job. |
| `images.console`, `images.readout` | `localhost/healthcheck-console:latest`, `localhost/healthcheck-readout:latest` | The two images on a cluster without OpenShift builds. |

Healthcheck Console has no login of its own and acts on MTA with its API key. Anyone who can reach MTA's host can list respondents and their contact emails, start assessments, generate readouts, download summaries and delete respondents. Expose it only on a trusted network.

The summary's title page uses `healthcheck-readout/cover.pdf` as its background. The file is not tracked. Put an A4 cover of at most 500 KB there before installing the chart or running the playbook. Without it the title page is plain.

## Run locally on kind

Two Ansible playbooks stand the whole environment up on a laptop, with upstream Konveyor, and remove it again. Once it is up it needs no network connection.

Prerequisites: `podman` with a machine of at least 6 GB of memory, `kind`, `helm`, `git` and `ansible` with the collections in `kind/requirements.yml`.

```sh
ansible-galaxy collection install -r kind/requirements.yml
ansible-playbook kind/up.yml
```

The playbook creates a kind cluster, installs an ingress controller and the Konveyor operator, builds the two images from their Containerfiles and loads them into the cluster, installs this chart and waits until Healthcheck Console can reach Konveyor. It ends by listing each address with the ingress and service behind it, and the in-cluster service names. On a cluster without OpenShift builds the chart uses those images and an Ingress in place of the builds and the Route.

- Konveyor: `https://localhost:8443/`
- Healthcheck Console: `https://localhost:8443/console/`
- Kubeconfig: `kind/kubeconfig`

Upstream Konveyor does not require a login by default.

To serve a trusted certificate, put a certificate for `localhost` with its chain in `kind/tls.crt` and its key in `kind/tls.key` before running the playbook. Neither file is tracked. Without them the ingress controller serves its self-signed certificate.

After a restart of the laptop, start the podman machine and then the cluster's container:

```sh
podman machine start
podman start healthcheck-control-plane
```

To remove the cluster, its kubeconfig and the two local images:

```sh
ansible-playbook kind/down.yml
```

## Run an assessment

1. In a browser tab that is logged in to MTA, open `/console/` on MTA's host. Upstream Konveyor on kind needs no login.
2. On "Start an assessment", enter the organisation and a contact email. The service creates the stakeholder, the application (named for the organisation) and the assessment, and opens the questionnaire. An organisation that already exists reopens its assessment.
3. Complete the questionnaire.
4. On "Generate a readout", choose the organisation. The tab reports what was stored: the verdict, each indicated product with its strength, the number of issues and the patterns. It links to the executive summary, a PDF to send to the respondent.
5. Read the result in MTA on the application: its risk, its Issues and Insights, the facts on its Reports tab and its product tags. The `presented` fact lists the areas to present, in order.

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

Download an executive summary, by application id:

```sh
curl -o summary.pdf "https://<MTA host>/console/api/summaries/<application id>"
```

## Maintenance

The "Maintenance" tab lists every respondent with its contact, whether its assessment is complete, when its readout was generated and a link to its summary. Each function is also in the API:

| Function | API |
|---|---|
| List respondents | `GET respondents` |
| Download respondents as CSV, with each result and signal | `GET respondents.csv` |
| Generate a readout for every completed assessment, four at a time | `POST readouts` for each organisation |
| Delete one respondent | `DELETE respondents/<application id>` |
| Delete all respondents: every application, stakeholder and readout task | `DELETE respondents` with `{"confirm": "delete all respondents"}` |

Deleting leaves the questionnaire and the tags in place. Neither delete can be undone.

## Tests

```sh
cd hashicorp-healthcheck && python3 -m unittest
```

The tests check the questionnaire's structure against the design and run the reference respondents in `personas.yaml` through the addon's readout logic. They do not need an MTA instance. They need Python 3 with PyYAML (`pip install pyyaml`).

## Links

* [Konveyor Project](https://www.konveyor.io/)
* [Questionnaire YAML documentation](https://github.com/konveyor/tackle2-hub/blob/main/docs/questionnaire-yaml.md)
