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

## À venir

- [ ] Fonction d'activation — rôle précis (pourquoi "décider si le signal
      passe")
- [ ] Prompting — bonnes pratiques, few-shot, limites
- [ ] Usage pratique — appeler une API LLM depuis un script
