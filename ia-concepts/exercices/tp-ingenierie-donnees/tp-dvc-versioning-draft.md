# TP — Versionner la base Chroma avec DVC (draft)

Statut : **design posé, pas encore exécuté**. Dernier TP de la vague 3,
rattaché à "Ingénierie de données pour le ML"
(`ingenierie-donnees/41-...md`).

## Objectif

Pouvoir revenir à une version antérieure de la base `chroma_notes_db/`
si une réindexation casse quelque chose — le réflexe Git appliqué aux
données plutôt qu'au code, en pratique cette fois (pas juste en
théorie comme dans `cicd-mlops/38-...md`).

## Rappel du problème que DVC résout

Rappel de `cicd-mlops/38-...md` : Git ne gère pas bien le binaire — un
`git add chroma_notes_db/` stockerait le fichier entier à chaque
commit, sans diff efficace. DVC stocke juste une **référence** (hash)
dans Git, et les fichiers lourds ailleurs.

## Étape 1 — Installation et initialisation

```bash
pip install dvc --break-system-packages
cd mytraining
dvc init
```

Ça crée un dossier `.dvc/` dans le repo, avec sa propre configuration —
à commiter dans Git normalement (c'est léger, juste de la config).

## Étape 2 — Faire suivre la base Chroma par DVC plutôt que Git

```bash
dvc add exercices/tp-rag-mcp/chroma_notes_db
```

Ça génère un petit fichier `chroma_notes_db.dvc` (juste un hash et des
métadonnées, quelques lignes) — **c'est ce fichier-là** qu'on commite
dans Git, pas la base elle-même :

```bash
git add exercices/tp-rag-mcp/chroma_notes_db.dvc .gitignore
git commit -m "Versionner la base Chroma avec DVC"
```

Point à vérifier : DVC ajoute normalement automatiquement une entrée au
`.gitignore` pour exclure le vrai dossier `chroma_notes_db/` du suivi
Git classique (puisque DVC le suit à sa place).

## Étape 3 — Configurer un stockage distant (remote)

Sans ça, DVC versionne uniquement en local — pas de sauvegarde
externe, pas de partage possible. Options les plus simples pour un
usage perso :

```bash
# Option A - simple dossier local différent (pour tester le mécanisme sans compte cloud)
dvc remote add -d stockage_local /home/vinz/dvc-storage

# Option B - un vrai stockage cloud (S3, Google Drive...) si disponible
```

Je pencherais pour l'Option A pour ce TP — valider le mécanisme de
versioning sans dépendance à un service externe payant.

```bash
dvc push
```

## Étape 4 — Test réel du versioning (le vrai objectif du TP)

1. Noter l'état actuel : `dvc status`
2. Modifier volontairement la base (ajouter un faux fichier de test à
   l'indexation, comme dans le TP sécurité, puis réindexer)
3. `dvc add` + `git commit` cette nouvelle version
4. **Simuler le problème** : imaginer que cette réindexation a "cassé"
   quelque chose (recall dégradé, détecté par le TP monitoring)
5. **Revenir en arrière** :
   ```bash
   git checkout HEAD~1 -- exercices/tp-rag-mcp/chroma_notes_db.dvc
   dvc checkout
   ```
6. Vérifier que la base Chroma est bien revenue à son état précédent
   (relancer une recherche test, comparer au comportement d'avant)

## Ce qu'il faudra vérifier/clarifier en codant

- Le stockage local (Option A) suffit pour comprendre le mécanisme,
  mais n'offre aucune vraie sauvegarde externe — à documenter comme
  limite si le TP s'arrête là
- Vérifier que `dvc checkout` restaure bien un dossier Chroma
  **complet et cohérent** (pas de fichiers SQLite partiellement
  restaurés qui casseraient l'intégrité de la base)
- Taille réelle de la base après plusieurs versions stockées — à
  surveiller si le TP est répété plusieurs fois avec beaucoup de
  changements

## Compétences pratiquées

- Installation et initialisation de DVC dans un repo Git existant
- Versioning de données binaires volumineuses sans polluer l'historique
  Git
- Configuration d'un stockage distant DVC
- Test réel d'un scénario de rollback de données (pas seulement de code)

## Lien avec les notes existantes

Prolonge directement `cicd-mlops/38-cicd-mlops-registry-tracking-reentrainement.md`
(pourquoi Git seul ne suffit pas pour du binaire) et
`ingenierie-donnees/41-introduction-etl-validation-fail-loud.md`
(pipeline ETL déjà pratiqué). Réutilise l'infrastructure du TP RAG/MCP
(`exercices/tp-rag-mcp/`).

---

## Vague 3 — les 5 TP maintenant tous draftés

Avec ce dernier design, les 5 idées notées dans
`exercices/idees-tp-vague3.md` ont chacune leur design détaillé :
`tp-deploiement/`, `tp-monitoring/`, `tp-cicd/`, `tp-gouvernance/`,
`tp-ingenierie-donnees/`. Aucun n'est encore exécuté — un beau
programme de pratique à enchaîner quand l'envie prendra.
