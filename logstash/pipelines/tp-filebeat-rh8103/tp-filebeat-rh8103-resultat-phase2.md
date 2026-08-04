# TP Filebeat/RH8103 → Logstash mTLS : résultat phase 2 (rôle Logstash + bout en bout)

Complète `tp-filebeat-rh8103-resultat-phase1.md`. Couvre le rôle
`logstash` (Rocky), et la validation complète du flux mTLS de bout en
bout — les deux hôtes déployés, connectés, un vrai event reçu.

## Résultat final validé

- `systemctl status logstash` actif, `LOGSTASH_KEYSTORE_PASS` transmis
  au daemon via `/etc/sysconfig/logstash` (`EnvironmentFile`) —
  **confirmé après un redémarrage complet de la VM** (`enable` +
  reboot), pas seulement un `systemctl restart` : le doute soulevé en
  phase 1 (ticket GitHub sur la fiabilité d'`EnvironmentFile` selon
  les versions) est levé, le mécanisme fonctionne bien sur 8.19.x
- Keystore Logstash peuplé (`beat_input_ssl_key_passphrase`)
- Port 5044/tcp ouvert côté firewalld (`public`, `permanent` +
  `immediate`)
- Event réel reçu de bout en bout : ligne `logger` générée sur RH8103,
  visible intacte côté Logstash (`event.original`/`message`
  identiques), avec les champs ECS natifs de Filebeat
  (`agent.*`, `host.*`, `log.file.*`, `ecs.version`, `input.type`) —
  jamais deviné à l'avance, observé tel quel comme prévu à l'Étape 4
  du draft

## Bugs réels rencontrés et corrigés

**1. Trois emplacements différents pour le même keystore, jamais
alignés au départ.** `logstash-keystore` sans `--path.settings`
cherche par défaut dans `$LS_HOME/config`
(`/usr/share/logstash/config/`) — pas `/etc/logstash/`, contrairement
à ce que la task `stat` supposait. Le daemon systemd, lui, démarre
avec `--path.settings /etc/logstash` (fixé dans l'unit du paquet).
Résultat : la task `stat`, les commandes `logstash-keystore`, et le
daemon réel regardaient potentiellement **trois chemins différents**
avant correction — le keystore créé par les tasks Ansible n'était
jamais celui que le daemon allait chercher. Corrigé en ajoutant
`--path.settings /etc/logstash` explicitement aux 3 commandes
(`create`, `list`, `add`).

**2. Dossier `$LS_HOME/config` manquant au moment du premier
`keystore create`.** Avant la correction du point 1, la task plantait
aussi parce que `/usr/share/logstash/config/` (l'emplacement par
défaut sans `--path.settings`) n'existait pas encore. Devenu sans
objet une fois le chemin explicite fixé (`/etc/logstash` existe déjà,
créé par le paquet).

**3. `Password is not ASCII` — fausse piste écartée.** Le tout premier
keystore créé au mauvais endroit (point 1) donnait cette erreur
d'intégrité en le relisant — d'abord suspecté comme un caractère non
souhaité dans la passphrase vaultée. En réalité, une fois le bon
`--path.settings` en place et un keystore recréé proprement au bon
endroit, plus aucune trace de cette erreur — c'était un keystore
corrompu/mal formé issu du point 1, pas un problème de contenu de la
passphrase.

**4. `--force` : option qui n'existe pas sur `logstash-keystore
add`.** Task "ajouter la passphrase" passant en `ok` sans erreur
visible, mais keystore réellement vide ensuite (`list` ne montrant
rien) — le run en mode verbose a révélé `Unrecognized option
'--force'`, une erreur silencieusement absorbée par le pipe
`echo | logstash-keystore` en mode normal (code de sortie non
significatif remonté malgré l'option invalide). Retiré purement et
simplement — inutile de toute façon, le `when` sur le contenu de
`list` assure déjà l'idempotence à lui seul, contrairement à
l'hypothèse initiale ("ceinture et bretelles").

## Décision confirmée : `EnvironmentFile` fonctionne sur 8.19.x

Le doute soulevé avant d'écrire les tasks (ticket GitHub signalant
que les variables d'`/etc/sysconfig/logstash` ne sont pas toujours
honorées selon la version) est tranché empiriquement : ça fonctionne,
vérifié après un redémarrage complet de la VM, pas juste un restart à
chaud du service.

## Reste à faire

- Étape 5 du draft : impact `logrotate` sur `/var/log/messages`
  (test de rotation en cours d'exécution)
- Étape 6 : certificat expiré (comportement d'échec documenté),
  permissions resserrées sur les clés privées au repos, retry/backoff
  `output.logstash`
- Remplacer le `filter {}` vide et l'`output stdout` par une vraie
  destination une fois le test brut confirmé stable

## Lien avec les notes existantes

`tp-filebeat-rh8103-resultat-phase1.md` (rôle Filebeat, phase 1),
`tp-filebeat-rh8103-draft.md` (design d'origine), `16-panorama-beats.md`,
`18-panorama-tls-mtls.md`, `28-codec-filtre-json-approfondi.md`
(champs ECS observés sans les deviner, même principe que les
structures imbriquées du codec `json`).
