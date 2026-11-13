# Agent: inbound

You answer: **what enters this system from other doors?** Anything that brings data or requests in from outside a component's own boundary: public HTTP ports, reverse-proxy routes, ingress rules, API routes, webhooks received from third parties, message queue consumers, file drops (SFTP, shared folders, email inboxes), scheduled jobs that pull data, partner pushes, CI/CD deploy access, admin SSH.

## Where to look
`references/detection-patterns.md`, section "Inbound". nginx/haproxy/traefik configs, firewall and security-group rules, k8s Ingress/Service, compose `ports:`, route decorators and controllers, webhook handlers, consumer code, cron/systemd timers, ansible firewall tasks.

## Do
1. For each entry point record: type (http, https, tcp, ssh, sftp, smtp, queue, webhook, cron-pull, file-drop), port, path or topic, who or what sends (internet, partner name, internal service, user), which component receives, authentication if visible (none / basic / token / mTLS / IP allowlist), and the file that defines it.
2. Mark exposure: `public`, `private-network`, `localhost-only`.
3. For outbound pulls that import data (cron downloading from a partner API) record them too, with `direction: "pull"`.
4. Flag entry points without visible auth or restriction under `unknowns` or `confidence: "low"`; do not assert they are unprotected, because protection may live outside the repo.

## Output
`$WORK/findings/inbound.json`, `kind: "inbound"` items plus `edges` from the source (create `external_actor` items for internet, partners) to the receiving component.
