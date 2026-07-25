# IA — Vague 3 (MLOps/Ops) : Monitoring & évaluation — drift, golden dataset, recall@k

Première session théorique de la vague 3, partie de l'exemple concret
du TP RAG/MCP déjà réalisé.

## Pourquoi "ça marchait au test" ne garantit rien dans le temps

Un système RAG testé une fois avec succès peut se dégrader
silencieusement dans le temps, sans qu'aucun code ne change — la
dégradation ne produit ni erreur ni crash, juste des résultats de moins
en moins pertinents.

## Les causes de drift identifiées

### 1. Documentation obsolète (data drift le plus simple)

La base de contenu évolue (nouvelles notes ajoutées, anciennes
modifiées) sans que la base vectorielle ne soit réindexée — le
contenu réel diverge de ce qui est indexé.

### 2. Vocabulaire qui évolue (concept drift)

Le modèle d'embedding est figé après son entraînement (rappel :
inférence = poids figés, aucun ajustement possible sans réentraînement
complet, voir `hardware/13-...md`). Si le vocabulaire/jargon des
questions posées évolue (nouveaux termes techniques, nouvelles
formulations), le modèle reste sur ce qu'il connaissait à
l'entraînement — dégradation progressive et silencieuse de la
pertinence pour ce nouveau vocabulaire.

### 3. Mise à jour silencieuse d'un modèle managé (API)

Propre aux embeddings via API (ex : Voyage AI) plutôt qu'en local
(`sentence-transformers`) : le fournisseur peut mettre à jour son
modèle en coulisses, sans prévenir, sans changer le nom du endpoint.
Si une partie de la base est indexée avant la mise à jour et une autre
après, les vecteurs deviennent **incompatibles entre eux** dans la même
base — comparer un vecteur "v1" à un vecteur "v2" du même modèle n'a
plus de sens, même avec la même dimension.

Argument en faveur d'un modèle d'embedding local (comme choisi dans le
TP RAG/MCP) : contrôle total de la version, rien ne bouge sans décision
explicite.

### 4. Incohérence de stratégie de chunking dans le temps

Si la stratégie de chunking change (ex : passage du découpage par mots
fixes au chunking sémantique vu dans `rag-embeddings/31-...md`) et que
seules les nouvelles notes sont réindexées avec la nouvelle stratégie,
les anciens et nouveaux chunks ont une granularité sémantique
différente — fausse la comparaison par similarité, même avec un modèle
d'embedding strictement identique.

## Comment détecter le drift — deux approches, pas équivalentes

### Upvote/downvote utilisateur — signal utile mais bruité

Même limites que pour le RLHF (`fondamentaux/17-...md`) : biais de
sélection (seuls certains utilisateurs votent), manque d'expertise pour
juger le fond. Pour le monitoring de drift spécifiquement, un vote
négatif peut avoir mille causes sans rapport avec le drift (question
mal posée, sujet absent de la base) — signal agrégé utile pour repérer
des tendances, pas un indicateur propre de dégradation.

### Golden dataset + recall@k — la vraie bonne pratique

**Golden dataset (eval set)** : un petit ensemble fixe de questions
avec leurs bonnes réponses/documents attendus, rejoué automatiquement à
intervalle régulier (chaque semaine, ou à chaque déploiement).

**Recall@k** : métrique standard d'évaluation RAG. Pour une question,
on définit à l'avance les documents pertinents attendus ; on regarde
parmi les k résultats retournés combien de ces documents attendus sont
effectivement présents. Exemple : 2 documents attendus retrouvés sur 3
→ recall@3 = 67%.

Suivre cette métrique dans le temps permet de détecter une dégradation
progressive (ex : recall@3 qui passe de 90% à 70% sur plusieurs mois)
avant qu'un utilisateur ne s'en plaigne.

## Ordre de remédiation — du moins coûteux au plus coûteux

Face à un recall qui baisse, l'ordre logique de vérification/action :

1. **Réindexation** — la base est-elle à jour avec le contenu réel ?
   (quasi gratuit à vérifier et corriger — cause la plus fréquente)
2. **Changement de modèle d'embedding** — passer à un modèle plus
   récent/performant sans réentraîner, juste réindexer avec le nouveau
   modèle (coût modéré)
3. **Fine-tuning du modèle d'embedding** — l'ajuster spécifiquement au
   vocabulaire du domaine (coût plus élevé, mais pas from scratch)
4. **Réentraînement complet** — quasiment jamais nécessaire pour ce
   type de problème, réservé à des cas extrêmes ; disproportionné vu le
   coût d'entraînement déjà détaillé (`hardware/13-...md`)

Piège à éviter : sauter directement à la solution 4 ("il faut
réentraîner le modèle") sans avoir vérifié la solution 1 (souvent la
vraie cause).

## Suite de cette note

La mesure de la qualité de la réponse **générée** (par opposition aux
documents récupérés) est traitée séparément dans
`monitoring/35-faithfulness-groundedness-llm-as-judge.md`.

## À approfondir dans une prochaine session (pistes identifiées, non couvertes ici)

- **Observabilité / tracing** (LangSmith ou équivalent) — ce que
  contient concrètement une trace, comment suivre une requête à travers
  tout le pipeline RAG pour déboguer un cas précis.
- **Latence et alerting** — pas seulement "est-ce pertinent" mais "est-ce
  assez rapide", avec des seuils déclenchant une alerte automatique.
