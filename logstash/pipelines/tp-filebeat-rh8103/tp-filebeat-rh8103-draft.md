# TP — Filebeat sur RH8103 → Logstash sur Rocky9, en mTLS (draft)

Statut : **design posé, pas encore exécuté**. Deuxième des 3 TP
pratiques du Palier 3. Contrairement aux deux TP précédents (fichier
relu après coup, ou callback JSON en TCP simple), celui-ci met en
pratique tout le panorama théorique du Palier 0 sur Beats (note 16)
et TLS/mTLS (note 18) — jusqu'ici jamais concrétisé.

## Contexte

- Filebeat déjà **installé** sur RH8103 via un rôle Ansible existant,
  simple (installation seule, à l'origine de `deployer_filebeat.log`)
  — mais ce rôle ne **configure** pas encore Filebeat. Ce TP consiste
  à **étendre ce rôle existant**, pas à configurer `filebeat.yml` à
  la main sur RH8103 : déploiement et configuration passent par
  Ansible de bout en bout (control node WSL, cible RH8103), cohérent
  avec le reste du programme
- Log source : `/var/log/messages` (vrai log système, pas un fichier
  synthétique) sur RH8103
- Destination : Logstash sur Rocky9, input `beats`
- **mTLS dès le premier passage** — pas de TCP en clair d'abord.
  Authentification dans les deux sens : Logstash vérifie le certificat
  client de Filebeat, Filebeat vérifie le certificat serveur de
  Logstash
- Fiabilité : queue par défaut (mémoire) assumée pour ce TP — le
  `queue.type: persisted` et la Dead Letter Queue sont prévus au TP
  dédié du Palier 4, pas ici

Question de conception à trancher avant d'écrire la moindre task :
où les certificats/clés sont-ils **générés** (sur le control node
WSL, directement sur les cibles via un module Ansible, ou en dehors
d'Ansible puis distribués) — et comment le matériel sensible (clé
privée, passphrase) est-il **transporté et protégé** une fois généré ?
Le module Ansible du programme a déjà introduit **Vault** — est-ce le
bon outil ici pour chiffrer la passphrase (ou la clé elle-même) dans
le rôle, plutôt que de la faire transiter en clair via une variable
Ansible ordinaire ?

## Étape 1 — Générer les certificats (CA, serveur, client)

Trois éléments : une autorité (CA) locale au lab, un certificat
serveur pour Rocky (Logstash), un certificat client pour RH8103
(Filebeat) — tous deux signés par la même CA, condition nécessaire
pour que la vérification mutuelle fonctionne.

Point de vigilance direct depuis la note 18 : la clé doit être au
format **PKCS#8**, pas PKCS#1 — à vérifier explicitement selon la
commande `openssl` utilisée pour générer chaque clé (certaines
génèrent du PKCS#1 par défaut, conversion nécessaire sinon).

Décision prise : la clé privée serveur sera **chiffrée par
passphrase**, celle-ci récupérée depuis le **Logstash Keystore**
(`${beat_input_ssl_key_passphrase}`, comme évoqué en note 18) plutôt
que stockée en clair dans le `.conf`. Ce choix expose potentiellement
au bug historique documenté (`ssl_key_passphrase` peu fiable selon les
versions, note 18) — à observer en le vivant plutôt qu'en le
contournant par anticipation ; si le bug se manifeste réellement, le
repli reste celui déjà documenté (clé non chiffrée + permissions
filesystem).

## Étape 2 — Configurer l'input `beats` côté Logstash (Rocky)

```
input {
  beats {
    port => 5044
    ssl_enabled => true
    ssl_certificate => "/chemin/vers/cert-serveur.crt"
    ssl_key => "/chemin/vers/cle-serveur.pkcs8.key"
    ssl_certificate_authorities => ["/chemin/vers/ca.crt"]
    ssl_verify_mode => "force_peer"
  }
}
```
`ssl_verify_mode => "force_peer"` est ce qui transforme un TLS simple
en **mTLS** — sans lui, Logstash chiffre la connexion mais n'exige pas
de certificat client. Point à vérifier : le port 5044 doit être
ouvert côté firewalld sur Rocky, sans quoi la connexion échouera
silencieusement côté réseau, avant même d'atteindre la couche TLS.

## Étape 3 — Étendre le rôle Ansible existant pour configurer Filebeat

Le rôle actuel installe Filebeat, point final — à étendre avec les
tasks de configuration : template `filebeat.yml` (input sur
`/var/log/messages`, output vers Logstash avec la config TLS côté
client), distribution des certificats/clé client, activation +
démarrage du service avec la nouvelle config.

Question d'idempotence à se poser, dans l'esprit du reste du
programme : si `filebeat.yml` change (nouveau certificat, nouvelle
option), le rôle doit-il redémarrer Filebeat **systématiquement** à
chaque exécution, ou seulement quand la configuration a réellement
changé ? Repense au pattern `handlers`/`notify` déjà pratiqué
ailleurs dans le module Ansible — comment l'appliquer ici pour éviter
un redémarrage inutile du service à chaque `ansible-playbook`, même
quand rien n'a bougé.

Point de moindre privilège à vérifier, cohérent avec la philosophie
du programme : sous quel utilisateur tourne le process Filebeat, et
cet utilisateur a-t-il réellement les droits de lecture sur
`/var/log/messages` (souvent restreint au groupe `adm`/`root` selon
la distribution) ? À vérifier plutôt qu'à supposer que ça fonctionne
d'office.

## Étape 4 — Test et observation des champs générés

Générer une entrée contrôlée dans `/var/log/messages` (`logger
"message de test"`, par exemple) et vérifier sa réception côté
Logstash (sortie `stdout`/`file`, sans filtre pour ce premier test).

Ne pas présupposer la structure des champs reçus — Filebeat, à la
différence de nos `input file` bruts jusqu'ici, ajoute ses propres
métadonnées automatiquement (agent, host, type d'input...). À observer
sur un vrai event reçu plutôt qu'à deviner les noms de champs à
l'avance.

## Étape 5 — Impact de `logrotate` sur `/var/log/messages`

Jamais abordé jusqu'ici dans le module. Question de fond avant de
chercher une solution toute faite : `logrotate` sur RH8103 tourne
selon quel mécanisme de rotation — renommage + création d'un nouveau
fichier (`create`), ou troncature du fichier en place
(`copytruncate`) ? La réponse conditionne tout le reste : Filebeat
suit un fichier par son **inode**, pas par son nom — un renommage ne
le perturbe donc pas en principe (il continue de lire l'ancien inode
jusqu'à épuisement, puis bascule sur le nouveau fichier créé). Une
troncature en place, en revanche, change le contenu sans changer
l'inode — à vérifier concrètement si Filebeat gère ça proprement ou
si des lignes se retrouvent perdues/dupliquées.

À observer en pratique plutôt qu'à résoudre sur le papier : configurer
(ou déclencher manuellement) une rotation de `/var/log/messages`
pendant que Filebeat tourne, et constater ce qui arrive réellement
côté Logstash — perte de lignes, doublons, ou transition propre.

## Autres pièges potentiels à explorer (liste ouverte, pas résolue à l'avance)

- **Registre Filebeat** (position de lecture persistée sur disque,
  équivalent du `sincedb` de Logstash, note 12) — que devient-il en
  cas de redémarrage du service Filebeat pendant une rotation en
  cours ?
- **Contexte SELinux** sur RH8103 (RHEL8, SELinux actif par défaut) —
  Filebeat a-t-il besoin d'un contexte spécifique pour lire
  `/var/log/messages` ou pour ouvrir une connexion sortante vers
  Rocky ?
- **Double ingestion au redémarrage** — si le registre n'est pas à
  jour au moment d'un redémarrage de Filebeat, un même log peut-il
  être réexpédié une deuxième fois ?

Ces points sont volontairement listés sans réponse préétablie — à
vérifier un par un pendant l'exécution du TP, pas à anticiper ici.

## Étape 6 — Exigences "prod ready" au-delà de la queue/DLQ

Le TP vise un niveau proche de la production, pas juste "ça marche
une fois" — la queue persisted/DLQ reste au Palier 4, mais plusieurs
autres exigences relèvent bien de ce TP :

**Cycle de vie du certificat** — générer volontairement un
certificat à validité très courte (1 jour, voire quelques minutes)
et observer le comportement réel de Logstash/Filebeat à
l'expiration : refus de connexion explicite, message d'erreur
clair, ou silence total sans rien dans les logs ? Un pipeline
"prod ready" doit avoir un comportement d'échec **connu et
documenté**, pas seulement un chemin nominal qui fonctionne.

**Permissions sur le matériel cryptographique** — même principe de
moindre privilège déjà appliqué à `git-push-perso`/`mcp-git` : qui
peut lire la clé privée serveur (Rocky) et la clé privée client
(RH8103) au repos sur disque ? À vérifier et resserrer explicitement,
pas à laisser aux permissions par défaut de la commande qui les a
générées.

**Retry/backoff côté Filebeat** — distinct de la queue
persisted/DLQ (Palier 4, côté Logstash) : les réglages propres à
`output.logstash` (`bulk_max_size`, `timeout`, nombre de tentatives)
qui déterminent comment Filebeat réagit **lui-même** à une coupure
réseau, avant même que la question d'une queue Logstash ne se pose.
Bonne passe préparatoire pour le futur TP Palier 4.

**Cohérence de version Filebeat/Logstash** — les deux tournent en
8.19.x dans le lab, donc pas de vrai risque ici, mais à décrire
*pourquoi* ça compte quand on exécutera le TP (protocole Beats
versionné entre les deux composants), plutôt que de bénéficier d'une
coïncidence de version sans en comprendre l'enjeu.

## Ce qu'il faudra vérifier/clarifier en exécutant

- Format PKCS#8 réellement obtenu selon la commande de génération
  utilisée (à vérifier, pas à supposer)
- Bug `ssl_key_passphrase` : reproductible ou pas sur la version de
  Logstash du lab — décision à prendre après test, pas avant
- Port 5044 libre et ouvert côté firewalld sur Rocky
- Utilisateur d'exécution de Filebeat et ses droits réels sur
  `/var/log/messages`
- Structure exacte des champs ajoutés par Filebeat (à observer sur un
  vrai event, sans préjuger du nommage)
- Mécanisme de rotation réel de `logrotate` sur `/var/log/messages`
  (`create` vs `copytruncate`) et comportement effectif de Filebeat
  face à une rotation en cours d'exécution
- Comportement du registre Filebeat en cas de redémarrage du service
  pendant/après une rotation (perte, doublon, ou reprise propre)
- Comportement exact à l'expiration d'un certificat de test à
  validité volontairement courte
- Permissions réelles sur les clés privées (serveur et client) après
  génération, avant tout resserrement
- Où et comment les certificats/clés sont générés et transportés vers
  RH8103 via Ansible, et si Vault est effectivement le bon outil pour
  protéger la passphrase/clé dans le rôle
- Comportement du rôle étendu à la ré-exécution : redémarre-t-il
  Filebeat uniquement quand la config change (via `handlers`), ou
  systématiquement

## Compétences pratiquées

- Mise en pratique du panorama Beats (note 16) et TLS/mTLS (note 18),
  jusqu'ici uniquement théoriques
- Génération et vérification d'une chaîne de certificats (CA, serveur,
  client) au bon format
- Diagnostic d'un problème réseau (port fermé) vs un problème TLS
  (certificat refusé) — deux couches d'échec différentes à distinguer
- Application du principe de moindre privilège à un service réel
  (droits de lecture de Filebeat sur un log système)
- Diagnostic du comportement d'un shipper de logs face à une rotation
  de fichier en cours d'exécution — mécanisme jamais abordé dans le
  module jusqu'ici
- Test délibéré d'un scénario d'échec (certificat expiré) pour
  documenter un comportement de panne plutôt que de ne valider que le
  chemin nominal
- Distinction entre fiabilité côté client (retry/backoff Filebeat) et
  fiabilité côté serveur (queue Logstash, Palier 4) — deux couches
  différentes du même problème de résilience
- Extension d'un rôle Ansible existant (installation seule → 
  installation + configuration complète), avec gestion de
  l'idempotence via `handlers`/`notify` pour éviter un redémarrage
  systématique du service
- Protection du matériel sensible (clé privée, passphrase) dans un
  rôle Ansible — probable réutilisation de Vault, déjà pratiqué
  ailleurs dans le module Ansible

## Lien avec les notes existantes

`16-panorama-beats.md` (triptyque de fiabilité, contre-pression —
queue persisted repoussée au Palier 4 ici), `18-panorama-tls-mtls.md`
(PKCS#8, bug `ssl_key_passphrase`, contournement recommandé),
`12-pipelines-config.md` (`sincedb`, comparé au mécanisme de reprise
de position de Filebeat).
