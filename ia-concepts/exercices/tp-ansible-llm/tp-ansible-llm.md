# TP (à faire) — Interroger un LLM depuis un playbook Ansible

Statut : **prévu, pas encore réalisé**. Bon exercice croisé IA + Ansible
(module `uri` + Ansible Vault).

## Objectif pédagogique

Mettre en pratique :
- Le module `uri` (appel API, vérification `status_code`)
- La gestion de secrets via Ansible Vault (clé API jamais en clair)
- La vérification de `stop_reason` (réponse tronquée ou non) vue dans
  `ia-concepts/notes/generation-parametres/09-usage-pratique-api-ansible.md`

## Scénario

Playbook qui, après un déploiement ou une collecte de logs (ex : sortie
de `audit-rpm-services`), envoie un extrait à un LLM pour générer un
résumé humain lisible des anomalies détectées.

## Étapes envisagées

1. Stocker la clé API dans un Ansible Vault (pas en clair dans le
   playbook) — bon prétexte pour aborder Vault en pratique.
2. Construire la tâche `uri` qui envoie un extrait de log/rapport en
   `content`.
3. Vérifier `status_code` et `stop_reason`, avec `fail` conditionnel si
   problème (réponse tronquée ou erreur HTTP).
4. Écrire le résumé généré dans un fichier (`copy`/`template`) ou
   l'afficher via `debug`.
5. (Optionnel, plus avancé) Boucler sur plusieurs fichiers de logs avec
   `loop`, en respectant le rate-limit de l'API.

## Prérequis à vérifier avant de démarrer

Ce TP nécessite une vraie clé API fonctionnelle (compte avec accès API,
différent d'un abonnement claude.ai classique). Si pas disponible, on
peut adapter le TP en simulant la réponse API localement (ex : petit
serveur HTTP factice) pour se concentrer sur la mécanique Ansible pure.
