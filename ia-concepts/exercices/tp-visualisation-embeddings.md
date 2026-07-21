# TP — Visualiser des embeddings de mots dans l'espace

Statut : **réalisé avec succès** ✅. TP léger, tout en Python sur CPU,
aucun GPU ni clé API nécessaire.

## Résultat obtenu (résumé — détails complets dans les notes liées)

Toutes les étapes ont été exécutées avec succès sur environnement WSL2 :
- Arithmétique vectorielle confirmée : `king - man + woman ≈ queen`
  (score 0.77), avec exploration de plusieurs autres analogies.
- Deux découvertes annexes non prévues au design initial :
  - Piège du hors-vocabulaire ignoré silencieusement par `doesnt_match`
  - Limite des embeddings **statiques** face à la polysémie (ex : "bank"),
    et pourquoi les LLM modernes (embeddings **contextuels** via
    l'attention) résolvent ce problème
- Visualisation PCA en 2D réalisée (matplotlib, via `savefig` — `plt.show()`
  ne fonctionne pas nativement sous WSL sans serveur graphique), avec
  regroupements cohérents observés (royauté, pays/capitales, animaux)
- Découverte méthodologique importante : la PCA en 2D **déforme** les
  distances réelles — une paire de mots peut sembler très proche sur le
  graphique sans l'être réellement dans l'espace complet à 100
  dimensions (vérifié concrètement avec tokyo/japan vs paris/france)

Détails complets, code exact et explications dans :
- `ia-concepts/notes/28-exploration-pratique-gensim-glove.md`
  (arithmétique vectorielle, doesnt_match, polysémie)
- `ia-concepts/notes/29-visualisation-pca-piege-distorsion.md`
  (PCA, visualisation, piège de la distorsion)

## Objectif initial

Reproduire soi-même la visualisation vue dans la vidéo 3Blue1Brown :
placer des mots dans un espace réduit à 2D/3D et vérifier
concrètement l'arithmétique roi - homme + femme ≈ reine.

## Pipeline

```
Mots → vecteurs (word2vec/GloVe via gensim)
     → réduction de dimensionnalité (PCA ou t-SNE)
     → affichage (matplotlib ou plotly)
```

## Étapes envisagées

1. **Installer gensim** (bibliothèque Python pour word2vec/GloVe) :
   ```bash
   pip install gensim --break-system-packages
   ```
2. **Charger un modèle pré-entraîné** — gensim permet de télécharger des
   vecteurs déjà entraînés sans avoir à entraîner soi-même :
   ```python
   import gensim.downloader as api
   model = api.load("glove-wiki-gigaword-100")  # 100 dimensions, léger
   ```
3. **Tester l'arithmétique vectorielle directement** (sans même
   visualiser, pour valider le concept en premier) :
   ```python
   model.most_similar(positive=['roi', 'femme'], negative=['homme'])
   # devrait faire ressortir "reine" en tête de liste
   ```
   Point d'attention : les modèles GloVe standards sont souvent
   entraînés sur corpus **anglais** — à vérifier s'il existe une version
   française équivalente disponible via gensim, sinon tester d'abord
   avec "king", "man", "woman", "queen" en anglais.
4. **Sélectionner un petit ensemble de mots à visualiser** — un mélange
   volontaire de paires liées (roi/reine, homme/femme, Paris/France,
   Berlin/Allemagne) et de mots sans rapport, pour bien voir les
   regroupements et écarts.
5. **Réduire la dimensionnalité** avec PCA (rapide, simple) :
   ```python
   from sklearn.decomposition import PCA
   vecteurs_2d = PCA(n_components=2).fit_transform(vecteurs_des_mots)
   ```
   Alternative à tester ensuite pour comparer : t-SNE
   (`sklearn.manifold.TSNE`), potentiellement plus fidèle visuellement
   mais plus lent.
6. **Afficher avec matplotlib** (statique, simple pour commencer) :
   annoter chaque point avec le mot correspondant.
7. **Bonus** : passer à `plotly` pour un graphique interactif
   (zoomable/rotable), plus agréable à explorer.

## Ce qu'il faudra vérifier/clarifier en le codant

- Disponibilité d'un modèle GloVe/word2vec en **français** via gensim
  (sinon travailler en anglais pour ce TP, ou chercher un modèle
  alternatif comme les vecteurs FastText de Facebook, disponibles en
  plusieurs langues).
- Le choix entre PCA et t-SNE aura probablement un vrai impact visuel à
  comparer concrètement (PCA peut écraser certaines relations fines que
  t-SNE préserve mieux, ou l'inverse selon les mots choisis).

## Compétences pratiquées

- Manipulation d'embeddings pré-entraînés (gensim)
- Arithmétique vectorielle concrète (`most_similar` avec positive/negative)
- Réduction de dimensionnalité (PCA, t-SNE) — notion pas encore vue en
  détail avant ce TP, à découvrir en pratique
- Visualisation de données (matplotlib/plotly)

## Extension future — comparer avec Llama (TP local)

Une fois le TP LLM local (Ollama/QLoRA) réalisé, refaire ce même exercice
de visualisation en extrayant les embeddings d'un modèle comme Llama
3.1 8B plutôt que word2vec/GloVe — deux intérêts :
- Vérifier concrètement que l'environnement GPU/Ollama fonctionne bien de
  bout en bout sur un cas d'usage différent du premier TP.
- Comparer la structure de l'espace vectoriel entre un modèle "classique"
  (word2vec, embeddings statiques, un seul vecteur fixe par mot) et un
  LLM moderne (embeddings contextuels, qui varient selon le contexte de
  la phrase — point pas encore vu en détail, à explorer à cette
  occasion).

Point à anticiper : extraire les embeddings internes d'un modèle comme
Llama est un peu plus complexe qu'avec gensim (nécessite d'accéder aux
couches internes du modèle, pas juste un appel d'API classique) — prévoir
d'utiliser une bibliothèque comme `transformers` (Hugging Face) plutôt
que Ollama pour cette extraction spécifique.

## Lien avec les notes existantes

Prolonge directement `23-visualisation-embeddings-hypothese-distributionnelle.md`
et les notions RAG/embeddings vues plus tôt (`02-...`,
`pipeline_rag_embedding_generation`).
