# mytraining

Repo de formation personnelle — notes, exercices et suivi de progression.

Vault Obsidian : ouvrir ce dossier directement comme vault (plugin **Obsidian Git** recommandé pour committer les notes automatiquement).

## Technos suivies

| Techno | Niveau visé | Format | Détail |
|---|---|---|---|
| RHEL 8 | Avancé — programme complet RHCSA (EX200) | notes/ + exercices/ | ci-dessous |
| Ansible | Intermédiaire — rôles, Vault, structure de projet | notes/ + roles/ | ci-dessous |
| Git | Débutant | notes/ | ci-dessous |
| Logstash | Débutant | notes/ + pipelines/ | ci-dessous |
| IA (concepts + pratique) | Vague 1 et 2 terminées, vague 3 (MLOps/Ops) en préparation | notes/ + exercices/ | voir ia-concepts/README.md |

## Suivi de progression — RHCSA (EX200)

- [x] 1. Comprendre et utiliser les outils essentiels
- [ ] 2. Créer des scripts shell simples
- [ ] 3. Faire fonctionner des systèmes (boot, systemd, processus)
- [ ] 4. Configurer le stockage local (partitions, LVM, swap)
- [ ] 5. Créer et configurer des systèmes de fichiers
- [ ] 6. Déployer, configurer et maintenir des systèmes
- [ ] 7. Gérer les réseaux de base
- [ ] 8. Gérer les utilisateurs et groupes
- [ ] 9. Gérer la sécurité (permissions, ACL, SELinux, firewalld)
- [ ] 10. Gérer les conteneurs (Podman)

## Suivi de progression — Git

- [x] Zone de staging (add / commit / diff / status)
- [ ] Branches : create, switch, merge
- [ ] Remotes : clone, push, pull, fetch
- [ ] Résolution de conflits
- [ ] Rebase vs merge
- [x] Purger un fichier de tout l'historique (git filter-repo) — module hors-série, git/notes/03-purge-historique-filter-repo.md

## Suivi de progression — Logstash

- [ ] Architecture (input / filter / output)
- [ ] Premier pipeline simple
- [ ] Filtres grok
- [ ] Sortie vers Elasticsearch

## Suivi de progression — Ansible

- [ ] Structure d'un rôle
- [ ] Inventaires et variables
- [ ] Ansible Vault
- [ ] Idempotence et handlers
- [ ] Tags et includes

## IA — suivi détaillé

Le détail complet (vague 1 base, vague 2 approfondissement, vague 3
MLOps/Ops, hors-programme, TP réalisés/en réserve, ressources externes)
est maintenant dans ia-concepts/README.md, pour garder ce fichier
racine lisible à mesure que le module IA continue de grossir.

En bref :
- Vague 1 (base) — terminée
- Vague 2 (approfondissement : paramètres, hardware, écosystème) — terminée
- Vague 3 (MLOps/Ops : déploiement, monitoring, CI/CD, gouvernance, data engineering) — en préparation
- 4 TP réalisés avec succès, 2 en réserve
