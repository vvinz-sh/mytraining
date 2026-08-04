# TP — Filebeat sur RH8103 → Logstash sur Rocky9, en mTLS (draft)

Statut : **design posé, pas encore exécuté**. Deuxième des 3 TP
pratiques du Palier 3. Contrairement aux deux TP précédents (fichier
relu après coup, ou callback JSON en TCP simple), celui-ci met en
pratique tout le panorama théorique du Palier 0 sur Beats (note 16)
et TLS/mTLS (note 18) — jusqu'ici jamais concrétisé.

## Contexte

- Filebeat déjà **installé** sur RH8103 via un rôle Ansible existant,
  simple (installation seule, à l'origine de `deployer_filebeat.log`).
  Logstash déjà installé sur Rocky de la même façon (rôle simple,
  installation seule). Les deux rôles sont **à étendre**, chacun dans
  son groupe d'inventaire — configuration de bout en bout par Ansible
  (control node WSL), pas de configuration manuelle sur les cibles
- **CA, certificats et clés déjà générés manuellement via `openssl`,
  hors Ansible** — CA locale, CSR par host, signature, EKU
  différenciés (`clientAuth` pour RH8103, `serverAuth` pour Rocky),
  conversion PKCS#8 chiffrée par passphrase. Détail complet du
  processus dans `pki-lab/README.md` (dossier séparé, à côté de ce
  draft). Ansible n'intervient qu'à
  partir de la **distribution** de ce matériel déjà produit, pas de
  sa génération
- **Protection du matériel sensible** : décision prise — la clé
  privée (`.p8`), le certificat (`.crt`) et le certificat de la CA
  (`ca.crt`) de chaque host sont stockés **en un seul bloc** dans un
  fichier Ansible Vault (`vault.yml`), exclu du dépôt via
  `.gitignore`. Pas de séparation passphrase/clé — tout le matériel
  sensible passe par le même mécanisme de protection
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

## Étape 1 — Rappel : matériel PKI déjà produit (voir annexe)

CA, certificats serveur/client et clés PKCS#8 chiffrées déjà générés
et vérifiés (en-tête `ENCRYPTED PRIVATE KEY`, correspondance modulus
clé/cert confirmée par host) avant même de commencer la partie
Ansible de ce TP. Processus documenté en annexe, pas répété ici.

Deux certificats **expirés** supplémentaires générés en parallèle
(un par host, `-startdate`/`-enddate` dans le passé) — réservés à
l'Étape 6 ("prod ready"), pas utilisés dans le déploiement nominal.

## Étape 1bis — Structure retenue pour les deux rôles

Conception posée avant d'écrire la moindre task. `ansible.cfg` fourni
avec le repo était un reliquat d'un projet plus ancien (pointait vers
`./inventory`, alors que le fichier réel est `inventory.ini`) — à
corriger avant tout run, sans rapport avec ce TP.

```
roles/filebeat/
  tasks/
    main.yml          # import_tasks: install.yml, configure.yml
    install.yml        # contenu actuel, déplacé tel quel
    configure.yml       # dépôt des certs (vault) + template filebeat.yml + notify handler
  handlers/
    main.yml           # restart filebeat
  templates/
    filebeat.yml.j2

roles/logstash/
  tasks/
    main.yml
    install.yml
    configure.yml       # dépôt des certs (vault) + template pipelines.yml + template du .conf du pipeline nommé + notify handler
    keystore.yml         # logique dédiée keystore, incluse depuis main.yml après configure.yml
  handlers/
    main.yml            # restart logstash
  templates/
    pipelines.yml.j2     # déclare uniquement le pipeline nommé "beats-tls" — pas de "main" (décision ci-dessous)
    beats-tls.conf.j2    # input beats + output
```

**Vault** : un fichier par groupe d'inventaire —
`group_vars/filebeat_hosts/vault.yml` et
`group_vars/logstash_hosts/vault.yml` — plutôt qu'un vault global
unique, cohérent avec la structure d'inventaire déjà en place. Même
mot de passe de vault sur les deux (décision de simplicité pour ce
lab, pas une exigence technique).

**`pipelines.yml` sans entrée `main`** : question posée avant de
trancher — un pipeline `main` déclaré mais sans aucun `.conf` dedans
génère-t-il une erreur au démarrage de Logstash, ou est-il toléré
silencieusement ? Sans avoir testé, décision prise par prudence :
**ne pas** garder `main`, seul `beats-tls` est déclaré. Rien d'autre
ne tourne sur Rocky pour l'instant, donc pas de perte fonctionnelle —
à revoir le jour où un deuxième pipeline nommé devient nécessaire.

**Séquence keystore (`keystore.yml`), pensée pour l'idempotence** —
`logstash-keystore add` n'est pas idempotente par défaut (échoue ou
redemande confirmation si la clé existe déjà), même problématique que
la création du keystore lui-même :
1. Vérifier la présence du fichier keystore (`stat` sur le chemin par
   défaut) → `register`
2. Créer le keystore (`logstash-keystore create`) seulement si
   l'étape 1 dit qu'il n'existe pas
3. Lister le contenu du keystore (`logstash-keystore list`) →
   `register`
4. Ajouter la clé `beat_input_ssl_key_passphrase` (valeur depuis le
   Vault, envoyée en `--stdin`) seulement si son nom n'apparaît pas
   dans le résultat de l'étape 3

