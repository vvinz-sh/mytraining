# TP — RAG sur LLM local : Pokémon (resserré) → notes de formation (général) (draft)

Statut : **design posé, pas encore exécuté**. Prolonge `tp-llm-local/`
(inférence Ollama, Phase 1) et `tp-rag-mcp/` (stack RAG déjà
fonctionnelle). Née d'une observation ludique : `qwen3:8b` invente des
noms Pokémon en français et boucle dessus (note 42, mode 4).

## Objectif

Vérifier si donner à un LLM local un contexte RAG contenant la vraie
liste des 151 Pokémon corrige l'hallucination observée en vanilla —
puis étendre le principe à un cas plus général et utile (les notes de
formation elles-mêmes) pour observer le comportement RAG sur du
contenu réel, pas juste un cas de test isolé.

## Phase 1 — Pokémon, injection de prompt simple (sans MCP)

### Étape 0 — Panorama rapide (avant de coder)

Vérifier s'il existe une liste Pokémon fr/en fiable et réutilisable
(éviter de la retaper à la main) — API publique type PokéAPI, ou
fichier CSV/JSON déjà existant en open data.

### Étape 1 — Baseline sans RAG (déjà en partie faite)

Reprendre le test ludique de la session précédente comme référence
"avant" : demander à `qwen3:8b` (vanilla, sans contexte injecté) la
liste des 151 Pokémon en français, noter le point exact où
l'hallucination/la boucle démarre.

### Étape 2 — Injection de prompt simple

Pas de Chroma, pas d'embeddings, pas de recherche sémantique — juste
coller la liste complète des 151 Pokémon (fr) directement dans le
prompt système ou en préambule du message utilisateur, puis reposer la
même question. Objectif : voir si un contexte simplement **présent**
dans la fenêtre (sans recherche) suffit à corriger le problème.

**Point de vigilance à anticiper** (déjà rencontré ce soir) : la
liste complète tient-elle dans `num_ctx` sans troncature ? Vérifier
le nombre de tokens avant de lancer, pas après un échec silencieux.

### Étape 3 — Comparaison

- Le modèle cite-t-il maintenant les bons noms ?
- Boucle-t-il encore au-delà d'un certain point, malgré le contexte
  fourni (le mécanisme de dégénérescence par répétition est-il un
  problème de *connaissance* ou un problème de *génération*, distinct
  et potentiellement non résolu par le RAG) ?
- Le modèle **invente-t-il des types Pokémon plausibles** pour des
  noms qu'il ne trouve pas dans le contexte fourni (test de la
  discipline "je m'en tiens au contexte" vs "je comble par prior"),
  ou reconnaît-il correctement ses limites ?

## Phase 2 — Généralisation aux notes de formation, via MCP

### Étape 1 — Réutiliser la stack existante

Adapter `serveur_mcp_notes.py` (déjà fonctionnel) pour qu'Ollama (pas
Claude Desktop) puisse l'appeler. Nécessite un pont — Ollama supporte
le tool calling nativement pour Llama 3.1/Qwen3, mais pas le protocole
MCP directement (point déjà identifié en Phase 1 debrief, jamais
implémenté). Panorama à refaire ici : existe-t-il un pont
communautaire MCP↔Ollama tool-calling prêt à l'emploi, ou faut-il
écrire un petit traducteur maison ?

### Étape 2 — Test sur une vraie question de formation

Poser une question dont la réponse existe précisément dans une note
(ex : "quel seuil a été retenu pour le guardrail sémantique et
pourquoi ?" — réponse dans la note sécurité, seuil 0.97). Vérifier si
le LLM local, via RAG, retrouve la bonne info plutôt que d'halluciner
une réponse plausible mais fausse.

### Étape 3 — Cas piège volontaire

Poser une question dont la réponse **n'existe pas** dans les notes
(inventée). Vérifier si le modèle admet l'absence d'info, ou comble le
vide par un prior plausible — test direct du biais de prior déjà
documenté en note 42 (mode 5), cette fois avec du RAG actif plutôt que
sur un contexte brut.

## Ce qu'il faudra vérifier/clarifier en cours de route

- Le point de bascule contexte-fourni vs `num_ctx` dépassé, si la base
  de notes grossit au-delà de ce qui tient en une fois
- Différence de comportement entre injection brute (Phase 1) et vraie
  recherche sémantique/RAG (Phase 2) — le contexte "juste présent" et
  le contexte "activement récupéré" ne sollicitent pas le modèle de
  la même façon

## Compétences pratiquées

- Distinction entre "corriger un manque de connaissance" (ce que le
  RAG peut faire) et "corriger un comportement de génération" (boucle,
  ce que le RAG ne peut probablement pas faire seul)
- Pont MCP ↔ tool-calling Ollama, jamais implémenté jusqu'ici
  (identifié comme piste en Phase 1, resté en réserve)
- Test volontaire de robustesse face à l'absence d'info (cas piège),
  pas seulement le cas qui marche

## Lien avec les notes existantes

Note 42 (modes d'échec — sycophancie, dégénérescence, biais de prior),
`tp-rag-mcp/` (stack RAG de référence), `tp-llm-local/` (inférence
Ollama, comportement de troncature/contexte déjà documenté).
