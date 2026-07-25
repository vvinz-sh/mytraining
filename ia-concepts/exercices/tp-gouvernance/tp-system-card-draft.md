# TP — Rédiger une "system card" pour le serveur notes-formation (draft)

Statut : **design posé, pas encore exécuté**. Rattaché à "Gouvernance &
conformité" de la vague 3 (`gouvernance/36-...md`). TP de documentation
pure, sans code — mais qui prend tout son sens après avoir réellement
construit et sécurisé le système documenté.

## Objectif

Documenter le serveur `notes-formation` (TP RAG/MCP + TP sécurité) selon
une structure inspirée des "model cards"/"system cards" utilisées en
pratique (popularisées par Google, Anthropic, OpenAI pour leurs propres
modèles) — synthétiser en un seul document ce qui est aujourd'hui
dispersé dans plusieurs fichiers `.md` du repo.

## Structure proposée du document

### 1. Vue d'ensemble
- Objectif du système (rechercher dans les notes de formation par
  similarité sémantique)
- Utilisateurs prévus (usage personnel, un seul utilisateur)
- Ce que le système fait et ne fait **pas** (ne modifie jamais les
  notes, lecture seule)

### 2. Données utilisées
- Source : fichiers `.md` du repo `mytraining`
- Volume approximatif (nombre de fichiers/chunks à la dernière
  indexation)
- Modèle d'embedding : `all-MiniLM-L6-v2` (sentence-transformers),
  384 dimensions, choix motivé (léger, local, pas de clé API) —
  renvoi vers `exercices/tp-rag-mcp/tp-rag-mcp-notes-resultat.md`
- Métrique de distance utilisée : L2 au carré par défaut (pas
  cosinus, jamais configuré explicitement) — renvoi vers la précision
  ajoutée dans `exercices/tp-securite/tp-securite-rag-mcp-guardrails-resultat.md`

### 3. Guardrails en place
Reprendre le tableau récapitulatif de
`securite/37-panorama-types-guardrails.md`, en précisant lesquels sont
**réellement implémentés** dans ce système (pattern + sémantique) vs
seulement documentés en théorie (classificateur entraîné, contrainte
structurelle, rate limiting — non implémentés ici).

### 4. Limites connues
- Faux positifs/négatifs mesurés lors de la calibration (le tableau des
  3 seuils testés dans le TP sécurité)
- Le seuil `0.97` est calibré empiriquement sur les 5 exemples
  d'injection actuels — pas garanti valable si la base d'exemples
  change
- Pas de logging des détections (mentionné en discussion, jamais codé)
- Réindexation manuelle uniquement, pas de détection automatique de
  drift pour l'instant (le TP CI/CD, une fois fait, comblera ce point)

### 5. Obligations RGPD identifiées
Reprendre la checklist pratique de `gouvernance/36-...md` — statut
actuel pour ce système précis (usage personnel donc risque faible,
mais principe à documenter quand même par exercice)

### 6. Historique des versions
Un tableau simple : date, changement, fichier de résultat associé —
par exemple :

| Date | Changement | Référence |
|---|---|---|
| Session TP RAG/MCP initial | Serveur créé, indexation de base | `tp-rag-mcp-notes-resultat.md` |
| Session TP sécurité | Ajout guardrail pattern + sémantique | `tp-securite-rag-mcp-guardrails-resultat.md` |
| Refonte manuelle | Réindexation complète from scratch | (à dater une fois fait) |

## Ce qu'il faudra vérifier/clarifier en rédigeant

- Est-ce que ce document doit être un fichier statique
  (`SYSTEM_CARD.md`) ou généré partiellement par script (comme le
  nombre de chunks actuel, qui change à chaque réindexation) — un
  document figé devient vite obsolète sur les parties chiffrées
- Où le placer dans le repo — probablement à la racine de
  `exercices/tp-rag-mcp/`, puisque c'est le système documenté

## Compétences pratiquées

- Synthèse de documentation technique dispersée en un seul document de
  référence
- Structuration selon un format reconnu (model card/system card)
- Exercice de recul sur son propre travail (limites, historique)

## Lien avec les notes existantes

Rassemble des éléments de `gouvernance/36-...md`,
`securite/37-...md`, `exercices/tp-rag-mcp/tp-rag-mcp-notes-resultat.md`
et `exercices/tp-securite/tp-securite-rag-mcp-guardrails-resultat.md` —
premier exercice de documentation transversale plutôt que de contenu
nouveau.
