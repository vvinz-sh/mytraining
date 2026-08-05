# TP Filebeat/RH8103 → Logstash mTLS : résultat phase 4 (Étape 6 — clôture du TP)

Complète `tp-filebeat-rh8103-resultat-phase3.md`. Couvre les 4 points
de l'Étape 6 du draft : cycle de vie du certificat, permissions sur
le matériel cryptographique, retry/backoff côté Filebeat, cohérence
de version Filebeat/Logstash. Dernière phase du TP.

Note: On commence par décrire les points 1 et 3 (respectivement certificats et mécanisme de backoff/retry)
qui se rejoignent naturellement. Viennent ensuite les points 2 et 4.

## Point 1 — Cycle de vie du certificat

Deux tests menés séparément, cert client restauré entre les deux
(via un tag Ansible dédié sur les tasks de dépôt des certs, pour
basculer nominal/expiré sans polluer durablement le rôle — seule
trace résiduelle : temporaire dans le vault).

### Test 1 — Certificat client (RH8103) expiré

**Côté Logstash** (qui effectue la vérification du cert client,
`ssl_verify_mode: force_peer`) : diagnostic exact et immédiat, via
une exception Java complète :
```
Caused by: java.security.cert.CertificateExpiredException: NotAfter: Tue Jan 02 01:00:00 CET 2024
```
Service **resté actif** — `BeatsHandler` gère l'exception connexion
par connexion, pas de crash global ; seule cette tentative précise
est rejetée.

**Côté Filebeat** (rejeté) : message **générique**, sans le motif
exact :
```
Failed to publish events caused by: remote error: tls: unknown certificate
```
Reconnexions automatiques visibles en boucle (`Connecting to
backoff(...)` / `established` / échec), sans configuration
particulière de notre part.

### Test 2 — Certificat serveur (Rocky) expiré

**Côté Filebeat** (qui effectue cette fois la vérification, côté
client TLS) : diagnostic exact et précis, directement dans ses
propres logs :
```
Failed to connect to backoff(async(tcp://rocky.localdomain:5044)): x509: certificate has expired or is not yet valid: current time 2026-08-05T17:25:07+02:00 is after 2024-01-02T00:00:00Z
```

**Côté Logstash** (rejeté) : message générique, sans le motif exact :
```
io.netty.handler.codec.DecoderException: javax.net.ssl.SSLHandshakeException: (bad_certificate) Received fatal alert: bad_certificate
```

### Règle générale dégagée des deux tests

**Celui qui effectue la vérification TLS obtient toujours le
diagnostic précis dans ses propres logs ; celui qui se fait rejeter
ne reçoit qu'une alerte TLS générique**, sans connaître la cause
exacte (expiré ? mauvaise CA ? révoqué ?) sans aller consulter les
logs de l'autre partie. Symétrique et cohérent sur les deux tests :
Logstash vérifie le client (test 1) → Logstash a le détail, Filebeat
non ; Filebeat vérifie le serveur (test 2) → Filebeat a le détail,
Logstash non.

### Aucune perte pendant les deux fenêtres d'échec

Dans les deux tests, les lignes générées via `logger` pendant que la
connexion échouait sont réapparues côté Kibana une fois le cert
restauré — aucune perte, juste un délai. Cohérent avec le principe
"at-least-once" déjà validé en phase 3 (Étape 5), cette fois côté
**publication** plutôt que lecture de fichier : tant que Filebeat n'a
pas reçu de confirmation, les events restent en attente dans sa queue
interne plutôt que d'être abandonnés.

## Point 3 — Retry/backoff côté Filebeat

Pas besoin de test dédié — le comportement de reconnexion observé
dans le Test 2 du point 1 (certificat serveur expiré, sur ~4 minutes,
10 tentatives numérotées) donne déjà la donnée empirique recherchée.

**Réglages par défaut confirmés** (doc officielle, rien de configuré
explicitement dans ce rôle) : `backoff.init: 1s`, `backoff.max: 60s`
— doublement exponentiel plafonné (`1 → 2 → 4 → 8 → 16 → 32 → 60`,
puis stabilisation au plafond).

**Intervalles réellement mesurés** entre tentatives successives :
~2,4s → 5,1s → 12,8s → 26,2s → 41,1s → 49s → puis stabilisation
autour de 30-40s. Progression cohérente avec le doublement théorique,
écart normal expliqué par le fait que chaque intervalle mesuré
inclut aussi le temps de la tentative de connexion elle-même
(handshake TCP+TLS qui échoue), pas seulement le temps d'attente pur
du backoff.

**Donnée complémentaire, tirée des métriques internes de Filebeat**
(`libbeat.pipeline.queue`) : capacité de la queue interne fixée à
`max_events: 3200` par défaut (mémoire). Tant que la coupure reste
plus courte que le temps de remplissage de cette queue, aucune
perte — juste de l'attente, comme observé. Une coupure plus longue
ferait éventuellement saturer cette queue, avec un risque de perte
selon la pression appliquée en amont (harvester ralenti ou lignes
perdues selon la config `queue.mem.flush.*`) — non testé ici, lien
direct avec le triptyque de fiabilité déjà posé côté Logstash
(note 16), Filebeat ayant son propre équivalent à une échelle
différente.

