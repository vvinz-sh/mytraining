# IA — Série de consolidation : couches, activation, attention, RAG, diversité

Session de questions courtes pour vérifier l'ancrage des notions vues
récemment, après un moment de "trop d'infos séparées".

## Q1 — Empilement de couches

Une couche prend `[4, 1]` → ressort `[9]`. Ce `9` devient l'**entrée** de
la couche suivante. Base du principe d'empilement (écho pipe Unix :
`commande1 | commande2`).

## Q2 — Pourquoi l'activation empêche l'effondrement en une seule couche

Rappel de l'analogie calques Photoshop : les calques en mode "Normal"
(opacité, combinaison proportionnelle) se recombinent en un seul calque
équivalent. Ceux en mode "Multiply" ne le peuvent pas, car **l'effet
dépend du contenu** (assombrit fortement le sombre, peu d'effet sur le
clair) — pas une proportion fixe uniforme partout.

Transposé à ReLU : traite différemment les valeurs négatives (→ 0) et
positives (inchangées) — un traitement qui **dépend du contenu** (signe
de la valeur), exactement comme Multiply dépend du contenu (luminosité).
C'est cette dépendance au contenu, plutôt qu'une simple proportion fixe,
qui empêche la recombinaison en une seule transformation globale
équivalente — d'où la nécessité de la non-linéarité pour que
l'empilement de couches apporte réellement quelque chose.

## Q3 — Pourquoi l'attention compare à TOUS les mots, pas juste le voisin

Un référent (ex : "il") peut se trouver n'importe où dans la phrase (au
début, loin du mot actuel), pas forcément juste avant. Si le modèle ne
regardait que le mot immédiatement précédent, il raterait les références
à longue distance. D'où la comparaison Query vs Key avec **tous** les
autres mots de la séquence, peu importe leur position.

## Q4 — RAG vs attention : où se situe la comparaison Query/Key

Même logique de base (Query vs Key par similarité, pondération des
Values), mais la différence clé est **où se trouve la comparaison** :

- **RAG** : la Query (la question) est comparée à des Keys venant d'une
  **base de documents externe**, en dehors du modèle — recherche qui va
  chercher des données ailleurs, avant que le modèle ne "pense".
- **Attention** : la Query (un mot) est comparée aux Keys des **autres
  mots de la même séquence**, à l'intérieur même du modèle, à chaque
  couche — pas de recherche externe, tout se passe entre les tokens déjà
  présents dans le texte en cours de traitement.

Résumé : externe = en dehors du texte/contexte actuel (base séparée) vs
interne = entre les éléments du texte en cours de traitement.

## Q5 — Forêt aléatoire vs multi-head attention : source de la diversité

Les deux mécanismes combinent plusieurs éléments indépendants
(arbres/têtes), mais la **source de la diversité** entre ces éléments
diffère :

- **Forêt aléatoire** : diversité par les **données** — chaque arbre voit
  un sous-échantillon différent des données d'entraînement.
- **Multi-head attention** : diversité par le **paramétrage** — toutes
  les têtes voient exactement la **même** phrase, mais chaque tête a des
  poids Q/K/V différents (initialisés différemment, puis ajustés
  indépendamment pendant l'entraînement).

Même principe général (diversité de points de départ → spécialisations
différentes → résultat combiné plus riche), mais mécanisme de diversité
différent : données (forêt) vs paramètres (attention).

## Points bien consolidés dans cette session

1. Empilement de couches = enchaînement séquentiel simple (sortie → entrée)
2. Non-linéarité nécessaire = dépendance au contenu, pas juste "rendre
   les choses plus complexes"
3. Attention = portée globale sur toute la séquence, pas juste le voisin
   immédiat
4. RAG et attention partagent la même logique Query/Key/Value, mais
   diffèrent sur l'emplacement (externe vs interne)
5. Diversité par données (forêt aléatoire) ≠ diversité par paramètres
   (multi-head attention) — deux mécanismes différents pour un même
   objectif (spécialisations complémentaires)
