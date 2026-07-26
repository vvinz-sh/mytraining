# TP — Serveur MCP perso pour committer sur `mytraining` (draft)

Statut : **design complet, pas encore exécuté**. TP hors programme, né
d'une discussion sur la modification manuelle de `notes/gouvernance/36-...md`
— pas rattaché à une catégorie vague 3 unique (touche à la fois
écosystème d'outils MCP, automatisation git/CI, et sécurité d'accès).

## Objectif

Un serveur MCP perso permettant à Claude Desktop de faire `git add`,
`git commit`, `git push` sur le dépôt `mytraining` en local (WSL2),
pour fermer la boucle : modifier une note en discussion → la voir
committée sans repasser par Obsidian Git manuellement.

## Étape 0 — Panorama des solutions existantes (fait)

Trois options recensées avant tout code :

1. **Serveur officiel `mcp-server-git`** (`modelcontextprotocol/servers`,
   Python/GitPython, `uvx` ou pip) — douze outils : `git_status`,
   `git_diff_unstaged`, `git_diff_staged`, `git_diff`, `git_commit`,
   `git_add`, `git_reset`, `git_log`, `git_create_branch`,
   `git_checkout`, `git_show`, `git_branch`. Maintenu par le groupe MCP
   officiel. **Ne couvre volontairement pas le push** (choix de
   sécurité probable : n'expose que des opérations locales
   réversibles).
2. **Forks communautaires** (`@cyanheads/git-mcp-server`, etc.) —
   couvrent push/pull/merge/rebase/stash, mais surface bien plus large
   que nécessaire et maintenance individuelle, pas d'un groupe officiel.
3. **Serveur GitHub officiel** (`@modelcontextprotocol/server-github`)
   — passe par l'API GitHub (token PAT) plutôt que git local, pertinent
   pour issues/PR, pas pour ce besoin précis.

**Décision** : serveur officiel `mcp-server-git` pour add/commit/status/
diff/log (déjà audité, couvre le besoin) + un serveur custom minimal
perso limité à un seul outil manquant : le push. Écarte les forks
communautaires au nom du moindre privilège (pas de merge/rebase/stash
inutiles exposés).

## Étape 1 — Conception du serveur custom `git-push-perso`

### Principe : deux fonctions, pas une

- `git_push_preview(repo_path)` — lecture seule, ne peut physiquement
  rien casser même appelée par erreur ou à répétition
- `git_push_confirm(repo_path, token)` — exécute le push réel,
  **uniquement** si le token fourni correspond à l'état réel du dépôt
  recalculé au moment de l'appel

### Le problème de la docstring seule (identifié en discussion)

Une docstring du type *"n'appeler qu'après validation"* est une
indication pour Claude, pas une protection technique — rien
n'empêche techniquement l'appel direct à `git_push_confirm`. La
vraie protection doit venir de la conception du code, pas du
commentaire.

### Mécanisme du token

- Basé sur le **hash des commits à pousser** (`repo.iter_commits("@{u}..")`),
  jamais sur le texte complet du `status --short` (qui inclurait des
  fichiers non suivis sans rapport, faussant la comparaison)
