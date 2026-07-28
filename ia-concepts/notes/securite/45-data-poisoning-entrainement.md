# IA — Data poisoning : empoisonnement du dataset d'entraînement

Complète la note 32 (mémorisation/extraction, differential privacy) —
un risque différent bien que voisin : la note 32 traite de ce qu'un
modèle peut **révéler involontairement** après un entraînement propre ;
ici, il s'agit d'un attaquant qui **manipule délibérément** les données
d'entraînement elles-mêmes pour influencer le comportement final du
modèle. Née d'une réflexion sur notre propre TP LLM local, où 504
exemples générés par API ont été utilisés sans vérification
individuelle avant l'entraînement.

## Pourquoi le dataset est une cible plus discrète que le modèle lui-même

Deux cibles possibles pour un attaquant : modifier directement les
poids d'un modèle déjà entraîné, ou glisser des exemples malveillants
dans le dataset **avant** l'entraînement.

- **Poids du modèle** : un artefact binaire (`.safetensors`), souvent
  signé, versionné, avec une empreinte vérifiable — une modification
  est en théorie détectable par comparaison de hash ou de provenance.
- **Dataset d'entraînement** : simplement du texte, potentiellement
  des milliers de lignes. Quelques dizaines d'exemples empoisonnés
  noyés dans un grand volume légitime sont **structurellement
  invisibles** à l'œil nu, et aucune des métriques d'entraînement
  standard (loss, `eval_loss`, `grad_norm` moyens) ne les fait
  ressortir — une répartition équilibrée par catégorie (comme nos
  28 exemples/type) ne garantit en rien l'absence de manipulation
  ciblée à l'intérieur d'une catégorie.

Exemple concret : des exemples "log contenant tel mot-clé rare →
réponse toujours *aucune action requise*", même face à un vrai
incident critique — un empoisonnement ciblé qui n'apparaîtrait dans
aucune moyenne globale.

## Où intervenir : avant l'entraînement, avec une vérification distincte de la mémorisation

Contrairement à la mémorisation (note 32), où le "quoi chercher" est
inconnaissable à l'avance, le data poisoning peut faire l'objet d'une
**vérification préventive** du dataset avant même de lancer
l'entraînement — le pipeline distingue clairement :

### 1. Détection d'anomalie statistique (avant entraînement)

Encoder chaque exemple du dataset avec un modèle d'embeddings (même
principe qu'un guardrail sémantique, appliqué ici au dataset plutôt
qu'aux messages en production), puis chercher des points qui
s'écartent significativement du "nuage" principal des exemples
légitimes. Un exemple empoisonné a souvent une structure
input/output artificiellement construite, détectable par cette
distance à la moyenne.

### 2. Signature spectrale (après entraînement, sur les activations)

Une trace détectable non pas dans le texte brut, mais dans la façon
dont le modèle **traite** ces exemples en interne (activations)
différemment des exemples légitimes — nécessite un modèle déjà
entraîné pour être observée.

### 3. Fonctions d'influence (après entraînement, coûteux)

Estimer l'impact de chaque exemple sur le comportement final du
modèle en simulant son retrait. Un exemple isolé dont l'effet est
disproportionné sur des cas sans rapport apparent est suspect —
techniquement lourd (dérivées de second ordre, souvent nécessite un
ré-entraînement ou une approximation coûteuse), à réserver aux cas où
une manipulation est déjà soupçonnée plutôt qu'en vérification
systématique.

### 4. Differential privacy — limiter l'impact plutôt que détecter (voir note 32)

DP-SGD ne détecte rien — il **limite structurellement** l'influence
que tout exemple individuel peut avoir, empoisonné ou non, via deux
mécanismes successifs :
- **Écrêtage (clipping)** : plafonner la norme du gradient de chaque
  exemple à une valeur maximale, **avant** tout ajout de bruit. Un
  exemple empoisonné, qui pousse souvent plus fort qu'un exemple
  légitime pour "forcer" un comportement, se retrouve ramené à la
  même échelle que les autres — son influence est déjà réduite avant
  même la seconde étape.
- **Bruit** ajouté ensuite à la somme des gradients (détaillé en note
  32).

**Nuance importante** : DP-SGD n'a pas été conçu comme un détecteur de
poisoning — son objectif premier est la confidentialité (empêcher la
mémorisation d'exemples individuels). L'effet protecteur contre le
poisoning est un effet de bord réel, pas une garantie de détection
explicite.

**Piste de détection dérivée, non conçue à l'origine pour ça** : la
**fréquence à laquelle un exemple précis déclenche l'écrêtage** au fil
des epochs peut servir de signal statistique — un exemple
systématiquement écrêté alors que la grande majorité du dataset ne
l'est presque jamais est suspect, sans que ce soit une preuve formelle.

## Ce que ça change pour notre propre TP (rétrospective)

Sur `dataset_entrainement_chatml.json` (504 exemples), aucune des
quatre techniques n'a été appliquée — ni détection d'outlier par
embedding en amont, ni DP-SGD pendant l'entraînement (LoRA/QLoRA
standard, sans mécanisme de confidentialité différentielle). La
génération via API réduit le risque par rapport à un corpus web
massif et non contrôlé, mais ne l'élimine pas structurellement — un
prompt de génération biaisé, ou une erreur systématique du modèle
générateur sur un type d'incident précis, produirait un effet proche
d'un empoisonnement, sans intention malveillante.

## Résumé

1. Le dataset d'entraînement est une cible plus discrète que le modèle
   entraîné lui-même — un texte se noie dans la masse là où un binaire
   modifié laisse une trace vérifiable.
2. Les métriques d'entraînement globales (loss, répartition par
   catégorie) ne détectent pas un empoisonnement ciblé et minoritaire.
3. Détection d'outlier par embedding = avant entraînement, sur le
   texte brut. Signature spectrale et fonctions d'influence = après
   entraînement, sur le comportement du modèle.
4. Differential privacy (DP-SGD) ne détecte pas le poisoning — elle
   limite structurellement l'impact de tout exemple individuel via
   écrêtage puis bruit, avec un effet protecteur en bonus, pas
   garanti ni conçu pour ça à l'origine.

## Lien avec les notes existantes

`32-memorisation-extraction-attack-differential-privacy.md` (mécanisme
détaillé de DP, compromis confidentialité/performance),
`25-guardrails-prompt-injection-moindre-privilege.md` (défense en
profondeur, principe transposé ici à l'entraînement plutôt qu'à
l'inférence), `tp-llm-local-phase2-resultat.md` et
`tp-llm-local-phase3-resultat.md` (dataset généré sans vérification
individuelle, cas d'usage concret discuté ici).
