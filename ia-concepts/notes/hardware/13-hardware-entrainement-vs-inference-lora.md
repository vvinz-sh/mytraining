# IA — Hardware : entraînement vs inférence, fine-tuning partiel (LoRA)

Suite de la session hardware (quantization, CUDA/Tensor Cores).

## Pourquoi l'entraînement consomme bien plus que l'inférence

**Inférence** (faire tourner un modèle déjà entraîné) : le calcul ne va
que dans un sens — les données traversent les couches, une réponse sort.
Il faut stocker les poids en mémoire + un peu de mémoire tampon pour les
calculs intermédiaires. Rien de plus.

**Entraînement** : en plus des poids, il faut stocker :
1. **Les gradients** — pour chaque poids, la valeur indiquant dans
   quelle direction et de combien l'ajuster (calculée par la
   **rétropropagation**/backpropagation). Quasi double la mémoire à lui
   seul (poids + gradients de même taille).
2. **Les états de l'optimiseur** — les algorithmes modernes (ex : Adam)
   gardent un historique des ajustements précédents par poids pour
   mieux calibrer le suivant. Peut représenter encore ~2x la taille des
   poids en plus.
3. **Les activations intermédiaires** — ce qui s'est passé à chaque
   couche pendant le passage "aller", nécessaire pour calculer les
   gradients au retour. Grandit avec la taille du batch et la profondeur
   du réseau.

Résultat : entraîner demande grossièrement **4 à 6 fois plus de mémoire**
que l'inférence pour un même nombre de paramètres, en plus de traiter
des batchs de milliers d'exemples en parallèle (vs une poignée de
requêtes en inférence).

### Pourquoi gradients et états d'optimiseur disparaissent après l'entraînement

Une fois les poids figés (calibrés), gradients et états d'optimiseur
n'ont plus aucune fonction — leur seul rôle était de servir de mémoire
de calcul pour ajuster les poids. Sans ajustement à faire, ce sont des
données mortes qu'on jette. Un modèle déployé (téléchargé/interrogé via
API) ne contient jamais que les poids finaux — d'où les "140 Go" pour un
modèle à 70 milliards de paramètres, pas 4-6x plus.

## Conséquence matérielle concrète

- **GPU grand public** (carte gaming) : 8-24 Go de VRAM.
- **GPU datacenter** (ex : NVIDIA H100) : 80 Go+ par puce, conçus pour
  être interconnectés par centaines (liens type NVLink).

L'interconnexion massive de centaines de GPU est **indispensable pour
l'entraînement** des gros modèles : le modèle (poids + gradients + états
d'optimiseur + activations, facteur ×4-6) dépasse largement la capacité
d'un seul GPU, il faut répartir le modèle et les calculs, avec une
synchronisation constante entre puces à chaque étape d'ajustement.

L'**inférence**, elle, ne nécessite que les poids — souvent 1 à 4 GPU
suffisent, parfois un seul avec de la quantization agressive (INT8/INT4),
sans coordination complexe entre centaines de puces (plus d'ajustement
collectif à synchroniser, juste une prédiction qui traverse le modèle
une fois).

C'est pour ça qu'un modèle de taille modeste peut tourner en inférence
sur une carte gaming perso, alors que l'entraîner depuis zéro nécessite
l'équivalent d'un datacenter entier, réservé à une poignée d'entreprises.

## Fine-tuning partiel — LoRA / PEFT

Le fine-tuning complet revient à recalibrer le LLM comme à
l'entraînement initial — même coût massif (gradients + états
d'optimiseur pour des milliards de poids). D'où l'intérêt du
**fine-tuning efficace en paramètres (PEFT)**, dont la technique la plus
connue est **LoRA (Low-Rank Adaptation)**.

Principe : geler presque tous les poids originaux (inchangés), et
ajouter seulement un petit nombre de nouveaux poids "greffés" par-dessus
(souvent < 1% du total), qu'on entraîne, eux, normalement.

Analogie : plutôt que réécrire un script bash de 5000 lignes pour
changer son comportement, on ajoute un petit wrapper qui intercepte et
ajuste certains résultats, sans toucher au script original.

Conséquence hardware : gradients et états d'optimiseur ne sont
nécessaires **que** pour le petit ajout, pas pour les milliards de poids
gelés — la consommation mémoire s'effondre. On peut faire du LoRA sur un
modèle de plusieurs milliards de paramètres avec un **seul GPU grand
public**, là où un fine-tuning complet aurait demandé un cluster.

### Pourquoi ça marche bien malgré un si petit ajout

