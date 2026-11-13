#!/usr/bin/env python3
"""Scan an unknown repository and inventory its infrastructure-related files.

Usage: python discover.py REPO --out WORKDIR

Writes WORKDIR/discovery.json and prints a human-readable summary.
Standard library only. Secrets inside URIs and key=value pairs are masked.
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

IGNORE_DIRS = {
    ".git", "node_modules", "vendor", "__pycache__", ".venv", "venv", "dist",
    "build", ".next", ".nuxt", ".idea", ".vscode", "target", ".terraform",
    ".tox", ".mypy_cache", ".pytest_cache", "coverage", ".cache", "bower_components",
}
MAX_FILE_BYTES = 512 * 1024
MAX_HITS_PER_FILE_PER_CAT = 8

# Filename-based families: (family, regex on relative path, case-insensitive)
FILE_FAMILIES = [
    ("docker", r"(^|/)(dockerfile[^/]*|docker-compose[^/]*\.ya?ml|compose[^/]*\.ya?ml|\.dockerignore)$"),
    ("kubernetes", r"(^|/)(k8s|kubernetes|manifests|deploy|deployment|charts?|helm)/.*\.ya?ml$|(^|/)(chart|values)\.ya?ml$"),
    ("ansible", r"(^|/)(ansible|playbooks?|roles|inventory|inventories|serverlist|group_vars|host_vars)(/|$)|(^|/)(ansible\.cfg|hosts(\.ini|\.ya?ml)?)$"),
    ("terraform", r"\.(tf|tfvars)$|(^|/)terragrunt\.hcl$"),
    ("cloud-iac", r"(^|/)(cloudformation|template|serverless|sam|bicep|pulumi)[^/]*\.(ya?ml|json|bicep|ts|py)$"),
    ("nginx-proxy", r"(^|/)(nginx[^/]*|haproxy[^/]*|traefik[^/]*|caddyfile|httpd[^/]*|apache[^/]*)(\.conf|\.ya?ml|\.toml)?$|\.conf$"),
    ("systemd-cron", r"\.(service|timer|socket)$|(^|/)(crontab|cron\.d)(/|$)|\.cron$"),
    ("ci-cd", r"(^|/)(\.github/workflows|\.gitlab-ci\.ya?ml|jenkinsfile|azure-pipelines\.ya?ml|\.circleci|bitbucket-pipelines\.ya?ml)"),
    ("env-config", r"(^|/)(\.env[^/]*|[^/]*\.env|config[^/]*\.(ya?ml|json|toml|ini)|settings[^/]*\.py|application[^/]*\.(properties|ya?ml))$"),
    ("db-schema", r"(^|/)(migrations?|alembic|prisma|schema|models?|entities|sql)(/|$)|\.sql$|schema\.prisma$"),
    ("package-manifest", r"(^|/)(package\.json|requirements[^/]*\.txt|pyproject\.toml|pom\.xml|build\.gradle|go\.mod|composer\.json|gemfile|cargo\.toml)$"),
    ("docs", r"(^|/)(readme[^/]*|docs?/.*\.(md|rst))$"),
]

# Content patterns: category -> list of regexes
CONTENT_PATTERNS = {
    "db_uri": [
        r"\b(postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis|rediss|amqps?|kafka|mssql|sqlserver|oracle|clickhouse|cassandra|neo4j|elasticsearch)://[^\s'\"<>]+",
        r"\bjdbc:[a-z0-9]+://[^\s'\"<>]+",
    ],
    "db_hint": [
        r"\b(DATABASE_URL|DB_HOST|DB_NAME|DB_PORT|MONGO(?:DB)?_(?:URI|URL|HOST)|REDIS_(?:URL|HOST)|POSTGRES_(?:HOST|DB)|MYSQL_(?:HOST|DATABASE)|ELASTIC(?:SEARCH)?_(?:URL|HOST))\b",
        r"\bimage:\s*['\"]?(postgres|mysql|mariadb|mongo|redis|rabbitmq|kafka|elasticsearch|opensearch|memcached|minio|clickhouse|influxdb|cassandra)\b",
    ],
    "port": [
        r"^\s*-?\s*['\"]?\d{2,5}:\d{2,5}(/(tcp|udp))?['\"]?\s*$",
        r"\b(EXPOSE)\s+\d+",
        r"\blisten\s+\d+",
        r"\b(containerPort|hostPort|targetPort|nodePort)\s*:\s*\d+",
        r"\b(PORT|[A-Z_]*_PORT)\s*[=:]\s*['\"]?\d{2,5}",
        r"\bfrom_port\s*=\s*\d+|\bto_port\s*=\s*\d+",
    ],
    "volume_disk": [
        r"^\s*volumes:\s*$",
        r"^\s*-\s*['\"]?[./\w${}-]+:/[\w./-]+(:ro|:rw)?['\"]?\s*$",
        r"\b(mountPath|hostPath|persistentVolumeClaim|storageClassName|storage)\s*:",
        r"\b(aws_ebs_volume|aws_efs_file_system|azurerm_managed_disk|google_compute_disk|aws_s3_bucket|azurerm_storage_account|google_storage_bucket)\b",
        r"\b(UPLOAD_DIR|UPLOAD_PATH|MEDIA_ROOT|STORAGE_PATH|DATA_DIR|LOG_DIR|BACKUP_DIR|/var/lib/[\w-]+|/data\b|/mnt/[\w-]+|/srv/[\w-]+)",
        r"\b(boto3|s3\.|BlobServiceClient|GCS|minio)\b",
    ],
    "host_machine": [
        r"^\s*\[[\w:.-]+\]\s*$",
        r"\b(ansible_host|ansible_user|ansible_connection)\s*=",
        r"^\s*(hosts|children):\s*$",
        r"\b(aws_instance|azurerm_(linux|windows)_virtual_machine|google_compute_instance|digitalocean_droplet|hcloud_server|vsphere_virtual_machine)\b",
        r"\bkind:\s*(Deployment|StatefulSet|DaemonSet|CronJob)\b",
        r"\bhostname\s*[:=]",
    ],
    "inbound": [
        r"\b(webhook|callback_url|WEBHOOK_[A-Z_]+)\b",
        r"\b(location\s+[/~^][^\s{]*|proxy_pass\s+[^;]+|upstream\s+\w+)",
        r"\bkind:\s*(Ingress|Service)\b",
        r"\b(sftp|ftp|smtp|imap|pop3)(://|\b.*(server|host|inbox))",
        r"\b(@app\.(route|get|post|put|delete)|@(Get|Post|Put|Delete|Controller)\(|router\.(get|post|put|delete)\(|app\.(get|post|put|delete)\()",
        r"\b(subscribe|consume|basic_consume|KafkaConsumer|@RabbitListener|@KafkaListener|sqs|pubsub)\b",
        r"^\s*([\d*/,-]+\s+){4}[\d*/,-]+\s+\S+",
        r"\bOnCalendar\s*=|\bschedule\s*:\s*['\"]",
    ],
    "external_url": [
        r"https?://(?!localhost|127\.|0\.0\.0\.0|example\.(com|org)|schemas\.|www\.w3\.org|json-schema\.org)[a-zA-Z0-9.-]+\.[a-z]{2,}[^\s'\"<>)]*",
    ],
}

SECRET_URI = re.compile(r"(://[^:/@\s]+:)([^@\s]+)(@)")
SECRET_KV = re.compile(
    r"(?i)((?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|auth)[\w-]*\s*[=:]\s*)(['\"]?)([^\s'\"]+)(['\"]?)"
)


def mask(line: str) -> str:
    line = SECRET_URI.sub(r"\1***\3", line)
    line = SECRET_KV.sub(lambda m: f"{m.group(1)}{m.group(2)}***{m.group(4)}", line)
    return line.strip()[:200]


def is_text(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            chunk = f.read(2048)
        return b"\0" not in chunk
    except OSError:
        return False


def walk(repo: str):
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for name in files:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, repo).replace(os.sep, "/")
            yield rel, full


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-hits", type=int, default=400, help="max hits kept per category")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    if not os.path.isdir(repo):
        sys.exit(f"Not a directory: {repo}")
    os.makedirs(args.out, exist_ok=True)

    compiled_fam = [(f, re.compile(p, re.I)) for f, p in FILE_FAMILIES]
    compiled_pat = {c: [re.compile(p, re.I | re.M) for p in ps] for c, ps in CONTENT_PATTERNS.items()}

    families = defaultdict(list)
    ext_count = defaultdict(int)
    top_dirs = defaultdict(lambda: {"files": 0, "exts": defaultdict(int)})
    hits = defaultdict(list)
    n_files = 0

    for rel, full in walk(repo):
        n_files += 1
        ext = os.path.splitext(rel)[1].lower() or "(none)"
        ext_count[ext] += 1
        top = rel.split("/")[0] if "/" in rel else "(root)"
        top_dirs[top]["files"] += 1
        top_dirs[top]["exts"][ext] += 1

        for fam, rx in compiled_fam:
            if rx.search(rel):
                families[fam].append(rel)

        try:
            size = os.path.getsize(full)
        except OSError:
            continue
        if size > MAX_FILE_BYTES or size == 0 or not is_text(full):
            continue
        try:
            with open(full, encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
        except OSError:
            continue

        for cat, rxs in compiled_pat.items():
            per_file = 0
            seen_lines = set()
            for i, line in enumerate(lines, 1):
                if per_file >= MAX_HITS_PER_FILE_PER_CAT:
                    break
                if len(line) > 600:
                    continue
                for rx in rxs:
                    if rx.search(line) and i not in seen_lines:
                        seen_lines.add(i)
                        per_file += 1
                        if len(hits[cat]) < args.max_hits:
                            hits[cat].append({"file": rel, "line": i, "text": mask(line)})
                        break

    data = {
        "repo": repo,
        "file_count": n_files,
        "top_level": {
            k: {"files": v["files"], "top_exts": sorted(v["exts"].items(), key=lambda x: -x[1])[:4]}
            for k, v in sorted(top_dirs.items())
        },
        "families": {k: sorted(set(v)) for k, v in families.items()},
        "hits": hits,
    }
    with open(os.path.join(args.out, "discovery.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # ---- human summary ----
    print(f"# Discovery: {repo}\n{n_files} files scanned (ignored: {', '.join(sorted(IGNORE_DIRS)[:6])}...)\n")
    print("## Top-level folders")
    for k, v in data["top_level"].items():
        exts = ", ".join(f"{e}:{n}" for e, n in v["top_exts"])
        print(f"- {k}: {v['files']} files ({exts})")
    print("\n## Infra file families found")
    if not families:
        print("- none detected by filename; rely on content hits and README")
    for fam in sorted(families):
        files = sorted(set(families[fam]))
        shown = ", ".join(files[:6]) + (f" ... (+{len(files) - 6})" if len(files) > 6 else "")
        print(f"- {fam} ({len(files)}): {shown}")
    print("\n## Content hits (kept in discovery.json)")
    for cat in CONTENT_PATTERNS:
        files = sorted({h["file"] for h in hits[cat]})
        print(f"- {cat}: {len(hits[cat])} hits in {len(files)} files")
    print(f"\nFull data: {os.path.join(args.out, 'discovery.json')}")


if __name__ == "__main__":
    main()