## Étape 2 — Étendre le rôle Ansible existant pour configurer l'input `beats` (Rocky)

Comme pour Filebeat, le rôle Logstash actuel installe le paquet,
point final — à étendre avec les tasks de configuration : template
du `.conf` d'entrée `beats`, distribution du certificat/clé serveur
depuis le Vault, activation du service.

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

Décision prise pour la passphrase : récupérée depuis le **Logstash
Keystore** (`${beat_input_ssl_key_passphrase}`, comme évoqué en note
18) plutôt que stockée en clair dans le `.conf`. Ce choix expose
potentiellement au bug historique documenté (`ssl_key_passphrase` peu
fiable selon les versions, note 18) — à observer en le vivant plutôt
qu'en le contournant par anticipation ; si le bug se manifeste
réellement, le repli reste celui déjà documenté (clé non chiffrée +
permissions filesystem).

## Étape 3 — Étendre le rôle Ansible existant pour configurer Filebeat

Le rôle actuel installe Filebeat, point final — à étendre avec les
tasks de configuration : template `filebeat.yml` (input sur
`/var/log/messages`, output vers Logstash avec la config TLS côté
client), distribution du certificat/clé client **depuis `vault.yml`**
(variables Vault → fichiers déposés sur RH8103 via `copy`/`template`
avec contenu chiffré en amont, déchiffré seulement au moment du
déploiement grâce au vault-pass), activation + démarrage du service
avec la nouvelle config.

Question d'idempotence à se poser, dans l'esprit du reste du
programme : si `filebeat.yml` change (nouveau certificat, nouvelle
option), le rôle doit-il redémarrer Filebeat **systématiquement** à
chaque exécution, ou seulement quand la configuration a réellement
changé ? Repense au pattern `handlers`/`notify` déjà pratiqué
ailleurs dans le module Ansible — comment l'appliquer ici pour éviter
un redémarrage inutile du service à chaque `ansible-playbook`, même
quand rien n'a bougé.

**Décision prise sur le moindre privilège** : Filebeat tourne en
`root` par défaut sur le paquet Elastic (comportement du packaging,
pas une erreur de config) — comportement à **durcir** pour ce TP,
pas à accepter tel quel :

1. **User dédié** — vérifier d'abord si le paquet a déjà créé un user
   système `filebeat` (même si le service tourne en `root` par
   défaut, le user peut très bien exister sans être utilisé) ; sinon
   en créer un explicitement (`ansible.builtin.user`, système, sans
   shell de connexion)
2. **Accès en lecture à `/var/log/messages`** — pas un `chmod`/`chown`
   direct sur le fichier de log (il est réécrit/tourné par
   `logrotate`, donc toute permission posée manuellement une fois
   risque de ne pas survivre à la prochaine rotation — lien direct
   avec l'Étape 5). Deux pistes à comparer plutôt qu'à choisir à
   l'aveugle : ajouter le user `filebeat` au groupe propriétaire du
   fichier (si `rsyslog` groupe `/var/log/messages` à un groupe
   stable dans le temps), ou une ACL POSIX par défaut sur le
   **dossier** `/var/log/` (`setfacl -d`, qui s'applique aussi aux
   fichiers recréés après rotation) plutôt que sur le fichier
   lui-même
3. **Override systemd** — un drop-in
   (`/etc/systemd/system/filebeat.service.d/override.conf`, `User=`/
   `Group=`) déployé via `template` + `systemd: daemon_reload: true`,
   plutôt que de modifier le fichier `.service` fourni par le paquet
   (qui serait écrasé à la prochaine mise à jour RPM)

**SELinux volontairement hors scope ici** — reporté au module
`rhel8-rhcsa` (Domaine 9, Sécurité, module RHCSA, pas encore attaqué). Ce TP fournit
un cas concret tout trouvé pour cet exercice futur : le contexte
SELinux nécessaire pour que Filebeat lise `/var/log/messages` (et,
potentiellement, ouvre une connexion sortante vers Rocky) sera traité
là-bas, en tant qu'exercice RHCSA à part entière plutôt qu'un aparté
dans ce TP Logstash.

Point à garder en tête pour l'Étape 5 (déjà prévue) : la solution
retenue au point 2 doit être **revalidée** après un test de rotation
réelle de `/var/log/messages` — une permission qui tient au moment du
déploiement mais qui saute après le premier `logrotate` ne serait
pas vraiment "prod ready".

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
- Existence confirmée d'un user système dédié (`filebeat` sur RH8103,
  `logstash` sur Rocky, créé par le paquet à l'installation) avant de
  fixer `owner`/`group` sur les tasks de dépôt des certs — pas supposé
- Contenu du Vault (`vault.yml`) réellement cohérent avec le matériel
  PKI produit en annexe — à vérifier après déchiffrement plutôt qu'à
  supposer une simple copie/coller réussie
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

## Annexe — Petite PKI de lab

Documentée séparément dans `pki-lab/README.md` (à côté de ce draft) —
CA, CSR, signature, EKU, conversion PKCS#8, vérifications effectuées,
certs expirés pour l'Étape 6. Généré et vérifié hors Ansible, avant le
début de la partie déploiement de ce TP.
