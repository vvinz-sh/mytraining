# IA — Vague 3 (MLOps/Ops) : CI/CD & pipelines MLOps

Session théorique partie d'un principe déjà vu sur Git (stockage
adressé par contenu, `reflexions-transversales.md`).

## Pourquoi Git seul ne suffit pas pour versionner un modèle

Git excelle sur le texte parce qu'il peut calculer des **diffs**
efficacement — du texte modifié partage souvent beaucoup de lignes
identiques avec la version précédente. Sur du **binaire** (un fichier
`.safetensors`, des millions de nombres), Git n'a aucun moyen de savoir
"quelles parties ont changé" de façon significative — même un
ajustement minime peut changer toute la représentation binaire.
Résultat : Git stocke le fichier **entier** à chaque commit, gonflant
l'historique de tout le poids du fichier à chaque version, même pour un
tout petit changement.

## DVC et model registries — la solution

Plutôt que de stocker le binaire complet dans Git, ces outils stockent
juste une **référence** (hash, pointeur) dans Git, et le fichier lourd
lui-même est stocké ailleurs (S3, stockage dédié) — Git garde son rôle
sur le texte/code, l'outil spécialisé gère le binaire volumineux.

### Ce qu'un vrai registre de modèles garde en plus du fichier de poids

- Le **dataset d'entraînement** utilisé (et sa version précise, pas
  juste "les données de janvier")
- Les **hyperparamètres** (learning rate, nombre d'époques — écho du
  poids unique et du gradient vu dans `hardware/13-...md`)
- Les **métriques obtenues** pour ce run précis (recall@k, accuracy...)

Permet de comparer objectivement plusieurs versions ("la version 3
est-elle meilleure que la version 2") — c'est le rôle du **tracking
d'expériences** (MLflow, Weights & Biases) : chaque run devient une
entrée traçable, pas un fichier de poids isolé sans contexte.

## Le cycle complet CI/CD MLOps

```
Monitoring détecte une régression (recall@k qui baisse,
   voir monitoring/33-monitoring-evaluation-drift-recall.md)
   → déclenche un pipeline de réentraînement automatisé
   → nouveau modèle entraîné, évalué sur le golden dataset
   → si meilleur que la version en prod : enregistré dans le model registry
   → déploiement progressif (canary/blue-green)
   → ancien modèle reste disponible en cas de rollback
```

## ⚠️ Pourquoi ce cycle ne doit jamais être 100% automatique

Les métriques (recall@k, golden dataset) sont calculées sur un
**ensemble limité et fixe** de questions — comme un LLM-juge
(`monitoring/35-...md`), elles restent un signal approximatif, jamais
une garantie parfaite de qualité réelle.

Un nouveau modèle pourrait très bien améliorer le recall@k sur le
golden dataset précis, tout en se dégradant sur des cas réels que ce
dataset ne couvre pas — le chiffre "meilleur" peut être trompeur, même
principe que la sur-confiance d'un LLM (le signal semble bon sans
garantir la justesse réelle).

**Principe à retenir** : sans validation humaine, un cycle entièrement
automatique pourrait déployer en production un modèle qui semble
meilleur sur le papier, mais qui a régressé sur des aspects que personne
n'a pensé à mesurer — même logique de vérification indépendante
appliquée depuis le début du repo (`fondamentaux/11-...md`), ici
appliquée à un pipeline automatisé plutôt qu'à une réponse de chat. Un
humain doit rester dans la boucle avant le déploiement final, même si
toutes les métriques automatiques semblent au vert.

## Résumé

1. Git n'est pas adapté au binaire volumineux (pas de diff efficace,
   stockage du fichier entier à chaque commit).
2. DVC/model registries séparent le rôle : Git pour le texte/code,
   stockage dédié pour les poids, avec juste une référence versionnée
   dans Git.
3. Un registre de modèles trace dataset + hyperparamètres + métriques,
   pas seulement le fichier de poids.
4. Le cycle monitoring → réentraînement → registre → déploiement peut
   être automatisé, mais nécessite une validation humaine avant mise en
   production — les métriques automatiques restent un signal
   approximatif, jamais une garantie absolue.
