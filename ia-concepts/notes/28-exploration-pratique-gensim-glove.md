# IA — Exploration pratique gensim/GloVe : arithmétique vectorielle et pièges

Session pratique (hors TP structuré, exploration libre suite à
l'installation de gensim). Confirme en conditions réelles plusieurs
notions vues en théorie.

## Setup

```bash
pip install gensim --break-system-packages
```
```python
import gensim.downloader as api
model = api.load("glove-wiki-gigaword-100")  # 100 dimensions, 128 Mo
```

## Confirmation pratique : roi - homme + femme ≈ reine

```python
model.most_similar(positive=['king', 'woman'], negative=['man'])
```
Résultat obtenu : `queen` en tête avec un score de **0.77** (similarité
cosinus), suivi de tout un voisinage sémantique cohérent (`monarch`,
`throne`, `princess`, `prince`, `elizabeth`, `emperor`...) — confirme en
pratique la théorie vue dans `23-visualisation-embeddings-...md`.

### Précision sur le score 0.77

L'arithmétique vectorielle ne "vise" jamais un mot précis — elle calcule
une **position** dans l'espace, qui tombe rarement exactement sur un mot
existant. Elle atterrit dans un **voisinage**, et `most_similar` renvoie
les mots les plus proches de cette position, classés par score
décroissant. L'espace vectoriel est continu, pas une grille discrète où
chaque position correspond à exactement un mot.

## `doesnt_match` — trouver l'intrus, avec un piège découvert en pratique

```python
model.doesnt_match(['ferrari', 'renault', 'bugati', 'mclaren'])  # faute d'orthographe
# → 'renault'
model.doesnt_match(['ferrari', 'renault', 'bugatti', 'mclaren'])  # bien orthographié
# → 'bugatti'
```

### ⚠️ Piège découvert : mots hors-vocabulaire ignorés silencieusement

Hypothèse de départ fausse : supposer que "bugati" (faute) faisait
partie du vocabulaire simplement parce que la commande n'avait pas levé
d'erreur.

Vérification qui a infirmé l'hypothèse :
```python
'bugati' in model.key_to_index  # False
model.get_vecattr('bugati', 'count')  # KeyError: mot absent
```

**Explication correcte** : `doesnt_match` **ignore silencieusement** les
mots absents du vocabulaire (contrairement à `most_similar` ou
`get_vecattr`, qui lèvent une erreur si le mot n'existe pas). Le premier
appel a donc en réalité calculé l'intrus parmi seulement 3 mots
(`ferrari`, `renault`, `mclaren`), pas 4 — d'où un résultat différent du
second appel qui, lui, a bien pris en compte les 4 marques.

**Leçon méthodologique** : le silence sur les mots hors-vocabulaire peut
fausser un résultat sans que ce soit visible — toujours vérifier la
présence des mots dans le vocabulaire avant de faire confiance à un
résultat de ce type de fonction.

## Fausse piste explorée et infirmée par vérification — fréquence vs contexte

Hypothèse testée : "renault" ressort comme l'intrus (dans le calcul à 3
mots) parce que c'est une marque plus fréquente/généraliste dans le
corpus que les 3 autres (sportives/exclusives).

Vérification :
```python
for marque in ['ferrari', 'renault', 'bugatti', 'mclaren']:
    print(marque, model.get_vecattr(marque, 'count'))
# ferrari 392578 / renault 391755 / bugatti 345818 / mclaren 390369
```

**Résultat : hypothèse infirmée.** Les fréquences brutes sont quasiment
identiques (sauf bugatti, légèrement en dessous) — la fréquence de
mention n'explique pas la position dans l'espace vectoriel.

**Piste plus probable (non vérifiée formellement)** : ce n'est pas le
**volume** de mentions qui compte, mais le **type de contextes** dans
lesquels chaque mot apparaît (écho direct de l'hypothèse
distributionnelle). Renault apparaît probablement aussi dans des
contextes "grand public" (berline, prix, familiale — cohérent avec des
modèles comme Clio/Scénic/Twingo), en plus du contexte sportif partagé
avec Ferrari/Bugatti/McLaren — cette différence de **voisinage
contextuel**, pas le volume, expliquerait l'écart géométrique.

## Leçon méthodologique générale de cette session

Une hypothèse plausible ("plus de mentions = plus généraliste") peut
sembler logique à l'oral, mais se révéler fausse dès qu'on la teste
concrètement — bon exemple pratique du réflexe de vérification
indépendante déjà vu (`11-limites-hallucinations-surconfiance.md`),
appliqué ici à ses propres hypothèses en cours d'exploration, pas
seulement aux réponses d'un LLM.

## Autres commandes utiles explorées/mentionnées

```python
model.similarity('cat', 'dog')       # score de similarité direct entre 2 mots
model.most_similar(positive=['tokyo', 'france'], negative=['japan'])  # → paris
model.most_similar(positive=['smaller', 'big'], negative=['small'])  # → bigger
model.most_similar(positive=['cars', 'dog'], negative=['car'])       # → dogs
```

## Limite découverte : mots polysémiques et embeddings statiques

Test sur "bank" (rivière vs institution financière) :

```python
model.most_similar('bank')
# → banks, banking, credit, investment, financial, securities...
# AUCUN mot lié au sens "rivière" dans le top 10

model.similarity('bank', 'money')  # 0.57
model.similarity('bank', 'river')  # 0.33
```

Le sens "finance" écrase complètement le sens "rivière" dans le vecteur
de "bank".

### Explication : embeddings statiques

GloVe/word2vec attribue **un seul vecteur fixe par mot**, calculé comme
une sorte de moyenne pondérée de tous les contextes rencontrés à
l'entraînement. Le sens "finance" de "bank" étant beaucoup plus fréquent
dans le corpus (Wikipedia, presse) que le sens "rivière", le vecteur
final penche fortement vers la finance — le sens minoritaire est
quasiment noyé, pas représenté à part égale.

C'est ce qu'on appelle des **embeddings statiques** : un vecteur fixe
par mot, peu importe la phrase où il apparaît.

### Différence avec les LLM modernes : embeddings contextuels

Les LLM utilisent l'**attention** (Q/K/V, voir
`20-mecanisme-attention-qkv-multihead.md`) pour donner des embeddings
**contextuels** : le vecteur d'un mot **change dynamiquement** selon les
mots qui l'entourent dans la phrase.

Mécanisme : chaque mot "regarde" les autres mots autour de lui via
l'attention, et sa représentation finale devient une moyenne pondérée
des mots jugés pertinents dans ce contexte précis. Si "bank" est entouré
de "river, water, sat" dans une phrase, et de "account, money, loan"
dans une autre, l'attention **regarde des mots différents** dans les
deux cas → la moyenne pondérée résultante est **différente** → le
vecteur final de "bank" n'est jamais figé, il se recalcule à chaque
phrase selon son contexte.

Résumé de la différence :
| | Embeddings statiques (GloVe/word2vec) | Embeddings contextuels (LLM/attention) |
|---|---|---|
| Vecteur par mot | Un seul, fixe, appris une fois | Recalculé à chaque phrase |
| Polysémie | Mal gérée (sens dominant écrase les autres) | Bien gérée (contexte différencie les sens) |

## Lien avec le TP structuré

Cette session couvre en pratique l'étape 3 du design
(`tp-visualisation-embeddings-draft.md` — "tester l'arithmétique
vectorielle directement"). Reste à faire pour le TP complet : sélection
d'un ensemble de mots à visualiser, réduction de dimensionnalité
(PCA/t-SNE), affichage (matplotlib/plotly).
