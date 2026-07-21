# IA — Réseaux de neurones : intuition des couches

## Structure de base

- **Couche d'entrée** : reçoit les données brutes (ex : valeur de chaque
  pixel d'une photo).
- **Couche(s) cachée(s)** : le vrai "travail" de transformation.
- **Couche de sortie** : résultat final (ex : "chat" / "pas chat").

Chaque neurone d'une couche est connecté à tous les neurones de la couche
suivante, et **chaque connexion a un poids** (un des "potentiomètres" vus
dans la note ML). Un neurone : prend les valeurs reçues, les multiplie
chacune par le poids de sa connexion, additionne, puis applique une
**fonction d'activation** qui décide si le signal "passe" vers la couche
suivante (à approfondir dans une prochaine session).

Analogie retenue : un pipeline de traitement de logs (parsing → filtrage
→ enrichissement → agrégation) — chaque étape transforme la sortie de la
précédente. Différence clé : dans un réseau de neurones, chaque couche
applique une transformation **apprise** (via les poids), pas une logique
écrite à la main.

## Pourquoi plusieurs couches cachées : abstraction croissante

Point à ne pas confondre : ce n'est **pas** un système de vote ou de score
cumulé couche par couche ("presque toutes les couches disent chat =
presque un chat" est **faux**). Chaque couche construit un niveau
d'**abstraction plus élevé** à partir des concepts plus simples de la
couche précédente ; seule la toute dernière couche prend la décision
finale.

Exemple pour une photo de chat :
1. Couche proche de l'entrée : motifs très simples (bords, contrastes,
   lignes).
2. Couche suivante : combine les bords en formes (contour d'oreille,
   courbe d'un œil).
3. Couche suivante : combine les formes en parties reconnaissables
   ("oreille de chat", "moustache").
4. Couche de sortie : combine les parties pour la décision finale.

## Ce qu'apporte concrètement une couche intermédiaire

Le vrai bénéfice n'est pas "moins de bruit" mais **réduire la complexité
de la transformation que la couche suivante doit apprendre**.

Sans couche intermédiaire, une couche devrait apprendre en un seul bond
une fonction bien plus complexe (ex : pixels bruts → "ceci est une
oreille" directement) — plus difficile à apprendre, demandant plus de
poids et de données, moins fiable. Avec la couche intermédiaire qui a déjà
simplifié le problème, la couche suivante n'a plus qu'un problème
nettement plus simple à résoudre.

### Exercice de renforcement — pipeline Ansible santé serveur

Décider si un serveur est "sain"/"à risque" à partir de données brutes
(CPU, RAM, logs d'erreurs, uptime).

- **Option A (une seule étape monolithique)** : doit apprendre/coder en
  même temps trois types de travail mélangés — calculer des indicateurs
  bruts pertinents (moyenne CPU, taux d'erreurs), **et** pondérer/combiner
  le tout pour la décision — sans étape intermédiaire pour valider chaque
  calcul avant de passer au suivant. Plus de sources d'erreur, plus
  difficile à apprendre/déboguer correctement.
- **Option B (étapes séparées)** : étape 1 calcule des indicateurs simples
  → étape 2 combine en scores composites (stabilité, performance) → étape
  3 combine ces scores déjà propres pour la décision finale. Chaque étape
  ne résout **qu'un seul type de problème**, et transmet un résultat déjà
  nettoyé à la suivante.

Parallèle direct avec les couches de neurones : chaque couche/étape
résout un problème plus simple et isolé, plutôt qu'une seule étape ne
doive tout résoudre (calcul brut + agrégation + décision) d'un coup.

## Reconsolidation — analogie pipe Unix (après une session de clarification)

Repris plus tard suite à une confusion sur le concept de couches.

### Base très simple

Une couche prend **plusieurs nombres en entrée** et ressort **plusieurs
nombres en sortie** (potentiellement un nombre différent de valeurs). Par
exemple `[5, 2, 8]` → `[12, 3]`. Empiler deux couches = la sortie de la
première devient l'entrée de la seconde.

### Analogie avec un pipe Unix (`commande1 | commande2`)

La sortie de `commande1` devient l'entrée de `commande2`, sans que
`commande2` ait besoin de savoir comment `commande1` a produit ce
résultat — juste ce qu'elle reçoit en entrée. Bonne analogie pour la
structure séquentielle des couches.

Nuance à corriger dans l'analogie : dans un pipe Unix, chaque commande
fait un travail **différent et défini à l'avance par un humain** (`grep`,
puis `sort`, puis `uniq`...). Dans un réseau de neurones, chaque couche
fait le **même type d'opération générale** (une transformation de
nombres), mais avec des réglages internes (poids) qui ne sont pas écrits
à la main — ils sont **appris** pendant l'entraînement. Le "quoi fait
chaque étape" émerge de l'ajustement des poids, il n'est pas défini
d'avance comme dans un pipe.

### Pourquoi une couche "complique" l'info tout en "simplifiant" le travail suivant — pas contradictoire

Exemple `sort | uniq` sur un fichier de logs :
- `uniq` seul sur un fichier **non trié** ne sert presque à rien : il ne
  détecte les doublons que s'ils sont **côte à côte** — des doublons
  éloignés passent inaperçus.
- `sort | uniq` : `sort` **réorganise** les lignes pour que les doublons
  se retrouvent côte à côte — ce n'est pas un filtrage, c'est une
  **transformation qui rend le travail suivant possible**.

Transposé aux couches : la couche 1 ne "filtre" pas les pixels — elle les
**transforme** en quelque chose de nouveau ("voici où se trouvent des
bords", une info construite, absente telle quelle des pixels bruts). La
couche 2 reçoit cette info enrichie et peut faire quelque chose
d'impossible directement sur des pixels bruts : assembler des bords
proches pour dire "ceci est un contour d'oreille".

**Les deux affirmations sont vraies en même temps, sans contradiction** :
- La couche **complique/enrichit** l'information brute (plus riche
  qu'avant : pixels → bords avec position/orientation).
- Mais elle **simplifie** le travail de la couche suivante (chercher un
  contour d'oreille est bien plus facile à partir de bords déjà
  identifiés que directement à partir de pixels bruts).

Même paradoxe apparent que `sort` avant `uniq` : trier ajoute une
structure (les lignes ne sont plus dans l'ordre brut du fichier), mais ça
simplifie radicalement le travail de `uniq` derrière. Plus d'information
structurée en sortie = moins de travail difficile pour l'étape suivante.

### Correction importante — CNN ≠ Transformer (LLM)

Point de confusion à corriger explicitement : évoquer un **CNN**
(Convolutional Neural Network, utilisant des **filtres** détectant des
motifs visuels — bords, textures) pour illustrer "plusieurs détecteurs en
parallèle à chaque couche" était une **analogie**, pas une description du
mécanisme réel d'un LLM.

Un LLM est un **Transformer**, qui utilise l'**attention** (Q/K/V, voir
`20-mecanisme-attention-qkv-multihead.md`) plutôt que des filtres. CNN et
Transformer sont deux **architectures différentes** de réseaux de
neurones — toutes deux organisées en couches, mais avec un mécanisme
interne différent à chaque couche (filtres pour CNN, attention pour
Transformer). Le principe général de spécialisation parallèle (plusieurs
détecteurs différents à la même étape) est valable dans les deux, mais ce
n'est pas le même mécanisme concret.

## À venir

- [ ] Fonction d'activation — rôle précis (pourquoi "décider si le signal
      passe")
- [ ] Prompting — bonnes pratiques, few-shot, limites
- [ ] Usage pratique — appeler une API LLM depuis un script
