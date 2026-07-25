# TP — Pipeline CI/CD sur le repo (GitHub Actions + golden dataset) (draft)

Statut : **design posé, pas encore exécuté**. Dépend directement du TP
Monitoring (`exercices/tp-monitoring/`) — ce TP l'**automatise**, il ne
le remplace pas. Rattaché à "CI/CD & pipelines MLOps"
(`cicd-mlops/38-...md`, `39-...md`, `40-...md`).

## Objectif

À chaque push sur `mytraining`, relancer automatiquement l'indexation
+ le calcul du golden dataset, et faire **échouer le build** si le
recall@k moyen descend sous un seuil défini — une vraie application du
principe "monitoring continu" vu en théorie, pas un test lancé une
seule fois à la main.

## Prérequis à valider avant de commencer

Ce TP suppose que le TP Monitoring (golden dataset + script recall@k)
est déjà fonctionnel — sinon, il n'y a rien à automatiser. À faire
dans l'ordre : Monitoring d'abord, CI/CD ensuite.

## Étape 1 — Le workflow GitHub Actions

Fichier `.github/workflows/verifier-recall.yml` :

```yaml
name: Vérification recall@k

on:
  push:
    paths:
      - 'ia-concepts/**/*.md'

jobs:
  test-recall:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Installer Python et dépendances
        run: |
          pip install sentence-transformers chromadb --break-system-packages

      - name: Réindexer la base
        run: python exercices/tp-rag-mcp/index_notes.py

      - name: Calculer le recall@k
        run: python exercices/tp-monitoring/calculer_recall.py --seuil 0.7
```

Le déclencheur (`on: push, paths: ia-concepts/**/*.md`) ne relance le
workflow **que** si des fichiers de notes ont changé — pas à chaque
modification de code sans rapport.

## Étape 2 — Adapter le script pour qu'il échoue proprement

Le script `calculer_recall.py` (basé sur celui du TP Monitoring) doit
**sortir avec un code d'erreur** si le seuil n'est pas atteint, pour que
GitHub Actions détecte l'échec :

```python
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--seuil", type=float, default=0.7)
args = parser.parse_args()

# ... calcul du recall@k moyen (repris du TP Monitoring) ...

if recall_moyen < args.seuil:
    print(f"ÉCHEC : recall@3 moyen = {recall_moyen:.2f}, sous le seuil de {args.seuil}")
    sys.exit(1)  # code de sortie non-zéro = échec du job GitHub Actions
else:
    print(f"OK : recall@3 moyen = {recall_moyen:.2f}")
    sys.exit(0)
```

## Étape 3 — Test réel du mécanisme (cas positif ET négatif)

Méthodologie de test déjà appliquée dans le TP sécurité — vérifier les
deux sens, pas seulement le cas qui marche :

1. **Cas positif** : pousser une modification normale (ex : une note
   corrigée), vérifier que le workflow passe au vert.
2. **Cas négatif, provoqué délibérément** : simuler une régression —
   par exemple, renommer temporairement un fichier attendu dans le
   golden dataset sans mettre à jour `golden_dataset.json`, pousser, et
   vérifier que le workflow **échoue** bien avec le message attendu.
   Annuler ensuite ce changement de test.

## Ce qu'il faudra vérifier/clarifier en codant

- Le runner GitHub Actions (`ubuntu-latest`) a-t-il assez de ressources
  pour charger `sentence-transformers` sans lenteur excessive à chaque
  run — à mesurer en pratique, potentiellement optimiser avec un cache
  de dépendances (`actions/cache`)
- Le chemin de la base Chroma en environnement CI (éphémère, pas
  `/home/vinz/...`) — probablement un chemin relatif au repo checkout,
  différent du chemin local habituel
- Décider si l'échec du workflow doit juste **notifier** (rouge sur
  GitHub) ou bloquer un merge de pull request (protection de branche à
  configurer séparément dans les paramètres GitHub)

## Compétences pratiquées

- Écriture d'un workflow GitHub Actions déclenché sur des chemins
  spécifiques
- Scripts avec code de sortie explicite pour intégration CI/CD
- Test du pipeline lui-même en cas positif et négatif délibérés
- Première vraie boucle de monitoring continu automatisée du repo

## Lien avec les notes existantes

Prolonge directement `cicd-mlops/38-...md` (cycle
monitoring→réentraînement, ici simplifié en
monitoring→échec-de-build plutôt que réentraînement complet, jugé
disproportionné pour ce repo) et réutilise le golden dataset du TP
Monitoring. Bon exemple concret du principe transversal Git/CI-CD déjà
esquissé dans `reflexions-transversales.md`.
