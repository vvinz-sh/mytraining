# IA — Deep learning vs ML, arbres de décision, forêts aléatoires

## Deep learning ≠ Machine Learning : un sous-ensemble, pas un synonyme

Le **ML** est le principe général : ajuster des paramètres à partir de
données plutôt qu'écrire des règles à la main. Il existe des techniques
de ML qui **ne sont pas** des réseaux de neurones (arbres de décision,
forêts aléatoires, SVM...).

Le **deep learning** désigne spécifiquement le ML fait avec des
**réseaux de neurones à plusieurs couches** (la structure vue
précédemment : entrée → couches cachées → sortie, abstraction
progressive, non-linéarité). "Deep" = profond = nombre de couches
empilées.

```
Machine Learning (principe général)
├── Arbres de décision, forêts aléatoires, SVM... (pas de réseaux de neurones)
└── Deep Learning (réseaux de neurones à plusieurs couches)
        └── LLM (deep learning appliqué au texte, à très grande échelle)
```

## Quand préférer un modèle simple (arbre) à du deep learning

Exemple : prédire si un employé va démissionner à partir de données
tabulaires simples (ancienneté, salaire, absences).

Deux raisons principales de préférer un arbre de décision :

1. **Interprétabilité** — un arbre montre littéralement sa logique
   ("si ancienneté < 2 ans ET absences > 5 → risque élevé"), lisible et
   justifiable par un humain (important pour une décision RH, souvent
   réglementée). Un réseau de neurones reste une boîte noire, même
   profond — ses poids ne se traduisent en aucune règle lisible.
2. **Rapport complexité/données nécessaires** — sur des données
   tabulaires simples (quelques colonnes bien définies), il n'y a pas de
   structure complexe à abstraire progressivement (pas de bords → formes
   → parties comme pour une image). Un arbre capture bien ces relations
   avec beaucoup moins de données qu'un réseau de neurones, qui a besoin
   de gros volumes pour ajuster correctement ses millions de poids.

Le deep learning brille sur des données **non structurées et complexes**
(images, texte, son) où personne ne sait dire à l'avance "quelles
caractéristiques regarder". Sur du tabulaire simple, un modèle plus
simple est souvent aussi bon, moins cher, plus rapide, et explicable —
le deep learning serait disproportionné (comme utiliser Opus effort max
pour trier des emails).

## Arbres de décision — comment ça apprend concrètement

L'algorithme ne sait pas à l'avance quel critère est pertinent — il le
**découvre** en testant statistiquement, sur les données d'entraînement,
quelle question ("ancienneté < 2 ans ?", "salaire < 30k€ ?"...) **sépare
le mieux** les catégories recherchées. Il choisit la question la plus
"pure" possible, puis répète récursivement sur chaque sous-groupe créé.

### Risque si l'arbre se subdivise sans limite

⚠️ Ce n'est **pas** de l'hallucination (concept propre aux modèles
génératifs comme les LLM — inventer un fait dans une réponse en langage
naturel ; un arbre de décision ne génère rien, il classe). C'est le
**surapprentissage (overfitting)** déjà vu avec le chat blanc/noir : un
arbre qui se subdivise jusqu'à isoler un seul exemple par feuille a
**mémorisé** chaque cas individuel plutôt qu'appris une règle générale.

Exemple : une règle ultra-spécifique du type "si ancienneté = 3,2 ans ET
salaire = 34 500€ ET absences = 4 → démission" ne généralise à aucun
nouvel employé qui ne correspond pas exactement à ce profil.

Garde-fous classiques : limiter la profondeur maximale de l'arbre, ou
exiger un nombre minimum d'exemples par feuille avant de continuer à
subdiviser.

## Forêt aléatoire (random forest) — agrégation d'avis indépendants

⚠️ Piège à éviter : ce n'est **pas** le même principe que les couches
d'un réseau de neurones. Les couches construisent une **abstraction
progressive séquentielle** (chaque étape dépend de la précédente). La
forêt aléatoire fonctionne sur un principe différent : **l'agrégation
d'avis indépendants**, en parallèle, pas en séquence.

Principe : entraîner plusieurs arbres séparément, chacun sur :
- un sous-échantillon aléatoire différent des données d'entraînement,
- souvent un sous-ensemble aléatoire différent des critères disponibles
  à chaque division.

Pour prédire : on demande l'avis de tous les arbres et on prend la
réponse majoritaire (ou la moyenne).

Analogie : un quorum d'avis d'experts (chacun n'ayant vu qu'un
sous-ensemble aléatoire des cas passés) plutôt qu'un pipeline sysadmin
séquentiel.

### Pourquoi le sous-échantillonnage différent est essentiel

Si tous les arbres voyaient exactement les mêmes données, ils
surapprendraient **de la même façon**, sur le même bruit — le vote
majoritaire ne ferait alors que confirmer l'erreur collective, sans
diversité à annuler.

En donnant à chaque arbre un sous-échantillon différent, chaque arbre
surapprend sur **un bruit différent**, propre à son propre
sous-échantillon. En agrégeant les votes, les erreurs individuelles
(variées, indépendantes) ont tendance à s'annuler mutuellement, alors
que le vrai signal sous-jacent (présent dans tous les sous-échantillons)
est renforcé par le vote — principe de la "sagesse des foules" appliqué
au ML.

## Résumé de la session

- Deep learning = sous-ensemble du ML (réseaux de neurones à plusieurs
  couches), pas un synonyme.
- Un modèle simple (arbre) peut être préférable à du deep learning pour
  l'interprétabilité et le peu de données/complexité nécessaires.
- Surapprentissage (pas hallucination) = risque d'un arbre trop profond.
- Forêt aléatoire = agrégation d'avis indépendants (parallèle), pas une
  abstraction séquentielle comme les couches de neurones — le
  sous-échantillonnage différent par arbre est ce qui permet aux erreurs
  de s'annuler au vote plutôt que de se confirmer collectivement.
