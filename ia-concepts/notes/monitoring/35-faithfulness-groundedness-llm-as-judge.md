# IA — Vague 3 (MLOps/Ops) : Faithfulness, groundedness et LLM-as-judge

Suite de `33-monitoring-evaluation-drift-recall.md` — cette note traite
spécifiquement la qualité de la réponse **générée**, par opposition à
la qualité des documents **récupérés** (couverte dans la note 33).

## Faithfulness / groundedness — au-delà du recall@k

Le recall@k s'arrête à l'étape "récupération des documents" — il ne
détecte jamais un problème qui survient **après**, au moment où le LLM
génère sa réponse finale à partir des documents récupérés. Même avec
un recall@3 = 100% (les bons documents sont bien là), le modèle peut
**inventer un détail** absent des documents, ou déformer légèrement ce
qui y était dit — une forme d'hallucination **spécifique au RAG**,
différente de l'hallucination "pure" (inventer sans aucune source).

**Faithfulness (groundedness)** : mesure si chaque affirmation de la
réponse générée peut être retracée jusqu'à une phrase précise des
documents récupérés.

### ⚠️ Pourquoi la similarité vectorielle ne suffit pas à la mesurer

Tentative naturelle : comparer par similarité la réponse générée aux
documents sources. Piège révélé par un exemple concret : "Paris est la
capitale de la France" (document) vs "Lyon est la capitale de la
France" (réponse générée, fausse) — ces deux phrases ont une similarité
vectorielle **élevée** malgré l'erreur factuelle, parce que structure et
sujet sont quasi identiques. Un embedding ne "voit" pas la différence
entre un fait vrai et un fait faux tant que la formulation reste
proche — la similarité seule est un mauvais outil pour détecter la
faithfulness sur ce genre de cas.

## LLM-as-judge

Principe : demander à un **second LLM** (même modèle ou différent) de
lire la réponse générée **et** les documents sources, puis de juger
explicitement si chaque affirmation est bien soutenue par ces documents
— un jugement basé sur la compréhension du sens et de la vérité
factuelle, pas une distance géométrique entre vecteurs.

### Le paradoxe du juge faillible

Le LLM-juge est **aussi** un LLM, avec les mêmes limites détaillées
ailleurs dans le repo (hallucination, sur-confiance,
`fondamentaux/11-...md`) — son jugement lui-même peut être faux, avec
un ton tout aussi confiant qu'une réponse correcte. Aucune garantie
absolue, seulement un signal automatisé.

Même compromis que l'ANN (`rag-embeddings/30-...md` : rapide mais
approximatif, 95-99% jamais 100%) — sauf que l'imprécision vient ici de
la nature même des LLM plutôt que d'un algorithme de recherche.

**Utilité malgré la limite** : permet d'évaluer des milliers de
réponses automatiquement, à une échelle impossible pour une relecture
humaine systématique — un signal statistiquement utile pour repérer des
tendances de dégradation, sans jamais remplacer un audit humain ponctuel
sur les cas les plus critiques.

## Résumé — deux métriques, deux étapes du pipeline

| Métrique | Étape mesurée | Détecte |
|---|---|---|
| Recall@k | Récupération des documents | Les bons documents sont-ils trouvés ? |
| Faithfulness/groundedness | Génération de la réponse | La réponse reste-t-elle fidèle aux documents trouvés ? |

Les deux sont nécessaires et complémentaires — un bon recall@k
n'implique jamais une bonne faithfulness, ce sont deux points de défaillance
indépendants dans le même pipeline.
