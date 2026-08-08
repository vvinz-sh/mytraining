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
- aucune fragmentation : vérifier sur le `.log` brut que le nombre
  d'événements en sortie correspond bien au nombre de stacks réelles
  (122), pas plus (sinon le pattern de continuation a raté une ligne
  quelque part)

Critère de réussite concret : dans Kibana, pouvoir filtrer/agréger
sur `exception.chain` (ex. compter combien de fois
`CertificateExpiredException` apparaît) sans avoir à faire une
recherche texte libre sur `message`.

## Matériel

Prêt : `expiredcert_rocky_logstash-plain.log` (à côté de ce draft),
capturé depuis `/var/log/logstash/logstash-plain.log` sur `rocky`
(et non via `journalctl`, qui réinjecte un en-tête syslog sur
chaque ligne et casse l'indentation d'origine — piège identifié
lors d'une première tentative).

Contenu réel : **122 tentatives** de handshake TLS rejetées (retry
Filebeat en boucle), chaîne à 5 niveaux
`DecoderException` → `SSLHandshakeException` → `ValidatorException`
→ `CertPathValidatorException` → `CertificateExpiredException`,
indentation en tabulation (`\t`) sur les lignes `at ...`. 122
événements attendus en sortie du pipeline si le pattern ne fragmente
rien.

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
- Matériel : disponible (`expiredcert_rocky_logstash-plain.log`,
  122 tentatives, chaîne à 5 niveaux)
- Déclenchement : `codec multiline`, `negate: false` sur pattern de
  continuation (`^\s+at\b|^Caused by:|^\.\.\. \d+ more`)
- Pas de comparaison avec le filtre déprécié (source unique, bug non
  démontrable)
- Grok en sortie pour extraire `exception.chain` en champ structuré

Reste à faire : écrire le draft d'exécution détaillé (étapes du
pipeline, config `input`/`filter`/`output`).

## Lien avec les notes existantes

`25-multiline-codec-concept.md`, `26-multiline-implementation-ansible-v.md`
(TP `multiline` déjà fait, cas ansible), `tp-filebeat-rh8103-resultat-phase4.md`
(origine des logs Java réels à réutiliser).
