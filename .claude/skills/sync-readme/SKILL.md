---
name: sync-readme
description: Sync README.md with the code — mainly the "Supported AWS Services" list and the service names in the intro, plus the "Tags applied" section. Use after adding/removing a service in src/services.py SERVICE_CONFIGS, changing tag names in src/data.py TaggingConfig, or when asked to sync/refresh the README.
---

# sync-readme

`src/services.py::SERVICE_CONFIGS` is the source of truth. Make `README.md` match it. Edit only the README.

## 1. Dump what the code supports

```bash
uv run python -c "
from src.services import SERVICE_CONFIGS as S
for k, ev in S.items():
    print(k, '->', ', '.join(f\"{e} ({c['resource_type']})\" for e, c in ev.items()))
"
```

Also read `TaggingConfig` in `src/data.py` for the tag names and `tag_resource` in `src/services.py` for which tags are applied.

## 2. Update README.md

1. **Supported AWS Services** (bullets grouped by category, e.g. Compute, Storage/Database, Streaming, Networking, Security, Monitoring, Development, Analytics, Mobile):
   - Every `SERVICE_CONFIGS` key must appear, under the best-fitting category, using the human name (`elbv2` → ELB, `kafka` → Kafka (MSK), `cognito-idp`/`cognito-identity` → Cognito, `cloudwatch` → CloudWatch Logs/Alarms by its resource types, `ec2` also covers VPC/NAT Gateway/EBS etc. only if worth naming).
   - Remove services that are in the README but not in `SERVICE_CONFIGS`.
   - Keep existing category order and wording; add a new category only if nothing fits.
2. **Intro bullet** ("Supports AWS services (EC2, S3, ...)"): keep it a short sample list; make sure every name in it is actually supported.
3. **Tags applied** section: table must list exactly the tags `tag_resource` writes, with the key names from `TaggingConfig`; keep the `owner_email` resolution order in sync with `CloudTrailTagger._owner_email` in `src/tagger.py`.
4. Architecture image `docs/architecture.svg` (hand-written SVG, edit the `<text>` directly) and table of contents: keep the tag label (`owner, created_at, owner_email`), the service count in "N services: ..." (= number of `SERVICE_CONFIGS` keys) and anchors consistent with the above.

## 3. Report

Reply with a short diff summary: services added, services removed, other lines changed. If nothing drifted, say the README is already in sync. Never `git commit`.