- Calculé par une fonction interne partagée `_commits_a_pousser()`,
  appelée indépendamment par `preview` (pour l'affichage) et par
  `confirm` (pour la vérification) — jamais l'une ne fait confiance au
  résultat mémorisé de l'autre
- `confirm` **recalcule** l'état réel à l'instant T et compare — si
  un commit a été ajouté entre l'aperçu et la confirmation, le token
  ne correspond plus, et le push est refusé avec message explicite

### Limite assumée (pas une faille à corriger)

Si le serveur officiel `mcp-server-git` est connecté en parallèle,
Claude a accès à `git_log` et pourrait en théorie reconstruire le
token sans jamais appeler `git_push_preview`. Le token protège contre
l'appel à l'aveugle ou le push d'un état non vérifié, mais ne remplace
pas une confirmation humaine explicite pour une action aussi sensible
qu'un push — compromis assumé pour ce TP.

### Décisions de conception validées

- Pas de `remote`/`branch` explicites : upstream déduit par défaut
- Pas d'option `--force` : absente du code, pas juste inutilisée
- Flux obligatoire : preview → (validation humaine dans la
  conversation) → confirm

## Étape 2 — Code

```python
# serveur_mcp_git_push.py
from fastmcp import FastMCP
import git  # GitPython — la même lib que le serveur officiel mcp-server-git
import hashlib

mcp = FastMCP("git-push-perso")

def _commits_a_pousser(repo_path: str) -> list[str]:
    """Fonction interne partagée — la SEULE source de vérité sur ce
    qu'il y a à pousser. Appelée par preview ET confirm séparément."""
    repo = git.Repo(repo_path)
    return [c.hexsha for c in repo.iter_commits("@{u}..")]

def _token(hashes: list[str]) -> str:
    """Condense la liste de hash en un seul token comparable."""
    return hashlib.sha256("".join(hashes).encode()).hexdigest()

@mcp.tool()
def git_push_preview(repo_path: str) -> str:
    """Montre ce qui serait poussé, sans rien modifier. Retourne aussi
    un token à fournir tel quel à git_push_confirm."""
    hashes = _commits_a_pousser(repo_path)
    if not hashes:
        return "Rien à pousser : la branche locale est à jour avec le remote."

    repo = git.Repo(repo_path)
    resume = f"{len(hashes)} commit(s) à pousser :\n"
    for h in hashes:
        resume += f"- {h[:7]} : {repo.commit(h).summary}\n"
    resume += f"\nToken à utiliser pour confirmer : {_token(hashes)}"
    return resume

@mcp.tool()
def git_push_confirm(repo_path: str, token: str) -> str:
    """Exécute le push réel — uniquement si le token correspond
    exactement à ce qui serait poussé À CE MOMENT PRÉCIS (recalcul, pas
    de confiance dans une valeur mémorisée)."""
    hashes_actuels = _commits_a_pousser(repo_path)
    if _token(hashes_actuels) != token:
        return ("Refusé : l'état du dépôt a changé depuis l'aperçu "
                "(nouveau commit, ou plus rien à pousser). "
                "Relance git_push_preview.")

    repo = git.Repo(repo_path)
    resultat = repo.remote(name="origin").push()
    return f"Push effectué : {resultat[0].summary if resultat else 'OK'}"

if __name__ == "__main__":
    mcp.run()
```

## Étape 3 — Architecture système retenue

### Deux clones distincts (pas de partage réseau entre les deux)

Cause du choix : Obsidian (Electron) ne peut pas ouvrir un vault via
`\\wsl.localhost\...` — bug documenté, `fs.watch` incompatible avec le
système de fichiers réseau 9P utilisé par ce partage. Contournement
retenu : deux clones séparés plutôt qu'un chemin réseau partagé.

- `/mnt/c/Users/Vinz/Documents/mytraining` (Windows) — Obsidian Git,
  usage humain occasionnel
- `/home/vinz/mytraining` (natif WSL2 Linux) — serveurs MCP, usage
  automatisé/fréquent

⚠️ **Discipline manuelle requise** : `git pull` sur le clone concerné
avant toute session d'écriture, dans un sens comme dans l'autre, pour
éviter une divergence silencieuse. À automatiser plus tard si ça
devient pénible.

### Utilisateur système dédié `mcp-git`

- Membre du groupe `code` (owner `vinz:code` sur le repo natif)
- Lecture seule sur les fichiers du repo, écriture sur `.git`
  uniquement (suffisant : `git add`/`git commit` n'écrivent que dans
  `.git/index` et `.git/objects`, jamais dans les fichiers de travail)
- Extensible plus tard vers du rw groupe si des fonctions plus
  avancées (modification directe de fichiers) sont ajoutées
- Clé SSH dédiée (pas celle de `vinz`), ajoutée comme **deploy key**
  GitHub en lecture/écriture, limitée à ce seul repo

## Étape 4 — Configuration `claude_desktop_config.json`

```json
{
  "mcpServers": {
    "notes-formation": {
      "command": "wsl.exe",
      "args": [
        "-d", "Ubuntu24",
        "/home/vinz/.py3/bin/python3",
        "/mnt/c/Users/Vinz/Documents/mytraining/ia-concepts/exercices/tp-rag-mcp/serveur_mcp_notes.py"
      ]
    },
    "git": {
      "command": "wsl.exe",
      "args": [
        "-d", "Ubuntu24",
        "-u", "mcp-git",
        "/home/vinz/.py3/bin/python3",
        "-m", "mcp_server_git",
        "--repository", "/home/vinz/mytraining"
      ]
    },
    "git-push-perso": {
      "command": "wsl.exe",
      "args": [
        "-d", "Ubuntu24",
        "-u", "mcp-git",
        "/home/vinz/.py3/bin/python3",
        "/home/vinz/mytraining/ia-concepts/exercices/tp-mcp-git-repo/serveur_mcp_git_push.py"
      ]
    }
  }
}
```

## Ce qu'il reste à faire concrètement (checklist)

- [x] Cloner `mytraining` en natif dans `/home/vinz/mytraining`
- [x] Créer le groupe `code` et l'utilisateur `mcp-git`, l'ajouter au
      groupe, poser les permissions (lecture seule + écriture `.git`)
- [x] Générer une clé SSH dédiée pour `mcp-git`
- [x] Ajouter cette clé comme deploy key GitHub (lecture/écriture,
      limitée à ce repo)
- [x] `pip install mcp-server-git --break-system-packages` dans
      `.py3`
- [x] Écrire `serveur_mcp_git_push.py` (code ci-dessus)
- [x] Mettre à jour `claude_desktop_config.json`
- [x] Tester le cas positif (preview → token → confirm → vérifier sur
      GitHub) et le cas négatif (confirm avec un mauvais token, ou
      après un nouveau commit entre-temps → doit être refusé)

## Compétences pratiquées

- Panorama comparatif avant décision de build (plutôt que réflexe
  "je code direct")
- Conception d'un mécanisme anti-contournement réel (token recalculé)
  plutôt qu'une simple convention documentée (docstring)
- Moindre privilège appliqué à trois niveaux : outils exposés (un seul,
  push), permissions fichiers système (lecture seule + `.git`), et
  accès réseau (deploy key limitée à un repo)
- Diagnostic d'une incompatibilité d'architecture (Electron/`fs.watch`
  vs système de fichiers réseau 9P) plutôt qu'un simple contournement
  à l'aveugle

## Lien avec les notes existantes

Prolonge `tp-rag-mcp/` (même socle FastMCP) et
`securite/25-guardrails-prompt-injection-moindre-privilege.md`
(principe de moindre privilège appliqué ici à un outil d'écriture git
plutôt qu'à un guardrail de lecture).
