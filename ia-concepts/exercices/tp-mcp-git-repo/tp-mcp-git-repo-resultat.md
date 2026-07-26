# TP — Serveur MCP perso `git-push-perso` : réalisé avec succès ✅

Complète `tp-mcp-git-repo-draft.md`. Le TP a été mené de bout en bout,
avec un vrai bug rencontré et corrigé en cours de route, et les deux
scénarios de validation prévus (cas positif et cas négatif) testés en
conditions réelles.

## Bug rencontré et corrigé

### Blocage silencieux au premier push — prompt SSH interactif sans terminal

Premier appel à `git_push_confirm` : aucune erreur, aucun log
d'exception côté serveur MCP, mais l'appel ne se terminait jamais —
obligé d'interrompre manuellement l'action.

**Diagnostic** : `git_commit` (opération purement locale) fonctionnait
sans problème ; seul `git_push_confirm` (première opération réseau
avec ce nouvel utilisateur `mcp-git`) bloquait. La première connexion
SSH vers un hôte jamais contacté déclenche une question interactive
(confirmation de la clé d'hôte). Le process étant lancé par
`wsl.exe` depuis Claude Desktop — sans terminal interactif pour y
répondre — la question restait posée indéfiniment, sans remonter
d'erreur exploitable dans les logs MCP.

**Correction** : accepter la clé d'hôte GitHub manuellement, une fois,
en dehors du flux MCP :

```bash
sudo -u mcp-git ssh -T git@github.com
```

Après ça, le push a fonctionné immédiatement avec le même token déjà
généré (aucun nouveau commit entre-temps, donc le token restait
valide).

**Leçon retenue** : un outil MCP qui ne remonte "aucune erreur" n'est
pas forcément bloqué dans son propre code — ça peut être une attente
interactive invisible en amont (ici, SSH), qu'aucune quantité de debug
côté script Python n'aurait révélée sans regarder le contexte
d'exécution (absence de terminal).

## Résultat des tests

### Cas positif

1. `git_push_preview` sur un commit réel (`a386252`) → 1 commit détecté,
   token généré
2. `git_push_confirm` avec ce token → push effectué (`9f3029d..a386252`)
3. Vérifié directement sur GitHub (contenu du fichier récupéré via
   `raw.githubusercontent.com`) : présent et à jour

### Cas négatif

1. Commit `4d5b265` créé → `git_push_preview` → token A généré (basé
   sur ce seul commit)
2. Un **deuxième** commit ajouté avant confirmation (volontairement,
   pour simuler un état qui a changé entre l'aperçu et l'action)
3. `git_push_confirm` avec le token A (périmé) → **refusé** :
   `"l'état du dépôt a changé depuis l'aperçu"`
4. Vérifié via `git_status` : les 2 commits restaient uniquement en
   local, rien poussé par erreur

Le mécanisme de token (hash des commits à pousser, recalculé à chaque
appel plutôt que mémorisé) a fonctionné exactement comme conçu : il
bloque un push sur un état différent de celui vérifié, sans jamais
tenter la moindre opération réseau dans ce cas.

## Ce que ce TP a démontré concrètement

- **Le token comme protection réelle, pas déclarative** : contrairement
  à une docstring ("n'appeler qu'après validation"), le token empêche
  *techniquement* un push sur un état non vérifié — la différence entre
  une convention et un mécanisme, déjà pressentie en conception, validée
  ici en conditions réelles avec un vrai commit surnuméraire.
- **Un blocage silencieux n'est pas toujours un bug applicatif** : la
  cause ici était complètement en dehors du code Python (SSH,
  contexte d'exécution non interactif) — un rappel que le diagnostic
  doit remonter au-delà de la seule couche qu'on vient d'écrire.
- **Panorama avant code, à nouveau rentable** : s'appuyer sur le
  serveur officiel `mcp-server-git` pour add/commit/status a évité de
  réécrire 12 outils déjà audités — seul le point réellement manquant
  (push) a nécessité du code custom.

## Compétences pratiquées

- Conception d'un mécanisme anti-contournement basé sur un hash
  recalculé, pas une valeur mémorisée
- Diagnostic d'un blocage sans log d'erreur (raisonnement par
  élimination : local vs réseau, première exécution vs exécutions
  suivantes)
- Authentification SSH dédiée à un utilisateur système à moindre
  privilège (`mcp-git`), séparée de l'utilisateur principal
- Test délibéré d'un cas négatif (pas seulement le cas qui marche) —
  même méthodologie que le TP sécurité