**Pistes pour un contexte plus critique**, discutées mais non
implémentées dans ce TP :
- `output.logstash` accepte plusieurs `hosts` avec `loadbalance: true`
  — mécanisme natif pour ne pas dépendre d'un seul Logstash, pas
  besoin de bricoler plusieurs blocs `output`
- Ajuster `backoff.max` selon la criticité réelle des logs et la
  capacité de rétransmission acceptable
- Surveillance proactive de la validité des certificats émis, pour
  anticiper une expiration plutôt que la découvrir via un échec de
  connexion — boucle avec le point 1 de cette même étape

## Point 2 — Permissions sur le matériel cryptographique

Vérification faite sur les deux hosts, aucun resserrement nécessaire
— les tasks écrites plus tôt dans le TP avaient déjà posé les bonnes
permissions :

```
ls -l /etc/filebeat/certs/
-rw-r--r--. 1 filebeat filebeat ... ca.crt
-rw-r--r--. 1 filebeat filebeat ... rh8103.crt
-rw-------. 1 filebeat filebeat ... rh8103.key

ls -l /etc/logstash/certs/
-rw-r--r--. 1 logstash logstash ... ca.crt
-rw-r--r--. 1 logstash logstash ... rocky.crt
-rw-------. 1 logstash logstash ... rocky.key
```

`0600` sur les deux clés privées, `0644` sur les certs/CA publics
(pas sensibles à protéger en lecture), propriétaire correct des deux
côtés (`filebeat`/`logstash`, jamais `root`).

**Dossiers parents également vérifiés**, pas seulement les fichiers —
un `0600` sur un fichier ne sert à rien si son dossier est trop
ouvert :
```
drwxr-x---. 2 filebeat filebeat ... /etc/filebeat/certs
drwxr-x---. 2 logstash logstash ... /etc/logstash/certs
```
`0750` sur les deux, aucun accès pour `other` — cohérent avec les
tasks du rôle. Point 2 entièrement validé sans ajustement nécessaire.

## Point 4 — Cohérence de version Filebeat/Logstash

Hypothèse de départ, à affiner : "même version = protocole qui se
comprend mieux". La doc officielle nuance ce raisonnement — le
protocole Beats (Lumberjack v2) est en fait **assez tolérant**, une
large plage de versions reste compatible entre elles (*"This output
works with all compatible versions of Logstash. See the Elastic
Support Matrix."*), pas un couplage strict version-à-version.

Le vrai risque pratique se situe ailleurs, à deux endroits distincts :

1. **Options de configuration retirées entre versions majeures du
   plugin** — la doc du plugin `beats` (input Logstash) précise :
   *"depuis la version 7.0.0 de ce plugin, plusieurs réglages SSL
   dépréciés ont été retirés"*. Un réglage utilisé aujourd'hui
   (`ssl_verify_mode`, par exemple — un warning à ce sujet a d'ailleurs
   été aperçu dans les logs au fil du TP) pourrait ne pas exister sur
   une version de plugin trop ancienne, ou porter un nom différent.
2. **Structure des champs d'enrichissement ECS**, qui dépend du mode
   de compatibilité ECS du plugin (lui-même lié à sa version) — les
   métadonnées ajoutées par le plugin `beats` ne se rangent pas au
   même endroit selon ce mode.

Donc la vraie raison de viser la même version n'est pas "le protocole
refuserait de communiquer avec une version différente" (il est plus
souple que ça), mais plutôt "éviter qu'une option de config utilisée
aujourd'hui n'existe pas encore, ou plus, de l'autre côté" — un risque
de **compatibilité de configuration**, pas de protocole au sens
strict. Dans ce lab, `8.19.17` des deux côtés : zéro risque réel,
mais la raison de fond est maintenant comprise plutôt que supposée.

## TP complet

Les 4 points de l'Étape 6 sont maintenant traités — cycle de vie du
certificat (asymétrie du diagnostic TLS découverte), permissions
(déjà bonnes, validées), retry/backoff (comportement par défaut
analysé empiriquement), cohérence de version (raison de fond
clarifiée). Avec les phases 1 à 4, le TP `tp-filebeat-rh8103` est
maintenant terminé de bout en bout.

## Lien avec les notes existantes

`tp-filebeat-rh8103-resultat-phase3.md` (phase précédente, principe
"at-least-once" déjà établi côté lecture), `16-panorama-beats.md`
(triptyque de fiabilité, contre-pression — équivalent Filebeat
identifié ici via la queue interne), `18-panorama-tls-mtls.md`
(PKCS#8, bug `ssl_key_passphrase`).
