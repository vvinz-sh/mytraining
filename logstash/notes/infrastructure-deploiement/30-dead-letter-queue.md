# Logstash — Dead Letter Queue (DLQ) native

Deuxième des 2 points théoriques du Palier 4. Clarifie une confusion
naturelle avec le routage manuel `_grokparsefailure` pratiqué sur les
TP ansible — le DLQ natif couvre une famille d'échecs **complètement
différente**, pas plus large ni un remplacement.

## Ce que le DLQ natif couvre réellement — deux cas, et seulement deux

Contrairement à l'intuition initiale ("un mécanisme générique pour
tout échec"), le DLQ natif ne capture que :

1. **Erreurs de l'output Elasticsearch**, pour des documents avec un
   code de réponse **400 ou 404** (échecs non-retryables)
2. **Erreurs d'évaluation d'une condition** (`if`) — par exemple
   comparer une string à un entier d'une façon qui fait planter la
   comparaison elle-même, pas juste renvoyer `false`

**Ce qui n'est jamais couvert**, quoi qu'il arrive : un grok qui
échoue, un `mutate` sur un champ absent, ou tout autre échec de
filtre. C'est précisément pour ça que le routage manuel
`_grokparsefailure` (pratiqué sur les TP ansible) reste nécessaire —
le DLQ et ce routage manuel couvrent deux familles d'échecs
totalement disjointes, ce n'est pas une question de DLQ "en plus
complet".

## Nuance sur les erreurs Elasticsearch : deux niveaux d'échec distincts

- **Requête HTTP qui échoue entièrement** (ES injoignable, timeout) →
  le plugin `elasticsearch` retente **indéfiniment** la requête
  entière — le DLQ n'a jamais l'occasion d'intervenir ici
- **Requête qui réussit** (`200 OK`) mais où certains **documents
  individuels** du batch sont refusés (mapping error, doc introuvable
  pour un update...) → **ces documents précis** partent dans le DLQ,
  un par un, pas toute la requête

## Vocabulaire : "document" (ES) vs "event" (Logstash)

Dans tout le pipeline Logstash — input, filter, output — on parle
d'**event**, de bout en bout. Le mot "document" n'apparaît que côté
**Elasticsearch**, parce que c'est sa terminologie de stockage à lui
(un index ES contient des documents JSON). Le plugin `elasticsearch`
(output) convertit chaque event Logstash en une action d'indexation
ES ; à partir de cette frontière API précise, la réponse d'ES parle
de "document" — mais c'est toujours, fondamentalement, le même event,
juste vu du côté du système qui le reçoit. L'entrée réellement
stockée dans le DLQ garde d'ailleurs l'event Logstash complet, avec
ses champs d'origine, enrichi d'un bloc `@metadata.dead_letter_queue`
(raison de l'échec, plugin concerné, horodatage) — pas un "document
ES" à part.

## Sans DLQ activé : drop silencieux ou pipeline bloqué

Citation exacte de la doc officielle : *"par défaut, quand Logstash
rencontre un event qu'il ne peut pas traiter [...], le pipeline soit
reste bloqué (hang), soit droppe l'event en échec."* Deux issues
possibles, aucune satisfaisante :

- **Drop silencieux** — l'event disparaît sans trace, sans log
  d'erreur visible par défaut
- **Blocage du pipeline** — le traitement se fige sur cet event, ce
  qui bloque potentiellement tout ce qui arrive derrière lui

Scénario concret qui en découle : une comparaison mal typée qui plante
en boucle bloque le traitement, les events s'accumulent en amont dans
la queue (mémoire ou persistée), et si rien ne se résorbe, ça finit
par saturer — le même "poof" final que dans le triptyque de fiabilité
de la note 16 (contre-pression/persisted queue/DLQ), sauf que la cause
ici est un **bug interne au pipeline lui-même**, pas un consommateur
externe trop lent.

## Surveillance : une métrique dédiée dans le node stats API

Le DLQ expose sa taille par pipeline via l'API déjà pratiquée en note
14/20 :
```
pipelines.${pipeline_id}.dead_letter_queue.queue_size_in_bytes
```
Fait directement le pont avec un item déjà noté au programme du
Palier 4 : `/_node/logging`, pour monter le niveau de log à chaud "en
cas de hausse d'échecs (DLQ qui grossit)" — cette métrique précise est
celle qui déclencherait ce diagnostic en pratique.

## Configuration et retraitement

Désactivé par défaut — activation via `logstash.yml` :
```yaml
dead_letter_queue.enable: true
```
Stocké en fichiers sur disque, un dossier séparé par pipeline
(`path.data/dead_letter_queue/<pipeline_id>` par défaut). Pour
retraiter les events plutôt que les laisser dormir indéfiniment : un
**pipeline séparé** avec l'input `dead_letter_queue`, qui relit la
queue, corrige ce qui posait problème (exemple de la doc : retirer un
champ mal typé qui faisait échouer le mapping ES), puis renvoie
l'event nettoyé vers sa vraie destination. Le traitement ne supprime
pas les entrées de la queue d'origine — nécessite une intervention
manuelle séparée pour la vider.

## Résumé

1. Le DLQ natif ne couvre que 2 cas : échecs Elasticsearch (codes
   400/404 sur documents individuels) et erreurs d'évaluation de
   condition — jamais les échecs de filtre (grok, mutate...)
2. Une requête HTTP totalement en échec (ES injoignable) est retentée
   indéfiniment, hors de portée du DLQ — seuls les rejets
   **individuels** dans une requête par ailleurs réussie y arrivent
3. "Document" est un terme Elasticsearch, pas Logstash — même chose
   qu'un event, vu depuis la frontière API du plugin de sortie
4. Sans DLQ, un event problématique est soit droppé silencieusement,
   soit bloque le pipeline (accumulation en amont jusqu'à saturation)
5. Taille du DLQ surveillable par pipeline via le node stats API,
   pont direct vers `/_node/logging` en cas de hausse anormale
6. Désactivé par défaut, stocké sur disque par pipeline, retraité via
   un pipeline dédié avec l'input `dead_letter_queue` — ne vide pas
   la queue d'origine automatiquement

## Lien avec les notes existantes

`16-panorama-beats.md` (triptyque de fiabilité — contre-pression,
persisted queue, DLQ — même famille de "poof" par saturation, cause
différente ici), `20-panorama-api-monitoring.md` et
`14-test-dissect.md` (node stats API, `/_node/logging`),
`tp-parsing-ansible-verbose-resultat.md` (routage manuel
`_grokparsefailure` — famille d'échecs disjointe du DLQ natif).

## Sources

- [Dead letter queues (DLQ) — Logstash Reference (Elastic)](https://www.elastic.co/docs/reference/logstash/dead-letter-queues)
