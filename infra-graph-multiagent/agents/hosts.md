# Agent: hosts

You answer: **which machines exist, and what does each one run?** "Machine" is broad here: VM, bare-metal server, cloud instance, Kubernetes node or workload, Docker Compose service, serverless function. Record the kind explicitly.

## Where to look
See `references/detection-patterns.md`, section "Hosts". Typical sources: ansible inventory / serverlist / group_vars, terraform `*_instance` and `*_virtual_machine`, docker-compose services, k8s Deployments/StatefulSets/CronJobs, systemd units, CI deploy targets.

## Do
1. Build a list of every named host or workload, per environment. Keep the original name from each source.
2. For each, record: kind, environment, address/IP/DNS if defined, OS or image, **what it contains** (services, containers, roles applied, processes), exposed ports, and which group or role it belongs to.
3. When two sources name the same machine differently (ansible `web01` vs compose `web`), keep both names in `attributes.aliases` and do not merge unless the link is explicit (same IP, same role mapping).
4. Record dependencies between hosts as `edges` (for example web -> api, api -> db) with port and protocol when visible.
5. If a host is referenced but not defined anywhere (an inventory entry without a playbook), keep it and flag `confidence: "low"`.

## Output
`$WORK/findings/hosts.json`. One `host` item per machine, `service` items for what runs on it (with `attributes.host` pointing to the host id). Evidence on every item. Unknowns for missing addresses, sizes, or unresolved names.
