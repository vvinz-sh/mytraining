# IA — Le mécanisme d'attention (Query/Key/Value, multi-head)

Prérequis conceptuel identifié après la session multimodalité —
explique comment un transformer relie les mots entre eux, "en même
temps" plutôt que séquentiellement.

## Le problème que l'attention résout

Phrase : "Le chat a mangé sa gamelle parce qu'il avait faim."

Le mot "il" fait référence à "le chat" — mais traité **indépendamment**
(sans regarder les autres mots), aucun moyen de savoir que "il" désigne
"chat" plutôt que "gamelle" (grammaticalement possible aussi à cet
endroit). Il faut un mécanisme qui permette à chaque mot de **regarder
les autres mots** de la phrase et de décider lesquels sont pertinents
pour lui — c'est le rôle de l'**attention**.

## Le principe : Query, Key, Value

Chaque mot génère trois vecteurs différents :
- **Query (Q)** — "qu'est-ce que je cherche ?" (ex : "il" cherche à qui
  il se réfère)
- **Key (K)** — "qu'est-ce que je propose comme information ?" (chaque
  mot a une "étiquette" qui dit ce qu'il représente)
- **Value (V)** — "quelle info je transmets si on me choisit" (le
  contenu réel apporté si jugé pertinent)

Mécanisme : comparer la Query d'un mot (ex : "il") avec la Key de
**chaque autre mot** de la phrase → un score de pertinence par mot →
moyenne pondérée des Value de tous les mots selon ces scores. Résultat :
la représentation finale de "il" est fortement influencée par la Value
de "chat" (score élevé), peu par celle de "gamelle" (score faible).

Analogie : une réunion où chaque participant (mot) "interroge" les
autres pour savoir qui est pertinent pour lui.

## Écho direct avec deux mécanismes déjà vus

**Softmax** : littéralement réutilisé ici — transforme les scores bruts
de comparaison Query/Key en probabilités qui somment à 100%, le même
softmax que pour choisir le prochain token.

**RAG** : écho encore plus large — comparer une question (vecteur) à une
base de documents (vecteurs) par similarité, puis pondérer/récupérer les
plus proches, est **exactement la même logique** que l'attention :

```
RAG (recherche externe)       : Query (question) vs Keys (documents)
                                 → récupère les Values (contenus) les plus proches
Attention (interne au modèle) : Query (un mot) vs Keys (tous les autres mots)
                                 → pondère les Values (contenus) des mots pertinents
```

L'attention est en quelque sorte un "mini-RAG" qui se passe à
l'intérieur même du modèle, à chaque mot, à chaque couche — plutôt
qu'une recherche externe dans une base de documents.

## Multi-head attention — pourquoi plusieurs têtes en parallèle

### Le problème d'une seule tête

Une seule tête d'attention ne capture **qu'un seul type de relation** à
la fois. Dans notre phrase, plusieurs relations coexistent :
- Référence ("il" → "chat")
- Cause ("parce que" relie "avait faim" à "a mangé")
- Grammaire ("a mangé" → sujet "chat")
- Possession ("sa" → "chat", pour une raison différente de "il")

Une seule tête devrait privilégier un seul type de relation par mot, pas
les capturer toutes avec la même vue.

### La solution — plusieurs têtes spécialisées

Le **multi-head attention** fait tourner plusieurs mécanismes
d'attention en parallèle (souvent 8, 16+ selon le modèle), chacun avec
ses propres Q/K/V appris différemment. Une tête peut se spécialiser sur
la référence, une autre sur la causalité, une autre sur la grammaire —
les résultats de toutes les têtes sont combinés à la fin.

Écho direct avec les CNN (couches de neurones) : plusieurs filtres en
parallèle à chaque couche, chacun détectant un motif différent (bords
verticaux, bords horizontaux, texture...) — même principe de
spécialisation parallèle, appliqué à l'attention plutôt qu'aux pixels.

### Pourquoi les têtes doivent être entraînées indépendamment (poids différents dès le départ)

Réutiliser la **même** tête plusieurs fois de suite (mêmes poids Q/K/V)
donnerait **exactement le même résultat** à chaque passage — les mêmes
poids produisent toujours la même sortie pour la même entrée, aucune
raison de spécialisation différente en répétant le même mécanisme.

Pour qu'une tête capture la référence et qu'une autre capture la
causalité, il faut des **poids Q/K/V différents dès le départ**
(initialisation aléatoire différente), puis un ajustement indépendant
pendant l'entraînement (gradient, erreur, correction) — chaque tête
trouve sa propre spécialisation par ce processus normal.

Écho avec la **forêt aléatoire** : chaque arbre voyait un sous-échantillon
différent des données → spécialisations différentes. Ici, chaque tête
n'a pas des données différentes, mais des **poids initiaux différents**
— la diversité de spécialisation vient de la diversité des poids appris,
pas de la répétition d'un même mécanisme. Même principe general (points
de départ différents → spécialisations différentes → résultat combiné
plus riche), mécanisme différent (données vs poids initiaux).

## Récap de la session

- L'attention résout le problème de relier des mots entre eux malgré la
  distance dans la phrase (ex : "il" → "chat").
- Mécanisme Query/Key/Value, avec softmax pour normaliser les scores de
  pertinence — même brique que pour le choix du prochain token, et même
  logique que RAG (recherche par similarité).
- Multi-head attention = plusieurs têtes en parallèle, chacune
  spécialisée sur un type de relation différent, grâce à des poids
  initiaux différents — écho direct avec les filtres multiples des CNN
  et la diversité des arbres d'une forêt aléatoire.
