# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A scheduled AWS Lambda that reads CloudTrail events, detects resource-creation calls (e.g. `RunInstances`, `CreateBucket`), and tags the new resource with `owner` (the CloudTrail username), `created_at` (the event time) and `owner_email` (resolved from the caller's `userIdentity`: IAM users via their name or `EMAIL_ID` tag, IAM Identity Center/SSO users via their Identity Store profile when `IDENTITY_STORE_ID` is set, otherwise `Unknown`; see `CloudTrailTagger._owner_email`). Deployed via the Serverless Framework, triggered on a `rate(24 hours)` schedule. An optional second Lambda (`src/reminder.py`, weekly) DMs each owner on Slack the resources they created that are older than N days; it is a no-op unless `SLACK_TOKEN_PARAM` is set.

## Commands

```bash
# Install deps (uv-managed venv, Python >=3.13)
uv sync

# Run locally against real AWS creds (uses AWS_REGION or defaults to us-east-1, hours=25)
export AWS_PROFILE=<your-profile>
export IDENTITY_STORE_ID=d-xxxxxxxxxx   # optional: SSO owner_email lookup
python -m src.main

# Slack cleanup reminders: dry run (prints messages), add --send to really send
uv run python -m src.reminder

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
1. `src/services.py` — add an entry to `SERVICE_CONFIGS[eventsource][EventName]` with `eventsource`, `resource_type`, `section`, and a `jmespath` expression to extract the resource ID from the CloudTrail event. The key must be the boto3 client name; events are matched on name **and** CloudTrail `EventSource` (names like `CreateCluster` repeat across services), so if the key differs from the `EventSource` prefix (`<prefix>.amazonaws.com`), add it to `CLOUDTRAIL_SOURCES`.
2. `src/services.py::tag_resource` — add a `case "<eventsource>":` branch calling the correct boto3 tagging API (ARN construction, tag shape, and client method all vary per service — check existing cases for the pattern that matches, e.g. IAM-list-of-dicts vs. plain dict).
3. `src/clients.py` derives the boto3 client dict directly from `SERVICE_CONFIGS.keys()`, so a new top-level `eventsource` key automatically gets a client — but the corresponding IAM `Action` (`<service>:*Tag*`) must also be added to `serverless.yml`'s `provider.iam.role.statements`.

`test/test_sls_lint.py::test_validate_sls_policy` enforces step 3 — it fails if any `SERVICE_CONFIGS` key has no matching IAM action in `serverless.yml`. `test/test_services.py` runs every configured event through `tag_resource` with real boto3 clients (calls stop after botocore validates the params, no AWS access), catching a missing `case`, a wrong client/method name or bad params, and checks each event resolves via its `EventSource`. Run `uv run pytest test` after adding a service.

### README sync

After any code change under `src/` (new/removed service, tag names, tagging behavior), run the `sync-readme` skill (`.claude/skills/sync-readme`) before finishing, so `README.md` stays in step.

### Conventions

- Generic reusable helpers (e.g. `is_email`) go in `src/utils.py`, not inline in `tagger.py`/`services.py`. Check there before writing a new one.
- Optional features stay off until configured (e.g. Slack reminders need `SLACK_TOKEN_PARAM`), and all env vars of one feature share a prefix (`SLACK_*`).
- Reminder delivery goes through the `src/notifier.py::Notifier` ABC (`send_to_owner`, `send_fallback`); `src/slack.py::Slack` is the implementation and `LogNotifier` is the dry run. A new channel (email, Teams) is a new `Notifier`, `Reminder` stays unchanged.
- Environment variables are read only through `src/data.py::Settings` (no `os.getenv` elsewhere). Add new env config as a field there, and pass it to the Lambda via `serverless.yml` `functions.tagger.environment`.

### Key files

- `src/services.py` — the service registry (`SERVICE_CONFIGS`) and the tagging dispatch (`tag_resource`). This is where nearly all service-specific logic lives.
- `src/tagger.py` — orchestration: fetch events, extract resource IDs, call `tag_resource`, collect stats.
- `src/clients.py` — builds one boto3 client per eventsource in `SERVICE_CONFIGS`, plus `cloudtrail`, `region`, `account_id`.
- `src/reminder.py` — optional weekly cleanup reminders: `Reminder` finds resources with an old `created_at` via the Resource Groups Tagging API, groups them by `owner_email`, sends via a `Notifier`; `handler` is the `reminder` Lambda.
- `src/notifier.py` / `src/slack.py` — `Notifier` ABC + `LogNotifier` (dry run); `Slack` notifier (stdlib urllib, bot token from SSM SecureString `SLACK_TOKEN_PARAM`).
- `src/utils.py` — shared helpers (logger setup, `is_email`, `env_field`, `arn_type_and_name`, and any other small reusable function). Home for anything not specific to one service or to orchestration.
- `src/data.py` — plain dataclasses (`Settings` for env vars, `TaggingStats`, `ResourceInfo`, `EventProcessingResult`, `TaggingConfig`) used as config/return types; no logic.
- `serverless.yml` — Lambda config (schedule, memory/timeout, env vars) and the IAM policy that must list a `*Tag*` action per supported service (plus `identitystore:GetUserId`/`DescribeUser` for SSO).
- `docs/architecture.svg` — hand-written SVG architecture diagram shown in the README; kept in sync by the `sync-readme` skill.
- `test/stack/` — a Terraform stack (with its own state) used to spin up real test resources across services; not part of the pytest suite.
