# TP — Contexte SELinux pour Filebeat (lecture `/var/log/messages`, connexion sortante) (draft)

Statut : **design posé, pas encore exécuté**. Premier TP concret du
Domaine 9 (Sécurité). Dépend directement du TP `tp-filebeat-rh8103`
du module `logstash` — à mener une fois que Filebeat y tourne sous un
user dédié non-root (override systemd), avec les permissions Unix
déjà réglées (ACL POSIX sur `/var/log/`).

## Contexte

Deux surfaces à vérifier, pas une seule :
1. **Lecture** de `/var/log/messages` par le nouveau process Filebeat
   non-root
2. **Connexion sortante** vers Rocky (port 5044, TCP) depuis ce même
   process — une policy SELinux peut bloquer une connexion réseau
   sortante indépendamment de tout problème de lecture de fichier

## Étape 1 — Confirmer que SELinux est bien en cause avant d'agir

Ne pas supposer que SELinux bloque quoi que ce soit avant de l'avoir
constaté. Deux vérifications préalables :
```
getenforce
```
(confirmer le mode `Enforcing`, pas `Permissive`/`Disabled` — sinon
SELinux n'est structurellement responsable de rien ici, même en
présence d'un échec).
```
ps -eZ | grep filebeat
```
Identifier le **domaine SELinux** (`_t` à la fin du contexte) sous
lequel le process tourne réellement après le passage à l'override
systemd. Question ouverte : ce domaine est-il un domaine confiné avec
une policy dédiée, ou `unconfined_service_t` (cas fréquent pour un
daemon tiers sans policy SELinux fournie par son éditeur) ? Dans ce
second cas, SELinux ne bloque probablement **rien** — le travail des
étapes suivantes serait alors inutile, à vérifier avant de s'y lancer.

## Étape 2 — Si un blocage existe, le diagnostiquer par les logs, pas par supposition

```
ausearch -m avc -ts recent
```
ou
```
journalctl -t setroubleshoot --since "10 min ago"
```
Chercher un événement `AVC denied` correspondant à la lecture de
`/var/log/messages` ou à la connexion sortante port 5044 — le message
d'audit précise le type source (domaine du process) et le type cible
(contexte du fichier/port concerné), base pour la correction plutôt
que de deviner une commande `setsebool`/`semanage` au hasard.

## Étape 3 — Corriger, avec l'outil adapté au type de blocage constaté

Ne pas présumer laquelle de ces pistes s'applique avant l'étape 2 :
- **Fichier** : le contexte de `/var/log/messages` (`var_log_t`,
  attendu par défaut) est-il correct, ou a-t-il dérivé ? (`ls -Z`,
  `restorecon` si besoin)
- **Réseau** : un booléen SELinux existant couvre-t-il ce cas
  (`getsebool -a | grep -i <mot-clé pertinent>`), ou faut-il déclarer
  le port 5044 comme autorisé pour ce type de connexion sortante
  (`semanage port`) ?
- **Policy** : si le domaine du process est confiné mais qu'aucun
  booléen existant ne couvre le besoin, generer un module de policy
  minimal à partir du contexte réel de l'AVC (`audit2allow`) plutôt
  que d'ouvrir largement les permissions du domaine

## Ce qu'il faudra vérifier/clarifier en exécutant

- Mode SELinux réel sur RH8103 avant toute autre étape
- Domaine SELinux réel du process Filebeat après l'override systemd
  (confiné ou `unconfined_service_t`)
- Présence ou non d'un AVC réel pour chacune des deux surfaces
  (lecture fichier, connexion sortante) — possible qu'une seule pose
  problème et pas l'autre
- Adapter la correction au type de blocage réellement observé, pas à
  une liste de commandes appliquées par précaution

## Compétences pratiquées

- Diagnostic SELinux méthodique (mode, domaine, AVC) avant toute
  correction, plutôt que des commandes `setsebool`/`semanage`
  appliquées à l'aveugle
- Distinction entre un blocage SELinux réel et une fausse piste
  (process en domaine `unconfined`, permissions Unix insuffisantes
  déguisées en "problème SELinux")
- Premier contact concret avec les outils du Domaine 9 RHCSA
  (`getenforce`, `ausearch`, `semanage`, `audit2allow`)

## Lien avec les notes existantes

`02-domaine9-selinux-amorce.md` (origine du pont, contexte),
`01-domaine1-outils-essentiels.md` (ACL, recoupe le même domaine).
Module `logstash`, `tp-filebeat-rh8103-draft.md` (Étape 3 — moindre
privilège, override systemd, point de départ de ce TP).
