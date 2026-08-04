# Domaine 9 — Sécurité (SELinux, ACL) : amorce

Statut : **pas commencé**, ce module reste très jeune (seul le
Domaine 1 a été traité jusqu'ici). Cette note existe pour fixer un
point de départ concret plutôt que d'aborder SELinux dans l'abstrait
— déjà repéré comme sujet du Domaine 9 dans les "à revoir" du
Domaine 1 (ACL, `setfacl`/`getfacl`), qui recoupe le même domaine.

## Origine du pont — module Logstash, TP `tp-filebeat-rh8103`

En durcissant le TP Filebeat/mTLS du module Logstash (faire tourner
Filebeat sous un user dédié non-root plutôt qu'en `root` par défaut),
la question de l'accès en lecture à `/var/log/messages` a fait
apparaître SELinux comme un sujet à part entière, volontairement
écarté de ce TP pour ne pas le complexifier hors de son scope
d'origine. Reporté ici, comme premier cas concret du Domaine 9,
plutôt qu'un exercice SELinux abstrait sans terrain réel.

## Ce que le TP `tp-filebeat-rh8103` a besoin de résoudre

Une fois Filebeat basculé sur un user dédié (via un override
systemd), avec un accès en lecture accordé côté permissions Unix
classiques (ACL POSIX sur `/var/log/`) : SELinux, actif par défaut
sur RHEL8 en mode `enforcing`, bloque-t-il malgré tout ce nouveau
process non-root, indépendamment des permissions Unix déjà réglées ?

Question à ne pas trancher sur le papier : la réponse dépend du
**domaine SELinux** sous lequel le process Filebeat tourne une fois
lancé via l'override systemd — un service qui hérite d'un domaine
confiné se heurtera aux règles de la policy même avec des permissions
Unix parfaitement correctes ; un service qui tourne en domaine
`unconfined` (cas fréquent pour des daemons tiers sans policy SELinux
dédiée fournie par leur éditeur) ne sera, lui, pas concerné du tout —
à vérifier avant de supposer qu'un travail SELinux est même
nécessaire.

## Lien avec les notes existantes

`01-domaine1-outils-essentiels.md` (ACL déjà repérées comme
recoupant le Domaine 9). Module `logstash`,
`tp-filebeat-rh8103-draft.md` (origine du pont, Étape 3 — moindre
privilège, override systemd).
