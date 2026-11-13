# Output template for INFRASTRUCTURE.md

Use this structure and order. Write headings in the user's language (French shown). Graph first, then table, in every section: the graph gives the shape, the table gives the proof.

````markdown
# Infrastructure de <nom du projet>

> Généré le <date> à partir du dépôt `<chemin>`. Chaque élément cite le fichier qui le prouve.

## 1. Le dépôt en un coup d'oeil
Two or three sentences: what the project does, stack, how it is deployed, environments found.

| Dossier | Rôle | Stack | Fichiers clés |
|---|---|---|---|
| `api/` | API métier | Node/Express | `api/package.json`, `api/src/server.js` |

## 2. Vue d'ensemble
One Mermaid flowchart, left to right, five zones: Internet and partners, Machines, Storage, Internal data, External services. Inbound arrows come from the left, outbound calls go to the right.

## 3. Machines et contenu
One diagram per environment (subgraph per machine, services inside). Then:

| Machine | Env | Type | Adresse | Contient | Ports | Source |
|---|---|---|---|---|---|---|

## 4. Stockage disque
Diagram: machine/service -> volume or bucket, with cylinders or folders.

| Emplacement | Type | Monté par | Contient | Rétention / backup | Source |
|---|---|---|---|---|---|

State clearly if no backup was found.

## 5. Bases de données internes
Diagram: services -> DBs, DBs -> their volumes.

| Base | Moteur | Hébergée sur | Schémas / tables principales | Clients | Source |
|---|---|---|---|---|---|

Optionally one `erDiagram` per DB when models are readable, max ~10 entities.

## 6. Bases et services externes
Diagram with dashed borders for everything outside the infra.

| Service | Type | Endpoint (masqué) | Utilisé par | Direction | Source |
|---|---|---|---|---|---|

## 7. Flux entrants (les autres portes)
Diagram: external actors -> entry points -> receiving components.

| Porte | Type | Port / chemin | Qui envoie | Reçu par | Exposition | Auth visible | Source |
|---|---|---|---|---|---|---|---|

## 8. Traçabilité
Index "où chercher quoi": for each theme (hôtes, volumes, BDD, ports, secrets/config, CI/CD), the list of key files in the repo.

## 9. Zones d'ombre
Numbered list. Each item: what is unknown or inferred, why, and the file to open to settle it.
````

## Notes
- Skip a section only if the whole topic is absent, and replace it with one line saying so.
- Sections 3 to 7 reuse the same node ids so the reader can follow an entity from one diagram to the next.
- The overview (section 2) must remain readable on its own: no more than about 25 nodes.