Pas une question de "l'essentiel du gain vient d'un petit ajustement par
hasard" (type Pareto) — la vraie raison est plus spécifique : les
changements nécessaires pour adapter un modèle à une tâche donnée ont un
**"rang intrinsèque faible"** (*low intrinsic rank*), vérifié
empiriquement. Même si le modèle de base a des milliards de paramètres,
la façon de le réajuster pour une tâche précise peut être décrite avec
beaucoup moins d'information que ça — un peu comme une config complexe à
des centaines de paramètres où, pour un besoin précis, il suffit en
réalité de toucher 3-4 leviers bien choisis.

Nuance : ce n'est pas que la tâche soit "mineure" en général, c'est que
**la nature même du problème** (adapter un modèle à une tâche
spécifique) est structurellement simple à exprimer, même si le modèle
qui la supporte est énorme.

## Reconsolidation — poids et gradients en détail (avec un exemple concret)

Repris plus tard pour bien démystifier ce qu'est concrètement un
gradient, à partir d'un exemple ultra-simplifié à un seul poids.

### Un seul "neurone" pour commencer

Modèle jouet : `prix_prédit = poids × surface`. Avec `poids = 2` et une
surface de 50 m², prédiction = 100. Vrai prix = 150, erreur = 50.

Augmenter le poids à 3 donnerait `3 × 50 = 150` — la bonne réponse.
Mais comment le modèle **sait-il lui-même** qu'il faut augmenter le
poids (pas le diminuer), sans qu'un humain le lui dise ?

### Le gradient — une pente, rien de plus mystérieux

Le gradient répond à : "si j'augmente ce poids d'un tout petit peu,
l'erreur augmente-t-elle ou diminue-t-elle ?" — techniquement une
dérivée, mais l'intuition suffit : une bille sur une courbe
(poids en abscisse, erreur en ordonnée), le gradient dit si le terrain
descend vers la gauche ou la droite à l'endroit où on se trouve.

**Convention** : un gradient **négatif** signifie que l'erreur diminue
quand le poids **augmente** (donc il faut augmenter le poids) ; un
gradient **positif** signifie l'inverse (il faut diminuer le poids).

### Pourquoi des petits pas, jamais un bond direct

Même si le gradient indique la bonne direction, l'algorithme n'ajuste
jamais le poids d'un coup à sa valeur "parfaite". Raison structurelle,
au-delà du simple risque de sur-correction : dans un vrai modèle, il
n'y a pas un seul poids mais des **milliards, tous interconnectés**. Un
même poids participe au calcul de millions d'exemples différents — un
grand saut qui corrige parfaitement un exemple pourrait **casser** ce
qui fonctionnait déjà pour d'autres exemples, puisque ce poids n'est
jamais utilisé isolément.

**Learning rate** : le paramètre qui contrôle la taille du pas
d'ajustement à chaque itération. Compromis à connaître :
- **Trop grand** → le modèle peut osciller sans jamais se stabiliser
  (rebondir d'un bord à l'autre d'une vallée), voire diverger
  (l'erreur augmente au lieu de diminuer).
- **Trop petit** → apprentissage extrêmement lent, des milliers
  d'itérations pour un progrès minime.

### Le cycle d'entraînement complet — vocabulaire assemblé

```
1. Le modèle fait une prédiction (avec ses poids actuels)
2. On compare à la bonne réponse → calcul de l'erreur
3. On calcule le gradient de chaque poids (direction + intensité de correction)
4. On ajuste chaque poids d'un petit pas (taille = learning rate)
5. On répète avec l'exemple suivant, des milliards de fois
```

Ce processus complet (étapes 3-4 : propager l'erreur pour ajuster tous
les poids) s'appelle la **rétropropagation** (backpropagation) — terme
mentionné en passant plus tôt dans le repo, jamais détaillé jusqu'ici.
L'ensemble du mécanisme (avancer par petits pas guidés par le gradient)
s'appelle la **descente de gradient**.

### Lien direct avec le coût mémoire de l'entraînement

Le gradient est cette "boussole" calculée pour **chaque poids
individuellement** — il faut en stocker un pour chacun des milliards de
poids, en parallèle des poids eux-mêmes. C'est exactement pourquoi
l'entraînement double quasiment la mémoire nécessaire (poids +
gradients), avant même de compter les états d'optimiseur — voir le
facteur ×4-6 détaillé plus haut dans cette même note.

## À venir (vague 2)

- [ ] Paramètres de génération (`temperature`, `top_p`/`top_k`)
- [ ] Multimodalité, guardrails, coûts/facturation
- [ ] Outils de l'écosystème (LangChain, bases vectorielles, etc.)
