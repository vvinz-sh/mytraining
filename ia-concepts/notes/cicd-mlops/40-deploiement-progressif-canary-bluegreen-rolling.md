# IA — Vague 3 (MLOps/Ops) : Déploiement progressif — canary, blue-green, rolling

Dernière session de la sous-catégorie CI/CD & pipelines MLOps — cette
checklist est maintenant complète.

## Le problème de départ

Même avec un golden dataset solide et un LLM-as-judge bien calibré
(`cicd-mlops/39-...md`), les métriques automatiques restent un signal
**approximatif** — un nouveau modèle peut sembler meilleur sur le papier
tout en régressant sur des cas réels non couverts par les tests.
Basculer 100% du trafic d'un coup expose **tous** les utilisateurs en
même temps à un problème non détecté, sans marge de réaction.

## Canary deployment

### Origine du nom

Référence aux canaris emmenés dans les mines de charbon — plus
sensibles aux gaz toxiques que les mineurs, ils montraient des signes
de détresse **avant** que le danger n'atteigne les humains, servant de
système d'alerte précoce. Les utilisateurs exposés en premier au
nouveau modèle sont appelés les "canaris" — souvent, ils ne savent
même pas qu'ils jouent ce rôle.

### Mécanisme

1. Nouveau modèle déployé sur une petite fraction du trafic (souvent
   1-5%)
2. Le reste des utilisateurs continue sur la version actuelle
3. Si les métriques sont stables/meilleures → augmentation progressive
   (5% → 20% → 50% → 100%)
4. Si dégradation détectée → rollback immédiat vers l'ancienne version,
   seule une petite fraction d'utilisateurs affectée

### Quel signal déclenche l'augmentation ou le rollback

⚠️ Piège identifié en session : les votes utilisateurs (upvote/downvote)
semblent une bonne idée pour ce rôle, mais souffrent des mêmes limites
déjà établies deux fois dans ce repo (RLHF, drift) — biais de
sélection, manque d'expertise pour juger le fond, signal bruité. Pas
adapté comme **déclencheur automatique** d'une décision de rollback qui
doit se prendre en quelques minutes.

Le bon signal : les **tests automatisés** déjà construits (golden
dataset, recall@k, faithfulness, `cicd-mlops/39-...md`) rejoués en
continu sur le trafic du canari. Les votes utilisateurs restent utiles,
mais en signal **complémentaire à plus long terme** (tendances sur
plusieurs semaines), pas comme critère de décision immédiate.

### Bien choisir les canaris (précision de l'article Liora)

Les canaris doivent être à la fois **tolérants aux bugs** (réduit
l'insatisfaction) et **capables de les détecter/remonter** (améliore le
produit via leurs retours). D'où la pratique courante de déployer
d'abord en interne, ou auprès de groupes d'utilisateurs opt-in
volontaires, avant le grand public.

### Avantage clé — pas d'infrastructure dupliquée

Contrairement au rolling et au blue-green (voir plus bas), le canary ne
nécessite **pas** une deuxième infrastructure complète — le test se
fait auprès d'un groupe d'utilisateurs, pas sur un serveur/une instance
séparée. Particulièrement adapté pour des organisations sans moyens
d'héberger deux versions complètes en parallèle.

### Limite

Malgré le canary, certains bugs peuvent encore passer à travers avant
la mise en production complète — une vérification supplémentaire reste
nécessaire avant le déploiement à 100%, le canary réduit le risque
mais ne l'élimine pas totalement (écho direct de la nature
probabiliste des tests ML déjà établie).

## Blue-green deployment

### Mécanisme

Deux environnements identiques : **bleu** (version actuelle en
production) et **vert** (nouvelle version, prête et testée en
parallèle). Bascule de **tout** le trafic d'un coup, de bleu vers vert.

### Pourquoi un rollback quasi instantané

L'ancienne version (bleu) reste **entièrement intacte et disponible**
pendant toute la bascule — jamais désactivée. Un rollback consiste
juste à rediriger le routing vers bleu à nouveau, une opération quasi
instantanée. Avec le canary, revenir en arrière veut dire redescendre
progressivement le pourcentage de trafic, plus lent à gérer proprement.

### Contrepartie

Nécessite de maintenir **deux infrastructures complètes** en parallèle
— coût d'hébergement doublé pendant la phase de transition,
contrairement au canary.

## Rolling deployment — la 3e stratégie (non couverte initialement)

Point complémentaire de l'article Liora, absent de notre discussion
initiale : le **rolling deployment** échelonne aussi les modifications,
mais au niveau des **serveurs/instances**, pas des utilisateurs comme le
canary. Chaque serveur est mis à jour un par un (ou par petits groupes),
progressivement, jusqu'à couverture complète de l'infrastructure.

Différence clé avec le canary : le rolling ne cible pas un sous-groupe
d'utilisateurs spécifique — n'importe quel utilisateur peut atterrir
sur un serveur mis à jour ou non, selon le load balancer, de façon
aléatoire plutôt que contrôlée.

## Tableau comparatif des 3 stratégies

| Stratégie | Granularité | Infra dupliquée nécessaire | Rollback | Détection avant impact large |
|---|---|---|---|---|
| Canary | Sous-groupe d'utilisateurs ciblé | Non | Progressif (redescendre le %) | Oui, contrôlée |
| Rolling | Serveurs/instances | Oui (transitoire) | Progressif (redéployer l'ancienne version serveur par serveur) | Partielle, non ciblée |
| Blue-green | Tout le trafic d'un coup | Oui (deux environnements complets) | Quasi instantané (re-router) | Non, tout ou rien |

## Résumé

1. Aucun déploiement de modèle ne devrait basculer 100% du trafic d'un
   coup, même après validation complète des tests automatisés — les
   métriques restent probabilistes.
2. Canary = risque limité à un sous-groupe, sans infra dupliquée, mais
   rollback plus progressif.
3. Blue-green = rollback quasi instantané, mais infra doublée et
   aucune détection avant bascule complète.
4. Rolling = alternative par serveurs plutôt que par utilisateurs, sans
   ciblage précis d'un groupe de test.
5. Le déclencheur de décision (augmenter le trafic ou rollback) doit
   être un signal objectif et automatisé (tests ML), jamais les votes
   utilisateurs seuls — trop bruités pour une décision aussi rapide et
   critique.

## Ressource externe

[Déploiement Canary pour les DevOps : en quoi ça consiste ? (Liora)](https://liora.io/canary-devops-tout-savoir)
— bon complément généraliste DevOps (pas spécifique IA), source du
rolling deployment et de la nuance sur l'infrastructure non dupliquée
propre au canary.
