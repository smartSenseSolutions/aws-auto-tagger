# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A scheduled AWS Lambda that reads CloudTrail events, detects resource-creation calls (e.g. `RunInstances`, `CreateBucket`), and tags the new resource with `owner` (the CloudTrail username) and `created_at` (the event time). Deployed via the Serverless Framework, triggered on a `rate(24 hours)` schedule.

## Commands

```bash
# Install deps (uv-managed venv, Python >=3.13)
uv sync

# Run locally against real AWS creds (uses AWS_REGION or defaults to us-east-1, hours=25)
export AWS_PROFILE=<your-profile>
python -m src.main

# Run tests
uv run pytest test

# Lint / format (ruff, config is ruff defaults — no [tool.ruff] section in pyproject.toml)
uv run ruff check .
uv run ruff format .

# Run all git hooks (this repo uses `prek`, not the `pre-commit` pip package)
prek run --all-files

# Deploy (requires `npm install -g serverless`)
sls deploy

# Tail deployed Lambda logs
sls logs -f tagger
```

Run a single test: `uv run pytest test/test_sls_lint.py::test_validate_sls_policy`.

## Architecture

Entry point: `src/main.py` (`handler` for Lambda, `main()`/`__main__` for local runs) → `src/tagger.py::CloudTrailTagger.run()`.

Flow, per invocation:
1. `CloudTrailTagger._get_events` pages through `cloudtrail.lookup_events` for the lookback window (`hours`, default 25 — deliberately >24h since the schedule runs every 24h, to close gaps).
2. For each event, `services.get_service_config(event_name)` looks up a matching entry in `SERVICE_CONFIGS` (keyed by eventsource → event name).
3. `_extract_resource_ids` pulls the resource identifier(s) out of the raw `CloudTrailEvent` JSON using the config's `section` (`requestParameters`/`responseElements`) and a JMESPath expression — one event can yield multiple resources (e.g. `RunInstances`).
4. `services.tag_resource` dispatches on `eventsource` via `match/case` to the right boto3 client call, since every AWS service has a different tagging API shape (ARN vs. name vs. ID; list-of-dicts vs. dict; different key names).

### Adding support for a new AWS service/event

This requires touching **three** places that must stay in sync:
1. `src/services.py` — add an entry to `SERVICE_CONFIGS[eventsource][EventName]` with `eventsource`, `resource_type`, `section`, and a `jmespath` expression to extract the resource ID from the CloudTrail event.
2. `src/services.py::tag_resource` — add a `case "<eventsource>":` branch calling the correct boto3 tagging API (ARN construction, tag shape, and client method all vary per service — check existing cases for the pattern that matches, e.g. IAM-list-of-dicts vs. plain dict).
3. `src/clients.py` derives the boto3 client dict directly from `SERVICE_CONFIGS.keys()`, so a new top-level `eventsource` key automatically gets a client — but the corresponding IAM `Action` (`<service>:*Tag*`) must also be added to `serverless.yml`'s `provider.iam.role.statements`.

`test/test_sls_lint.py::test_validate_sls_policy` enforces step 3 — it fails if any `SERVICE_CONFIGS` key has no matching IAM action in `serverless.yml`. Run this test after adding a service.

### Key files

- `src/services.py` — the service registry (`SERVICE_CONFIGS`) and the tagging dispatch (`tag_resource`). This is where nearly all service-specific logic lives.
- `src/tagger.py` — orchestration: fetch events, extract resource IDs, call `tag_resource`, collect stats.
- `src/clients.py` — builds one boto3 client per eventsource in `SERVICE_CONFIGS`, plus `cloudtrail`, `region`, `account_id`.
- `src/data.py` — plain dataclasses (`TaggingStats`, `ResourceInfo`, `EventProcessingResult`, `TaggingConfig`) used as return/config types; no logic.
- `serverless.yml` — Lambda config (schedule, memory/timeout) and the IAM policy that must list a `*Tag*` action per supported service.
- `test/stack/` — a Terraform stack (with its own state) used to spin up real test resources across services; not part of the pytest suite.
