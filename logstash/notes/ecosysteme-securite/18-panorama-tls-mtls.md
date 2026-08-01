# Logstash — Panorama TLS/mTLS entre composants

Complète le Palier 0 — théorie seulement, la mise en pratique
(sécuriser Filebeat RH8103 ↔ Logstash Rocky9) est prévue au Palier 3.

## TLS simple vs mutuel (mTLS) : qui prouve quoi à qui

**TLS simple** (HTTPS classique) : seul le **serveur** prouve son
identité au client. Cohérent pour un site web public, où n'importe
quel visiteur anonyme doit pouvoir se connecter sans être identifié.

**mTLS** (mutual TLS, requis pour Beats↔Logstash) : les **deux**
parties se prouvent mutuellement leur identité. Justifié précisément
parce que Logstash reçoit des données d'infrastructure sensibles
d'un client **précis et connu à l'avance** (une machine spécifique,
pas un visiteur anonyme) — le besoin d'authentifier le client n'a pas
de sens pour un site web public, mais en a tout le sens ici : éviter
qu'un client inconnu se branche sur Logstash, ou (pire niveau
confidentialité) qu'un client se connecte à un serveur Logstash
usurpé.

## Les trois éléments d'une config TLS Logstash

Dans la config `input { beats { ssl_certificate => ..., ssl_key =>
..., ssl_certificate_authorities => ... } }` :

- **`ssl_certificate`** — la partie **publique** du certificat de
  Logstash, exposée aux clients, signée par la CA de confiance
- **`ssl_key`** — la clé **privée**, jamais exposée, utilisée pour
  déchiffrer/signer côté serveur
- **`ssl_certificate_authorities`** — définit quelle CA est acceptée
  pour valider les certificats reçus (côté client dans ce cas, pour
  le mTLS)

Dans cet écosystème, c'est typiquement **la même CA privée**
(auto-générée via `elasticsearch-certutil`) qui signe à la fois le
certificat de Logstash et celui de Filebeat — contrairement à un site
web public qui passe par une CA commerciale reconnue.

## Piège pratique : le format PKCS#8 obligatoire pour la clé

Erreur typique documentée si la clé n'est pas au bon format :
*"your private key was not in PKCS8 format"*.

**Pourquoi PKCS#8 spécifiquement** (question posée avant de conclure
à une contrainte arbitraire de Logstash) : PKCS#8 est une syntaxe de
clé privée **générique**, agnostique de l'algorithme (RSA, EC,
Ed25519...) — l'identifiant d'algorithme est encodé **dans** la
structure ASN.1, pas dans l'en-tête. PKCS#1, plus ancien, est
spécifique à RSA. Confirmation frappante : **Ed25519 n'existe même
pas** en format "traditionnel" — il a été défini après que PKCS#8 soit
devenu le standard, donc il n'a jamais eu besoin d'un format
spécifique à lui.

Conversion nécessaire si la clé est en PKCS#1 :
```
openssl pkcs8 -in cle_pkcs1.pem -topk8 -nocrypt -out cle_pkcs8.pem
```

**Détail amusant lié à Logstash spécifiquement** : une pull request
réelle trouvée sur `jruby-openssl` (la bibliothèque TLS que Logstash
utilise en interne, puisqu'il tourne sur JRuby) corrige un bug précis
de parsing des clés EC au format PKCS#8 — la contrainte PKCS#8 n'est
donc pas arbitraire, mais son support technique a eu ses propres
accrocs historiques côté implémentation JRuby.

## PKCS#8 chiffré (avec passphrase) : supporté en théorie, buggé en pratique

Question posée : PKCS#8 permet le chiffrement par passphrase (un
fichier chiffré commence par `-----BEGIN ENCRYPTED PRIVATE KEY-----`)
— Logstash le prend-il en charge ?

**En théorie, oui** : le plugin `beats` a un paramètre dédié
`ssl_key_passphrase`, confirmé dans le code source
(`SslContextBuilder.new(@ssl_certificate, @ssl_key, passphrase)`).

**En pratique, un vrai point de friction historique** — plusieurs
tickets GitHub documentent que ce paramètre ne fonctionne pas de
façon fiable selon les versions :
- *"SSL_key_passphrase doesn't currently work"* (issue #61)
- *"ssl_key_passphrase doesn't work starting from version 6.0.8"*
  (issue #391, quelqu'un a dû downgrader de version pour contourner)
- Un utilisateur confirme explicitement ne jamais avoir réussi à
  faire fonctionner une clé PKCS#8 chiffrée avec le plugin `beats`

**Contournement systématiquement recommandé** : générer la clé en
PKCS#8 **sans** chiffrement (`-nocrypt`), et protéger l'accès
autrement — via les **permissions filesystem** (même principe de
moindre privilège déjà appliqué à `git-push-perso`/`mcp-git`), ou en
stockant la **passphrase** dans le **Logstash Keystore**
(`${beat_input_ssl_key_passphrase}`, item déjà ajouté au programme du
Palier 1) plutôt qu'en clair dans le `.conf` — même si la clé
elle-même reste non chiffrée sur disque.

## Résumé

1. mTLS (double authentification) se justifie par la nature du
   client (machine connue, pas visiteur anonyme) — contrairement au
   TLS simple du web public
2. Une seule CA privée signe généralement les deux côtés dans
   l'écosystème Elastic, contrairement à une CA publique commerciale
3. PKCS#8 est exigé car générique/agnostique de l'algorithme — PKCS#1
   est propre à RSA, et des algorithmes modernes (Ed25519) n'existent
   qu'en PKCS#8
4. Le chiffrement de la clé par passphrase est supporté en théorie
   mais historiquement peu fiable en pratique — le contournement
   réel passe par les permissions filesystem ou le Keystore, pas par
   le chiffrement natif de la clé elle-même

## Lien avec les notes existantes

`01-panorama-alternatives-interfacage-securite.md` (filtre `ruby`,
moindre privilège), README Palier 1 (item Keystore ajouté récemment,
directement pertinent ici), README Palier 3 (TP Filebeat RH8103,
mise en pratique de mTLS prévue).

## Sources

- [Secure communication with Logstash (Beats, Elastic Docs)](https://www.elastic.co/docs/reference/beats/filebeat/configuring-ssl-logstash)
- [TLS for the Elastic Stack (Elastic Blog)](https://www.elastic.co/blog/tls-elastic-stack-elasticsearch-kibana-logstash-filebeat)
- [Understanding PKCS8 vs PKCS1 vs PKCS12 (sslhow.com)](https://sslhow.com/pkcs8-vs-pkcs1-vs-pkcs12)
- [Private Key Formats: Why Your Key Gets Rejected (getaCert.com)](https://getacert.com/gotchas/private-key-formats)
- [logstash-input-beats source (GitHub)](https://github.com/logstash-plugins/logstash-input-beats/blob/main/lib/logstash/inputs/beats.rb)
- [SSL_key_passphrase doesn't currently work (GitHub Issue #61)](https://github.com/logstash-plugins/logstash-input-beats/issues/61)
- [ssl_key_passphrase doesn't work starting from 6.0.8 (GitHub Issue #391)](https://github.com/logstash-plugins/logstash-input-beats/issues/391)
- [Logstash pour les devs — 24 : Sécurité Logstash (SSL, auth, secrets) — Blog Pal'Temps, fr](https://blog.paltemps.fr/logstash-24-securite/)
