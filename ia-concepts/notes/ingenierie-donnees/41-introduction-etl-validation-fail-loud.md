# IA — Vague 3 (MLOps/Ops) : Ingénierie de données — introduction

Première session sur la dernière sous-catégorie vierge de la vague 3,
partie d'un vrai bug découvert en direct sur `index_notes.py`.

## Le pipeline ETL qu'on utilise déjà sans le nommer

`index_notes.py` fait exactement ce qu'on appelle un pipeline **ETL**
(Extract, Transform, Load) en ingénierie de données classique, appliqué
au ML :
- **Extract** : lire les fichiers `.md` du repo
- **Transform** : chunking + génération des embeddings
- **Load** : chargement dans Chroma

## Bug réel découvert en testant : le fichier vide silencieux

Test effectué en direct : créer un `test.md` vide et lancer
`index_notes.py`. Résultat : **aucune erreur, aucun warning** — le
script continue normalement.

### Pourquoi ça se passe ainsi

`chunk_text` fait `text.split()` sur une chaîne vide → liste vide →
**zéro chunk généré** pour ce fichier, sans que rien ne le signale. Le
script poursuit silencieusement comme si tout allait bien.

### Pourquoi ce silence est plus dangereux qu'un plantage

Principe clé de l'ingénierie de données : **"fail loud, not silent"**.
Une erreur qui plante bruyamment est immédiatement visible et
corrigible. Un échec silencieux (0 chunk généré, script qui continue)
peut passer inaperçu pendant des mois — une "dette invisible" qui
s'accumule jusqu'à ce que quelqu'un remarque, bien plus tard, que
certaines notes ne remontent jamais dans les recherches.

## Premier concept clé : la validation de données

Vérifier activement, **à l'ingestion**, que ce qu'on reçoit respecte des
règles minimales (pas vide, structure attendue, taille raisonnable)
plutôt que de laisser passer silencieusement n'importe quoi.

### Deux familles de contrôles, pas une seule

Point de clarification important : l'ingénierie de données mélange deux
natures de contrôles différentes, pas juste une.

- **Contrôles déterministes classiques** (comme un test de code
  classique, réponse binaire) : fichier vide ou non, taille aberrante,
  encodage invalide — exactement le type de test "vrai/faux" qu'on
  utiliserait pour n'importe quelle fonction classique.
- **Contrôles statistiques propres au ML** (assertion à seuil, écho de
  `cicd-mlops/39-...md`) : distribution des tailles de chunks
  cohérente, cohérence des embeddings générés — plus proche du
  recall@k (un seuil de tolérance, pas une réponse binaire simple).

## À venir

- Approfondir la validation de données (au-delà du cas "fichier vide") :
  détection d'anomalies plus subtiles, schémas de validation
- Versioning de données (DVC) — déjà esquissé dans
  `exercices/idees-tp-vague3.md`
- Feature stores — concept, à quoi ça sert
- Cycle de vie de la donnée (rétention, suppression, lien avec le RGPD
  déjà vu dans `gouvernance/36-...md`)
