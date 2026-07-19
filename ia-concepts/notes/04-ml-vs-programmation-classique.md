# IA — Machine Learning vs programmation classique

## Le changement d'angle fondamental

**Programmation classique** — on écrit les règles soi-même (ex : détection
de spam via `si sujet contient "GRATUIT"` ou `si expéditeur en liste
noire`). Approche **réactive** : chaque cas raté nécessite qu'un humain
rajoute une règle, intenable dès que le problème a trop de variations.

**Machine Learning** — au lieu d'écrire les règles, on donne au système
des milliers/millions d'exemples déjà étiquetés, et c'est le système qui
**déduit lui-même** les motifs.

Point plus profond que la simple réactivité : pour certains problèmes
(reconnaître un visage à partir de pixels), il est **impossible d'écrire
les règles à la main**, même avec un temps illimité — la variabilité
(angle, lumière, expression) rend ça combinatoire à l'infini. Personne ne
sait formuler ces règles explicitement, même un expert.

## Ce qui change pendant l'entraînement : les poids

Ce qui est ajusté à l'intérieur du système, ce sont des **poids**
(paramètres) — millions/milliards de nombres réglables.

Analogie : un immense standard téléphonique avec des milliards de
potentiomètres. Avant l'entraînement, réglés au hasard (prédictions
aléatoires). Pendant l'entraînement : à chaque exemple, le système prédit,
on compare à la bonne réponse (étiquette), et si c'est faux, on ajuste
légèrement les poids dans la bonne direction. Répété des millions de fois.

Résultat final : rien n'est écrit en dur comme du code (pas de ligne
"si ceci alors visage") — juste des milliards de poids réglés à des
valeurs précises qui, combinés, produisent la bonne réponse la plupart du
temps.

Un LLM = même principe, appliqué au texte, à bien plus grande échelle
(centaines de milliards de poids).

## Pourquoi beaucoup d'exemples, variés, sont nécessaires

Deux raisons :

1. **Représentativité** — il faut couvrir la diversité réelle des cas
   (couleurs, races, poses différentes pour un chat, par exemple).
2. **Éviter le surapprentissage (overfitting)** — avec un seul exemple ou
   trop peu de diversité, le système risque de "mémoriser" des détails
   spécifiques à cet exemple précis (ex : un reflet particulier dans
   l'œil) au lieu d'apprendre les vraies caractéristiques générales du
   concept.

## Biais du dataset — piège concret

Exercice : un système entraîné **uniquement** sur des chats blancs
reconnaîtra mal (ou pas) un chat noir. Le système a appris à tort que
"blanc" fait partie des caractéristiques d'un chat, faute de diversité
pour lui prouver le contraire — un signal parasite (couleur) pris pour
pertinent, noyant les vraies caractéristiques (oreilles, moustaches,
forme).

C'est le **biais du jeu de données (dataset bias)** : un modèle est aussi
bon que les données qu'on lui montre, jamais meilleur. Un dataset non
représentatif = mauvaise généralisation, même si l'apprentissage sur les
données fournies est parfait.

## Les trois piliers du ML de base (récap)

1. Poids/paramètres ajustés progressivement, plutôt que règles écrites à
   la main.
2. Beaucoup d'exemples variés nécessaires pour généraliser plutôt que
   mémoriser.
3. Surapprentissage et biais du dataset — deux pièges directement liés au
   manque de diversité/volume des données d'entraînement.

## À venir

- [ ] Réseaux de neurones — intuition (comment les poids sont organisés,
      couches, activation)
- [ ] Prompting — bonnes pratiques, few-shot, limites
- [ ] Usage pratique — appeler une API LLM depuis un script
