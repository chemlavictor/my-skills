# Findings schema

Every specialist agent writes one JSON file in `$WORK/findings/<agent>.json`. A shared format lets the synthesizer merge five independent views without guessing.

```json
{
  "agent": "hosts",
  "environments": ["prod", "staging"],
  "items": [
    {
      "id": "prod_web01",
      "kind": "host",
      "name": "web01",
      "environment": "prod",
      "description": "Public web front, runs nginx and the Node app",
      "attributes": {
        "address": "10.0.1.10",
        "aliases": ["web"],
        "ports": ["80", "443"],
        "contains": ["nginx", "web-app container"]
      },
      "evidence": [
        {"file": "ansible/serverlist/prod.ini", "lines": "3-7"},
        {"file": "docker-compose.prod.yml", "lines": "12-30"}
      ],
      "confidence": "high",
      "inferred": false
    }
  ],
  "edges": [
    {
      "from": "prod_web01",
      "to": "prod_api01",
      "label": "REST",
      "protocol": "http",
      "port": "8080",
      "evidence": [{"file": "nginx/web.conf", "lines": "21"}]
    }
  ],
  "unknowns": [
    {"question": "Where is the staging DB hosted?", "look_at": "api/config/staging.yml"}
  ]
}
```

## Rules
- `id`: lowercase ASCII with underscores, unique across the file, prefixed by environment when there is more than one. Mermaid node ids are derived from it.
- `kind` values by agent:
  - repo-mapper: `folder`, `environment`
  - hosts: `host`, `service`
  - storage: `volume`, `bucket`, `path`, `backup`
  - databases: `db_internal`, `db_external`, `cache`, `broker`, `search`
  - inbound: `inbound`, `external_actor`
- `evidence` is required and each entry needs a path relative to the repo root. Lines are optional but valuable.
- `confidence`: `high` (explicitly defined), `medium` (implied by code), `low` (referenced only).
- `inferred: true` when no file states it directly.
- Mask secrets as `***` in every field.
- `unknowns` always include `look_at`, the file the reader should open next.
