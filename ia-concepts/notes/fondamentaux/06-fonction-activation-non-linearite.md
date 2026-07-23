# IA — Fonction d'activation : pourquoi la non-linéarité est nécessaire

## Le problème sans fonction d'activation

Fait mathématique clé : **empiler plusieurs couches qui font uniquement
des sommes pondérées (sans rien d'autre entre elles) revient
mathématiquement à une seule couche.** Peu importe le nombre de couches
empilées, ça s'effondre en une seule transformation équivalente.

Conséquence directe : sans fonction d'activation, la progression vue
précédemment (couche 1 = bords → couche 2 = formes → couche 3 = parties)
serait **impossible**. On perdrait toute la notion d'abstraction
progressive — il ne resterait qu'une seule transformation générale, quel
que soit le nombre de couches empilées.

## Analogie calques Photoshop (retenue, avec nuance)

- Calques en mode **"Normal"** (opacité, combinaison proportionnelle
  simple) → équivalent à un seul calque recalculable, exactement comme
  les couches sans activation qui s'effondrent en une seule.
- Calques en mode **non linéaire** (Overlay, Multiply, Screen) → l'effet
  dépend du contenu (ex : Multiply assombrit fortement les zones déjà
  sombres, peu d'effet sur les zones claires) — impossible de recombiner
  en un seul calque équivalent.

C'est exactement le rôle de la fonction d'activation : introduire une
**non-linéarité** qui empêche l'effondrement, permettant à chaque couche
d'apporter une vraie transformation supplémentaire.

## Pourquoi ReLU (fonction simple) suffit à casser la linéarité

ReLU : si négatif → 0, sinon → garde la valeur.

Point de correction important : ce n'est **pas** le fait d'appliquer la
fonction "par couche" qui casse la linéarité (une fonction linéaire
appliquée à chaque couche resterait linéaire et s'effondrerait quand
même). C'est **le comportement de la fonction elle-même** qui est non
linéaire.

Une fonction linéaire garde toujours le même écart proportionnel entre
deux valeurs après transformation. ReLU casse ça : ReLU(-3) = 0 et
ReLU(-1) = 0 → l'écart entre -3 et -1 disparaît complètement. Mais
ReLU(1) = 1 et ReLU(3) = 3 → l'écart est intact. La fonction se comporte
**différemment selon la zone** (négatif vs positif) — cette rupture de
comportement uniforme est ce qui empêche de recombiner le tout en une
seule transformation globale équivalente. Une seule application de ReLU
suffirait déjà à casser la linéarité ; l'appliquer à chaque couche sert
juste à profiter de cette cassure de façon répétée.

## Récap — rôle de la fonction d'activation

1. Sans elle : empiler des couches = un seul gros calcul proportionnel
   (linéaire), quel que soit le nombre de couches.
2. Avec elle (ex. ReLU) : chaque couche introduit une "cassure" qui
   empêche l'effondrement — c'est ce qui rend possible la progression
   bords → formes → parties (abstraction croissante).
3. La non-linéarité vient du **comportement de la fonction elle-même**
   (traitement différent selon la zone de valeurs), pas du fait de
   l'appliquer plusieurs fois à des couches différentes.

## À venir

- [ ] Prompting — bonnes pratiques, few-shot, limites
- [ ] Usage pratique — appeler une API LLM depuis un script
