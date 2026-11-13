#!/usr/bin/env python3
"""Lint INFRASTRUCTURE.md: Mermaid syntax pitfalls + referenced file paths exist.

Usage: python validate_output.py doc.md --repo REPO

Exit code 0 = clean, 1 = problems found. Standard library only.
This is a heuristic linter, not a full Mermaid parser; it catches the mistakes
that most often break rendering.
"""
import argparse
import os
import re
import sys

FENCE = re.compile(r"```mermaid\s*\n(.*?)```", re.S)
BACKTICK = re.compile(r"`([^`\n]+)`")
PATH_LIKE = re.compile(r"^[\w.@~/-]+(/[\w.@~-]+)+(:\d+(-\d+)?)?/?$|^[\w.-]+\.(ya?ml|json|tf|conf|ini|py|js|ts|sql|toml|env|sh|md|cfg|properties|xml|service|timer)(:\d+(-\d+)?)?$")
SECRET = re.compile(r"(?i)://[^:/@\s*]+:(?!\*\*\*)[^@\s]{3,}@|(password|secret|token|api[_-]?key)\s*[=:]\s*['\"]?(?!\*\*\*)[A-Za-z0-9/+_-]{8,}")
RESERVED = {"end", "graph", "subgraph", "flowchart", "class", "style", "click", "default"}


def lint_block(code: str, idx: int):
    errs = []
    lines = code.splitlines()
    first = next((l.strip() for l in lines if l.strip() and not l.strip().startswith("%%")), "")
    if not re.match(r"^(flowchart|graph|erDiagram|sequenceDiagram|classDiagram|stateDiagram(-v2)?|C4Context)\b", first):
        errs.append(f"diagram {idx}: first line should declare a diagram type, got '{first[:40]}'")
    opens = sum(1 for l in lines if re.match(r"^\s*subgraph\b", l))
    closes = sum(1 for l in lines if re.match(r"^\s*end\s*$", l))
    if opens != closes:
        errs.append(f"diagram {idx}: {opens} 'subgraph' but {closes} 'end'")
    if code.count('"') % 2:
        errs.append(f"diagram {idx}: odd number of double quotes")
    for n, l in enumerate(lines, 1):
        s = l.strip()
        if s.startswith("%%"):
            continue
        # unquoted label with parentheses/brackets inside e.g. A[foo (bar)]
        m = re.search(r'\b\w+\[(?!\(|"|\[|/|\\)([^\]"]*[()][^\]"]*)\]', s)
        if m:
            errs.append(f"diagram {idx} line {n}: label with parentheses must be quoted: ...[\"...\"]")
        m = re.match(r"^(\w+)\s*[\[({>]", s)
        if m and m.group(1).lower() in RESERVED and m.group(1).lower() not in {"graph", "subgraph", "flowchart", "class", "style", "click"}:
            errs.append(f"diagram {idx} line {n}: node id '{m.group(1)}' is reserved")
        if re.search(r"-->\s*\|[^|]*\|\s*-->", s):
            errs.append(f"diagram {idx} line {n}: malformed edge label")
        if re.search(r"\\n", s):
            errs.append(f"diagram {idx} line {n}: use <br/> instead of \\n")
    n_nodes = len(set(re.findall(r"^\s*(\w+)\s*[\[({>]", code, re.M)))
    if n_nodes > 35:
        errs.append(f"diagram {idx}: {n_nodes} nodes, split it (aim for <= 25)")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doc")
    ap.add_argument("--repo", required=True)
    a = ap.parse_args()

    text = open(a.doc, encoding="utf-8").read()
    problems = []

    blocks = FENCE.findall(text)
    if not blocks:
        problems.append("no ```mermaid blocks found")
    for i, b in enumerate(blocks, 1):
        problems += lint_block(b, i)

    # file paths referenced in prose/tables (outside mermaid blocks)
    prose = FENCE.sub("", text)
    missing = set()
    checked = set()
    for m in BACKTICK.finditer(prose):
        token = m.group(1).strip()
        if not PATH_LIKE.match(token) or token.startswith(("http", "/var/", "/etc/", "/mnt/", "/data", "/srv/", "/opt/", "/usr/", "/home/", "/tmp/")):
            continue
        path = re.sub(r":\d+(-\d+)?$", "", token).rstrip("/")
        if path in checked:
            continue
        checked.add(path)
        if "*" in path:
            continue
        if not os.path.exists(os.path.join(a.repo, path)):
            missing.add(path)
    for p in sorted(missing):
        problems.append(f"referenced path not found in repo: {p}")

    for n, l in enumerate(text.splitlines(), 1):
        if SECRET.search(l):
            problems.append(f"line {n}: possible unmasked secret")

    for sec in ("Zones d'ombre", "Unknowns", "Open questions"):
        if sec.lower() in text.lower():
            break
    else:
        problems.append("missing 'Zones d'ombre' (unknowns) section")

    print(f"{len(blocks)} mermaid diagram(s), {len(checked)} distinct file path(s) checked")
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print(f"- {p}")
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
