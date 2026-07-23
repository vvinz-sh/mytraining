# Réflexions transversales — parallèles et TP croisés entre catégories

Notes issues d'une session de recul sur l'ensemble du repo (Ansible,
Git, RHEL8, Logstash, IA), cherchant les ponts conceptuels entre
domaines plutôt que de les traiter en silos.

## Parallèles identifiés entre les catégories

### 1. Pipelines — traitement séquentiel avec transformation à chaque étape

- **Logstash** : input → filter → output
- **Unix** : `grep | sort | uniq` (analogie utilisée pour expliquer les couches de neurones)
- **IA** : couches d'un réseau (chaque couche transforme la sortie de la précédente)
- **Ansible** : un playbook est une séquence de tâches, chacune transformant l'état du système
- **RHEL8** : le boot process (bootloader → kernel → systemd → cibles)

### 2. Parallélisme indépendant, puis combinaison des résultats

- **Multi-head attention** : plusieurs têtes en parallèle, résultats combinés
- **Forêt aléatoire** : plusieurs arbres indépendants, vote majoritaire
- **Ansible** : exécution parallèle sur plusieurs hosts (forks), résultats agrégés
- **Logstash** : plusieurs workers en parallèle avant sortie unifiée
- **Git branches** : développement parallèle, fusionné par merge

### 3. Idempotence — refaire une action ne doit rien casser

- **Ansible** : principe fondateur, relancer un playbook = même état final
- **IA (`temperature: 0`)** : même entrée → sortie quasi-identique
- **RHEL8/systemd** : redémarrer un service déjà actif ne devrait rien casser
- **Git** : un commit identique produit le même hash

### 4. Moindre privilège — même règle de sécurité partout

- **RHEL8** : permissions ugo, SELinux, ACL
- **Ansible** : comptes de service avec juste les droits sudo nécessaires
- **IA** : guardrails par moindre privilège pour un outil MCP
- **Git** : protection de branches, accès lecture seule vs écriture

### 5. Boucles avec réajustement, pas simple répétition

- **Ansible** (`until`/`retries`, ou `include_tasks`+`loop`) : retenter en changeant de stratégie
- **IA - agent** : même principe, codé dans le TP agent (fenêtre de log croissante à chaque tentative)
- **RHEL8/systemd** : `Restart=on-failure` + `RestartSec`, avec throttling ("Start request repeated too quickly", observé dans le log d'incident simulé du TP agent)

### 6. Éviter de refaire un calcul dont le résultat est déjà connu

- **Git** : stockage adressé par contenu, un blob identique jamais stocké deux fois
- **IA** : ne réindexer que les documents modifiés, ne pas recharger un modèle dont les poids ne changent pas
- **Ansible** : fact caching
- **RHEL8** : cache de pages du système de fichiers, DNS caching

### 7. Les logs comme substrat commun

Le parallèle le plus concret : RHEL8 génère des logs (journald/syslog),
Logstash existe pour les traiter, Ansible produit ses propres logs
d'exécution, et le TP agent IA a fait tourner un LLM pour analyser des
logs système — les 5 catégories se rejoignent littéralement sur cet
artefact commun.

### Fil rouge général

La plupart des principes qui semblent "propres à l'IA" (idempotence,
moindre privilège, boucles avec réajustement, éviter le recalcul) sont
en réalité des principes d'ingénierie système généraux, déjà pratiqués
côté sysadmin sans être nommés ainsi — l'IA ajoute un cerveau
statistique par-dessus la même mécanique.

## Idées de TP transverses (pistes légères, pas encore designées)

- **Logstash + RHEL8 + IA** : centraliser les logs d'une VM RHCSA vers
  Logstash, avec un filtre qui appelle l'API Claude pour classer/enrichir
  chaque événement avant stockage — prolonge le TP agent, en flux
  continu plutôt qu'à la demande.
- **Ansible + Git** : un playbook qui audite un repo (secrets oubliés
  type vault, vieux commits suspects) avant un merge — garde-fou
  automatisé façon CI.
- **RHCSA + IA** : reprendre l'esprit du TP agent, orienté audit de
  conformité système (permissions, SELinux, services actifs) plutôt que
  diagnostic d'incident — un "agent de compliance" léger.
- **Logstash + Git** : indexer l'historique Git (commits, auteurs,
  fréquence) comme des événements Logstash, pour visualiser l'activité
  d'un repo dans le temps.
- **Capstone final** : un mini SOC maison — RHEL8 génère des logs →
  Logstash centralise → un agent IA (via MCP) analyse et propose une
  remédiation → Ansible l'exécute → Git versionne la config finale
  appliquée. Objectif ambitieux à garder en tête une fois RHCSA/Ansible/
  Logstash plus avancés individuellement — synthèse de toutes les
  catégories du repo.
