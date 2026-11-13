# Agent: reviewer

You did not write the document, so you can judge it without attachment. Your job is to find claims that the repo does not support.

## Do
1. Run `scripts/validate_output.py` and fix every reported problem (broken Mermaid, missing paths, possible secrets).
2. Pick **at least five** claims, preferring the surprising ones (an external DB, a public port, a host that holds many services). Open the cited file and confirm the claim at that line. If it does not hold, correct it or move it to "Zones d'ombre".
3. Check coverage: compare `discovery.json` families and hits against the document. Any infra file family or DB URI that appears in discovery but not in the document needs either an entry or an explanation.
4. Check the four questions are answered: machines + contents, disk storage, internal vs external DBs, inbound flows. An empty section must say why (for example "no backup found in repo").
5. Re-run the validator until it prints `OK`.

Report in two lines what you corrected. Do not rewrite sections that are fine.
