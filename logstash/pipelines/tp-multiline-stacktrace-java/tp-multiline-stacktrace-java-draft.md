# TP — Recoller une stack trace Java multiligne (mini-draft)

Statut : **amorce seulement, pas encore designé en détail**. Palier 3
(renforcement, multiligne, intégration) — complète le TP `multiline`
déjà fait sur la sortie `ansible-playbook -v` (notes 25/26), cette
fois sur un cas plus classique/représentatif.

## Objectif visé

En sortie de ce TP, une stack trace Java multiligne brute (plusieurs
lignes `at ...`, `Caused by:` imbriqués, `... N more`) doit devenir
**un seul événement Logstash structuré**, avec :
- un champ `exception.chain` listant, dans l'ordre, les exceptions
  de la chaîne `Caused by:` (ex. `[DecoderException,
  SSLHandshakeException, CertPathValidatorException,
  CertificateExpiredException]`)
- la trace complète toujours accessible (champ `message` conservé
  tel quel, pas perdu au profit de l'extraction)
- aucune fragmentation : vérifier sur le `.log` brut regénéré que le
  nombre d'événements en sortie correspond bien au nombre de stacks
  réelles, pas plus (sinon le pattern de continuation a raté une
  ligne quelque part)

Critère de réussite concret : dans Kibana, pouvoir filtrer/agréger
sur `exception.chain` (ex. compter combien de fois
`CertificateExpiredException` apparaît) sans avoir à faire une
recherche texte libre sur `message`.

## Matériel à régénérer

Vérification faite : les notes du TP `tp-filebeat-rh8103` (résultat
phase 4) ne contiennent que des lignes uniques extraites à l'époque
(`Caused by: java.security.cert.CertificateExpiredException: ...`,
`io.netty.handler.codec.DecoderException: ...`), pas une vraie stack
multiligne avec frames `at ...`. Les `.log` bruts d'origine ne sont
plus disponibles (jamais committés, propres à la VM).

Décision : **regénérer la simulation d'erreur SSL expiré** (même
scénario que le point 1 de l'Étape 6 du TP `tp-filebeat-rh8103` —
cert client ou serveur expiré) pour capturer une vraie stack Java
complète côté Logstash, cette fois en conservant le `.log` brut.

## Décisions prises

**Pattern de déclenchement** : `negate: false` sur un pattern qui
matche les lignes de *continuation* (`^\s+at\b|^Caused by:|^\.\.\.
\d+ more`), pas `negate: true` sur un pattern de timestamp. Logique
inverse du cas ansible (notes 25/26), où l'en-tête déclenchait un
nouveau départ — ici c'est la continuation qui est explicite.

Raison retenue (cohérente avec le principe fail-loud déjà appliqué
sur DLQ et le callback plugin) : avec `negate: false` sur la
continuation, toute ligne au format inattendu casse le bloc →
fragmentation visible dans Kibana. Avec `negate: true` sur un
timestamp, l'échec est silencieux : une ligne mal formée serait
absorbée comme continuation, fusionnant deux événements distincts
sans le signaler.

**`codec` seul, pas de comparaison avec le filtre déprécié** :
lecture depuis un seul fichier de log → le bug du filtre `multiline`
déprécié (regroupement sur le flux global, pas par source) ne peut
pas se manifester avec une seule source de toute façon. Comparaison
non pertinente sur ce cas, pas de valeur pédagogique à la forcer ici.

**Extraction grok structurée** : pas de champ texte brut unique.
Objectif : sortir la chaîne des `Caused by:` en champ structuré
(ex. `exception.chain: [DecoderException, SSLHandshakeException,
CertPathValidatorException, CertificateExpiredException]`), pour
rendre la trace exploitable en filtre/agrégat Kibana plutôt qu'en
recherche texte seule sur `message`.

## Design du TP — récapitulatif

Toutes les décisions de conception sont prises :
- Matériel : à régénérer via nouvelle simulation SSL expiré (cert
  client ou serveur), `.log` brut conservé cette fois
- Déclenchement : `codec multiline`, `negate: false` sur pattern de
  continuation (`^\s+at\b|^Caused by:|^\.\.\. \d+ more`)
- Pas de comparaison avec le filtre déprécié (source unique, bug non
  démontrable)
- Grok en sortie pour extraire `exception.chain` en champ structuré

Reste à faire : régénérer le matériel sur le lab, puis écrire le
draft d'exécution détaillé (étapes) une fois le `.log` brut en main.

## Lien avec les notes existantes

`25-multiline-codec-concept.md`, `26-multiline-implementation-ansible-v.md`
(TP `multiline` déjà fait, cas ansible), `tp-filebeat-rh8103-resultat-phase4.md`
(origine des logs Java réels à réutiliser).
