# Konveyor HashiCorp Surveys

## HashiCorp Snapshot

A 14-question Konveyor questionnaire for a booth or introductory session. A technical practitioner answers it in about five minutes. No knowledge of HashiCorp products is needed.

It indicates whether a deeper discovery session is warranted, and in which of five capability areas it should start: infrastructure lifecycle, machine identity and secrets, human access, service networking and workload lifecycle.

It is not an architecture assessment or a lead score. Its results are signals for a follow-up. The readout names the product associated with each area as the starting point for that follow-up.

Validated against Migration Toolkit for Applications (MTA) 8.3.0. The design is in [hashicorp-snapshot/DESIGN.md](hashicorp-snapshot/DESIGN.md).

## Components

- `hashicorp-snapshot/`: the questionnaire, its tests and its design.
- `survey-bootstrap/`: a small Python service served on MTA's own host at `/bootstrap/`. Its page starts an assessment from an organisation and a contact email, and generates readouts. Sharing MTA's host keeps a logged-in browser tab logged in when the page sends it on to the questionnaire.
- `snapshot-readout/`: an MTA addon. It derives the readout from a completed assessment and writes it to the application as Issues, Insights, facts and product tags. Running it again replaces its previous output.

## Install

Prerequisites:

- `oc`, logged in with rights to create builds, deployments, routes, network policies and addons in the `openshift-mta` project.
- An MTA API key with administrator rights, and MTA's URL:

  ```sh
  export MTA_ENDPOINT=https://mta.example.com
  export MTA_ADMIN_TOKEN=...
  ```

- Python 3 with PyYAML (`pip install pyyaml`) for `seed_tags.py` and the tests.

Steps:

1. Seed the tag categories. This comes before the import: see [design section 3](hashicorp-snapshot/DESIGN.md#3-mta-behaviour-the-design-depends-on). The script creates only what is missing.

   ```sh
   python3 hashicorp-snapshot/seed_tags.py
   ```

   If MTA's certificate is issued by a private CA, point `SSL_CERT_FILE` at the CA bundle.

2. Import the questionnaire, through the questionnaire import in the MTA administration view or with:

   ```sh
   curl -X POST "$MTA_ENDPOINT/hub/questionnaires" \
     -H "Authorization: Bearer $MTA_ADMIN_TOKEN" \
     -H "Content-Type: application/x-yaml" \
     --data-binary @hashicorp-snapshot/questionnaire.yaml
   ```

3. Deploy Survey Bootstrap, giving its route MTA's host name, and build its image on the cluster:

   ```sh
   oc -n openshift-mta create secret generic survey-bootstrap --from-literal=api-key="$MTA_ADMIN_TOKEN"
   oc kustomize survey-bootstrap/ | sed "s/mta.example.com/<MTA host>/" | oc apply -f -
   oc -n openshift-mta start-build survey-bootstrap --from-dir=survey-bootstrap/ --follow
   ```

   The Deployment rolls out each new build. `MTA_HUB` is the hub's in-cluster address. `MTA_API_KEY` is read from the `survey-bootstrap` secret.

4. Register the readout addon and build its image:

   ```sh
   oc apply -k snapshot-readout/
   oc -n openshift-mta start-build snapshot-readout --from-dir=snapshot-readout/ --follow
   ```

Survey Bootstrap has no login of its own and acts on MTA with the API key. Anyone who can reach MTA's host can list organisation names, start assessments, generate readouts and read their summaries. Expose it only on a trusted network.

## Run an assessment

1. In a browser tab that is logged in to MTA, open `/bootstrap/` on MTA's host.
2. On "Start an assessment", enter the organisation and a contact email. The service creates the stakeholder, the application (named for the organisation) and the assessment, and opens the questionnaire. An organisation that already exists reopens its assessment.
3. Complete the questionnaire.
4. On "Generate a readout", choose the organisation. The tab reports what was stored: the verdict, each indicated product with its strength, the number of issues and the patterns.
5. Read the result in MTA on the application: its risk, its Issues and Insights, the facts on its Reports tab and its product tags. The `presented` fact lists the areas to present, in order.

## API

The page and any other client use the same API, under `/bootstrap/api/`.

Start an assessment:

```sh
curl -X POST "$MTA_ENDPOINT/bootstrap/api/assessments" \
  -H 'Content-Type: application/json' \
  -d '{"organisation": "Example Ltd", "email": "contact@example.com"}'
```

The response gives the application and assessment ids and the assessment's path in MTA. `questionnaire` is an optional third field, needed only when MTA holds more than one questionnaire besides its built-in one. `GET questionnaires` lists their names.

Generate a readout for an organisation with a completed assessment:

```sh
curl -X POST "$MTA_ENDPOINT/bootstrap/api/readouts" \
  -H 'Content-Type: application/json' \
  -d '{"organisation": "Example Ltd"}'
curl "$MTA_ENDPOINT/bootstrap/api/readouts/<task id>"
```

The first call returns the task id. The second gives the task's state and, once it has succeeded, what was stored in MTA. `GET organisations` lists the organisations in MTA.

## Tests

```sh
cd hashicorp-snapshot && python3 -m unittest
```

The tests check the questionnaire's structure against the design and run the reference respondents in `personas.yaml` through the addon's readout logic. They do not need an MTA instance.

## Links

* [Konveyor Project](https://www.konveyor.io/)
* [Questionnaire YAML documentation](https://github.com/konveyor/tackle2-hub/blob/main/docs/questionnaire-yaml.md)
