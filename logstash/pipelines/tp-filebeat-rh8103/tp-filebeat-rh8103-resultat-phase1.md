# TP Filebeat/RH8103 → Logstash mTLS : résultat phase 1 (rôle Filebeat)

Complète `tp-filebeat-rh8103-draft.md`. Couvre uniquement le rôle
`filebeat` (RH8103), testé **sans Logstash en face** — objectif
volontairement limité à valider toute la mécanique Ansible côté
client avant d'ajouter la variable Logstash. Phase 2 (rôle
`logstash`, test de bout en bout) reste à faire.

## Résultat final validé

- Service actif, tourne bien sous le user dédié `filebeat` (pas
  `root`) — confirmé par `ps -eo user,cmd`
- Keystore Filebeat peuplé (`SSL_KEY_PASSPHRASE` présent, vérifié via
  `filebeat keystore list` en `become_user: filebeat`)
- Lecture de `/var/log/messages` opérationnelle (plus d'erreur de
  permission dans `journalctl -u filebeat`)
- Seule erreur restante, attendue : échec de connexion réseau/TLS vers
  `rocky.localdomain:5044` — normal, aucun Logstash à l'écoute côté
  serveur pour cette phase

## Bugs réels rencontrés et corrigés

**1. `template`/`copy` ne créent jamais les dossiers parents
manquants.** Le déploiement de l'override systemd
(`/etc/systemd/system/filebeat.service.d/override.conf`) échouait
avec `Destination directory ... does not exist` — le dossier
`.service.d/` n'existe pas par défaut sur une installation fraîche.
Corrigé par une task `file: state: directory` explicite avant le
`template`, plutôt que de supposer que le module la crée pour soi.

**2. `become_user` sur un user système sans `$HOME` échoue
silencieusement sur le répertoire temporaire.** Les tasks keystore
(`become_user: filebeat`, user créé avec `create_home: false`)
généraient un warning `Unable to use '/home/filebeat/.ansible/tmp'`.
Corrigé en pointant `ansible_remote_tmp` vers un dossier déjà
possédé par `filebeat` (`/var/lib/filebeat/.ansible-tmp`), plutôt que
de créer un `$HOME` artificiel juste pour Ansible.

**3. Ordre des tasks : keystore avant le déploiement de
`filebeat.yml`.** `filebeat keystore create` échouait avec
`permission denied` sur `filebeat.yml` — au moment de cette task, le
seul `filebeat.yml` présent sur le disque était encore celui du
paquet RPM (`root:root`, `0600`), pas celui du template
(`root:filebeat`, `0640`), puisque la task de dépôt du template
venait **après** dans le fichier. Première réaction (écartée après
coup) : `recurse: true` sur tout `/etc/filebeat` pour donner la
propriété à `filebeat` — jugé too much et contraire à l'approche
moindre privilège du TP (aurait aussi changé le propriétaire des
fichiers d'exemple du paquet, sans besoin réel). Correction retenue :
**réordonner les tasks**, déployer `filebeat.yml` avant les tasks
keystore plutôt que d'élargir des permissions pour contourner un
problème d'ordre.

**4. ACL `default: true` sur `/var/log/` n'est pas rétroactive.**
Après toutes les corrections précédentes, `filebeat` restait bloqué
sur `permission denied` en lisant `/var/log/messages`
(`-rw-------`, `root:root`). Diagnostiqué par `getfacl` : la default
ACL posée sur le **dossier** `/var/log/` était bien présente
(`default:user:filebeat:r--`), mais ne s'applique qu'aux fichiers
**créés après elle** — `/var/log/messages` existait depuis la
création de la VM (créé par `rsyslog`), donc jamais couvert. Corrigé
par une **deuxième** ACL, explicite cette fois, directement sur le
fichier (`ansible.posix.acl`, sans `default: true`) — les deux ACL
coexistent : celle sur le dossier couvre les futurs fichiers de
rotation, celle sur le fichier couvre l'existant.

## Décision annexe : dépréciation `INJECT_FACTS_AS_VARS`

Warning rencontré en cours de route (`INJECT_FACTS_AS_VARS default
to True is deprecated`) — `ansible_hostname` (utilisé dans
`group_vars/filebeat_hosts/main.yml` et `filebeat.yml.j2`) dépend de
ce comportement. Deux options envisagées : fixer
`inject_facts_as_vars = True` dans `ansible.cfg` (fige le
comportement actuel, mais dépend d'un réglage lui-même en transition),
ou remplacer par `ansible_facts.hostname` partout (plus verbeux, mais
ne dépend d'aucun réglage de compatibilité). **Option retenue :
`ansible_facts.hostname` partout** — appliqué dans les deux fichiers
concernés.

## Reste à faire (phase 2)

- `configure.yml` côté rôle `logstash` : dossier certs, dépôt
  cert/clé serveur depuis le vault, keystore Logstash
  (`beat_input_ssl_key_passphrase`), template `pipelines.yml` +
  `.conf` de l'input `beats` (`ssl_verify_mode: force_peer`)
- Test de bout en bout une fois les deux rôles déployés (connexion
  réelle établie, event reçu côté Logstash)
- Étapes 4 à 6 du draft (observation des champs générés, impact
  `logrotate`, exigences "prod ready" — cert expiré, permissions
  clés, retry/backoff, cohérence de version)

## Lien avec les notes existantes

`tp-filebeat-rh8103-draft.md` (design d'origine), `16-panorama-beats.md`,
`18-panorama-tls-mtls.md`, `12-pipelines-config.md` (`sincedb`,
comparé au registre Filebeat).
