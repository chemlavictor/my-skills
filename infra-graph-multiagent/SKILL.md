---
name: infra-graph-multiagent
description: Explore an unknown repository with a multi-agent workflow and produce an infrastructure document in Markdown with Mermaid graphs - machines/hosts and what each one runs, disk storage, internal databases, external databases/services, and every inbound entry point (ports, webhooks, queues, SFTP, cron, third-party pushes) - each fact tied to the file that proves it. Use this skill whenever the user wants to map, document, audit or understand the infrastructure of a repo, asks "what does my repo contain / where are the servers / where is the data stored / what talks to what", wants an architecture or infra diagram, or mentions docker-compose, ansible, terraform, kubernetes, serverlist, nginx, databases or storage in a codebase they do not know well. Also trigger on French requests such as "graph d'infra", "schéma d'infrastructure", "cartographie du repo", "où sont stockées les données", "documenter l'infra", "multiagent", even if the user never says "skill" or "mermaid".
---

# Infra Graph (multi-agent)

Turn an unfamiliar repository into one Markdown document (`INFRASTRUCTURE.md`) that answers four questions, with Mermaid graphs and a source file next to every claim:

1. **Which machines exist and what does each one run?**
2. **Where does data live on disk?** (volumes, mounts, upload folders, logs, backups)
3. **Which databases are used?** Internal (owned by this infra) vs. external (managed or third-party).
4. **What enters the system from other doors?** (HTTP ports, webhooks, queues, file drops, cron, partner pushes)

The user often does not know what the repo looks like, so the first deliverable is a map of the repo itself. Never assume a stack; discover it.

Write the final document in the language the user wrote in (French by default if they wrote French). Keep identifiers, file paths and Mermaid node ids in ASCII.

## Why this is multi-agent

Infra facts are scattered across unrelated file types (compose, ansible, terraform, nginx, CI, env files, ORM code). One pass tends to anchor on the first stack it sees and miss the rest. Splitting the work by *question* gives each agent a narrow lens, and a separate reviewer catches unsupported claims. The agents work in parallel and write structured findings; only the synthesizer writes the final Markdown.

## Workflow

Set `WORK=/home/claude/infra-work` (or any scratch dir) and `REPO=<repo path>`. If the user has not given a path, look in `/mnt/user-data/uploads`, unzip archives if needed, and use the project root (the folder containing `.git`, or the top folder of the upload).

### Phase 0 - Discovery (you, deterministic)

```bash
python /path/to/skill/scripts/discover.py "$REPO" --out "$WORK"
```

It writes `$WORK/discovery.json` and prints a short summary: tree overview, which infra file families exist (docker, k8s, ansible, terraform, nginx, CI, env, ORM...), and grep hits for ports, DB URIs, volumes and external URLs. Secrets in URIs are masked. Read the printed summary, then decide which agents are worth launching. Skip an agent only if discovery shows nothing relevant to its question, and say so in the final "zones d'ombre" section.

If the repo has several environments (prod/staging/dev, several inventories, several compose files), note them now; every agent must keep environments separate.

### Phase 1 - Parallel specialists

Launch these agents **in the same turn** when subagents are available. Each reads its prompt file from `agents/`, receives `REPO`, `WORK` and the discovery summary, and writes `$WORK/findings/<name>.json` following the schema in `references/findings-schema.md`.

| Agent | Prompt | Answers |
|---|---|---|
| `repo-mapper` | `agents/repo-mapper.md` | What is in each top-level folder (web, api, pkg, ansible, ...)? |
| `hosts` | `agents/hosts.md` | Machines/hosts/nodes and the services or containers on each |
| `storage` | `agents/storage.md` | Disk volumes, mounts, upload/log/backup paths, object storage |
| `databases` | `agents/databases.md` | Internal DBs and external DBs/caches/brokers, schemas, who connects |
| `inbound` | `agents/inbound.md` | Every way data or requests enter: ports, ingress, webhooks, queues, cron, file drops |

If no subagent tool exists (plain chat), run the same five roles yourself **one after the other**, writing each findings file before starting the next. Do not blend them: the narrow focus is what makes the result reliable.

### Phase 2 - Synthesis (one agent)

Read `agents/synthesizer.md`. It merges all findings, resolves name conflicts (the same machine called `web01` in ansible and `web` in compose), drops duplicates, and builds the graphs and tables following `references/output-template.md`. Mermaid rules are in `references/mermaid-rules.md`; follow them, because one bad character breaks the whole diagram.

### Phase 3 - Review (separate agent)

Read `agents/reviewer.md`. The reviewer did not write the document, so it can check it fairly:

```bash
python /path/to/skill/scripts/validate_output.py "$WORK/INFRASTRUCTURE.md" --repo "$REPO"
```

The script lints Mermaid blocks and checks that every backticked file path exists in the repo. The reviewer then spot-checks at least five claims against the real files (open the file, confirm the line), removes or downgrades anything unsupported, and moves doubtful items to "Zones d'ombre". Fix and re-run until the script passes.

### Phase 4 - Deliver

Save the result as `/mnt/user-data/outputs/INFRASTRUCTURE.md` and present it. In the chat reply, give a three-to-five line summary (number of machines, databases, entry points, biggest unknowns) and nothing more; the document is the deliverable.

## Non-negotiable rules

- **Evidence or it did not happen.** Every machine, volume, DB and entry point cites at least one `path/to/file` (add `:line` when known). If something is inferred (for example a DB implied by an ORM but no host is defined), mark it `inferred` and say why.
- **Never print secrets.** Passwords, tokens, keys and full connection strings with credentials are masked as `***`. Host, port and DB name are fine to show; usernames only when they are clearly not sensitive.
- **Do not invent.** Missing hostnames, IPs or sizes stay as "not defined in repo". A short honest "unknown" beats a plausible guess, because readers will trust the diagram.
- **Separate environments.** Never merge prod and staging into one box; one graph per environment when they differ.
- **External means outside this infra.** Managed cloud DBs, SaaS APIs, partner SFTP, third-party webhooks go in the external zone with a dashed style, so the reader sees the trust boundary at a glance.
- **Keep diagrams readable.** At most about 25 nodes per diagram; split by environment or by layer instead of drawing one giant graph.

## Files in this skill

- `scripts/discover.py` - repo scan and masked grep hits (Phase 0)
- `scripts/validate_output.py` - Mermaid lint and path existence check (Phase 3)
- `agents/*.md` - one prompt per agent
- `references/findings-schema.md` - JSON format agents write
- `references/detection-patterns.md` - what to look for per technology
- `references/output-template.md` - exact structure of `INFRASTRUCTURE.md`
- `references/mermaid-rules.md` - syntax rules and styling conventions
