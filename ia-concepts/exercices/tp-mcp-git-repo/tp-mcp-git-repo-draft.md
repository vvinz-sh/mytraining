# TP — Serveur MCP perso pour committer sur `mytraining` (draft)

Statut : **design posé, pas encore exécuté**. TP hors programme, né
d'une discussion sur la modification manuelle de `notes/gouvernance/36-...md`
— pas rattaché à une catégorie vague 3 unique (touche à la fois
écosystème d'outils MCP, automatisation git/CI, et sécurité d'accès).

## Objectif

Un serveur MCP perso permettant à Claude Desktop de faire `git add`,
`git commit`, `git push` sur le dépôt `mytraining` en local (WSL2),
pour fermer la boucle : modifier une note en discussion → la voir
committée sans repasser par Obsidian Git manuellement.

## Étape 0 — Panorama des solutions existantes (avant d'écrire quoi que ce soit)

Ne pas réinventer la roue : recenser d'abord ce qui existe.

- Serveur MCP **git** officiel/communautaire (écosystème
  `modelcontextprotocol/servers`) — vérifier s'il couvre déjà
  add/commit/push ou seulement lecture (log, diff, status)
- Serveur MCP **filesystem** générique — souvent en lecture/écriture
  fichier mais sans notion de commit git
- Comparer sur : scope des opérations couvertes, granularité des
  permissions (whitelist de chemins ?), maintenance active,
  configuration nécessaire (`claude_desktop_config.json`)

Critère de décision : si un serveur existant couvre add/commit/push
avec un contrôle d'accès suffisant → l'utiliser tel quel. Sinon →
justifier pourquoi un serveur custom en FastMCP (comme pour
`tp-rag-mcp/`) est nécessaire, et sur quel point précis l'existant est
insuffisant.

## Étape 1 — Scope et permissions

- Racine unique autorisée : le repo `mytraining` (pas le reste du
  système de fichiers WSL)
- Confirmer si `push` doit être automatique après commit, ou nécessiter
  une validation explicite dans la conversation avant chaque push
  (repasse par le principe de moindre privilège vu dans le TP sécurité)

## Étape 2 — Implémentation (si aucun serveur existant ne convient)

- Outils exposés : `git_status`, `git_diff`, `git_add`, `git_commit`,
  `git_push` — un outil par opération plutôt qu'un outil générique
  `run_git_command` (surface d'attaque plus large si le serveur exécute
  n'importe quelle commande git passée en argument)
- Réutiliser la structure FastMCP du TP RAG/MCP comme base

## Étape 3 — Test

- Cas positif : modifier une note (ex : ajout du point Article 5 sur
  `36-...md`), demander le commit via Claude Desktop, vérifier
  l'apparition sur GitHub
- Cas limite à tester : tentative de commit hors du dossier `mytraining`
  — doit être bloquée

## Ce qu'il faudra vérifier/clarifier en codant

- Faut-il un `.gitignore` ou une whitelist explicite pour éviter de
  committer des fichiers indésirables (config locale, cache Python) ?
- Gestion des credentials git (SSH agent WSL2 déjà configuré ou à
  vérifier) pour que le `push` fonctionne sans intervention manuelle

## Compétences pratiquées

- Panorama comparatif avant décision de build (plutôt que réflexe
  "je code direct")
- Conception d'un serveur MCP avec surface d'accès restreinte
  (moindre privilège appliqué à un outil d'écriture, pas juste de
  lecture comme le RAG)
- Fermeture de boucle conversation → action sur le repo réel

## Lien avec les notes existantes

Prolonge `tp-rag-mcp/` (même socle FastMCP) et
`securite/25-guardrails-prompt-injection-moindre-privilege.md`
(principe de moindre privilège appliqué ici à un outil d'écriture git
plutôt qu'à un guardrail de lecture).
