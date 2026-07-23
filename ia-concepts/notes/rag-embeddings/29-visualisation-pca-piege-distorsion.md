# IA — Visualisation PCA des embeddings et le piège de la distorsion

Suite et fin du TP embeddings — réduction de dimensionnalité et
visualisation, avec une découverte méthodologique importante en prime.

## Pipeline exécuté avec succès

```python
mots = ['king', 'queen', 'man', 'woman', 'prince', 'princess',
        'paris', 'france', 'tokyo', 'japan', 'berlin', 'germany',
        'dog', 'cat', 'puppy', 'kitten']
vecteurs = [model[mot] for mot in mots]

from sklearn.decomposition import PCA
pca = PCA(n_components=2)
vecteurs_2d = pca.fit_transform(vecteurs)

import matplotlib.pyplot as plt
plt.figure(figsize=(10, 8))
plt.scatter(vecteurs_2d[:, 0], vecteurs_2d[:, 1])
for i, mot in enumerate(mots):
    plt.annotate(mot, (vecteurs_2d[i, 0], vecteurs_2d[i, 1]))
plt.title("Visualisation d'embeddings de mots (PCA)")
plt.savefig('embeddings_viz.png', dpi=150, bbox_inches='tight')
```

Note pratique WSL : `plt.show()` échoue (pas de serveur d'affichage
graphique par défaut) — utiliser `plt.savefig()` vers un chemin
accessible depuis Windows (`/mnt/c/Users/...`) à la place.

## Résultat obtenu — regroupements cohérents observés

- **Animaux** (kitten, puppy, dog, cat) — bien groupés ensemble.
- **Pays/capitales** (germany/berlin, france/paris, japan/tokyo) —
  chaque paire proche géométriquement.
- **Royauté** (king, queen, prince, princess) — regroupés, avec une
  séparation visible entre le duo masculin (king/prince) et le duo
  féminin (queen/princess) — la même direction géométrique
  "masculin → féminin" que l'arithmétique vectorielle testée
  précédemment (`23-...md`, `28-...md`), mais visible directement sur
  le graphique.
- **man/woman** — plus isolés, cohérent avec le fait que ce sont des
  mots plus génériques que les paires spécifiques environnantes.

## ⚠️ Découverte méthodologique importante : le piège de la distorsion PCA

Observation initiale sur le graphique : "tokyo" et "japan" semblaient se
chevaucher presque exactement, beaucoup plus proches que "paris"/"france"
ou "berlin"/"germany".

Hypothèse testée (plausible mais pas vérifiée) : association culturelle
plus forte tokyo/japon que pour les autres paires.

### Vérification directe dans l'espace complet (sans PCA)

```python
model.similarity('tokyo', 'japan')    # 0.746
model.similarity('berlin', 'germany') # 0.729
model.similarity('paris', 'france')   # 0.748
```

**Résultat : hypothèse infirmée.** Les trois scores sont quasi
identiques (0.73-0.75), "paris/france" est même légèrement le plus élevé
des trois — alors que sur le graphique 2D, "tokyo/japan" semblait de
loin la paire la plus proche.

### Explication : la PCA en 2D n'est qu'une projection, elle déforme

Les vecteurs originaux ont 100 dimensions ; les écraser à 2 pour
l'affichage peut faire sembler deux mots très proches simplement parce
que la PCA a "aplati" une différence qui existait dans les dimensions
qu'elle a choisi d'ignorer — pas forcément parce qu'ils sont réellement
proches dans l'espace complet.

## Leçon méthodologique à retenir

**Une visualisation 2D d'embeddings est utile pour l'intuition générale
des regroupements, mais jamais fiable pour comparer des distances
précises entre deux points spécifiques.** Pour une comparaison précise,
toujours revenir au calcul de similarité dans l'espace original
(toutes les dimensions), jamais se fier à ce que montre l'œil sur une
projection réduite.

Même réflexe de vérification indépendante pratiqué depuis le début des
sessions IA (`11-limites-hallucinations-surconfiance.md`,
`28-exploration-pratique-gensim-glove.md`), appliqué ici à une
visualisation plutôt qu'à une réponse de LLM — la conclusion tirée
visuellement doit toujours être vérifiée par un calcul direct avant
d'être considérée comme fiable.

## TP embeddings — terminé ✅

Toutes les étapes prévues dans `ia-concepts/exercices/tp-visualisation-embeddings/tp-visualisation-embeddings.md`
ont été réalisées avec succès : arithmétique vectorielle, exploration
(doesnt_match, polysémie), réduction PCA, visualisation matplotlib.
Reste en extension future (non prioritaire) : comparaison avec des
embeddings contextuels extraits d'un vrai LLM (Llama via
`transformers`), et test de t-SNE en comparaison de PCA.
