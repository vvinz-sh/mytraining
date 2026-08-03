# TP — `/_node/logging` à chaud + DLQ native (diagnostic + retraitement) (draft)

Statut : **design posé, pas encore exécuté**. Complète le Palier 4,
regroupe deux items du README en un seul TP cohérent : monter le
niveau de log à chaud sans redémarrer le pipeline, **et** le
retraitement du DLQ (initialement prévu comme deux points séparés,
fusionnés à la demande de Vincent après les notes 20/30).

## Contexte

Pas d'Elasticsearch dans le lab pour l'instant (Palier 5, pas encore
fait) — donc le déclencheur "documents individuels refusés par ES
(400/404)" du DLQ (note 30) n'est **pas** reproductible ici. Seul le
deuxième cas couvert par le DLQ natif l'est : une **erreur
d'évaluation de condition** (comparaison de types incompatibles).
Scope de ce TP assumé en conséquence : déclencher le DLQ via ce
second cas, pas via ES.

## Étape 1 — Activer le DLQ sur un pipeline de test

```yaml
# logstash.yml ou pipelines.yml (par pipeline)
dead_letter_queue.enable: true
```
Désactivé par défaut (note 30) — à activer explicitement avant toute
chose.

## Étape 2 — Déclencher volontairement une erreur d'évaluation de condition

Écrire un filtre avec une condition qui compare des types
incompatibles d'une façon qui plante littéralement l'évaluation (pas
juste un `if` qui renvoie `false` proprement). Question à trancher en
expérimentant plutôt qu'en écrivant une regex trouvée toute faite :
quelle comparaison précise fait planter l'évaluation elle-même,
distincte d'une comparaison qui renvoie simplement `false` ? Repense
à ce qui a été observé sur `=~`/`==` (note 27) — pas toutes les
comparaisons "qui échouent" échouent de la même façon.

## Étape 3 — Observer la croissance du DLQ via l'API

```
GET /_node/stats/pipelines
```
Repérer `pipelines.${pipeline_id}.dead_letter_queue.queue_size_in_bytes`
(note 30) — vérifier qu'il croît à mesure que des events déclenchent
l'erreur, sans avoir besoin d'ouvrir le fichier DLQ sur disque pour
le constater.

## Étape 4 — Monter le niveau de log à chaud via `/_node/logging`

```
PUT /_node/logging
{ "logger.logstash.filters.conditional" => "DEBUG" }
```
(nom exact du logger à vérifier — à confirmer via `/_node/plugins`
ou la doc, pas à deviner). Objectif : obtenir plus de détail sur
*pourquoi* l'évaluation échoue, sans redémarrer le pipeline (donc sans
perdre l'état en cours, ni interrompre le flux d'events restants).

Question à observer plutôt qu'à anticiper : est-ce que ce changement
de niveau via l'API est **persistant** après un redémarrage de
Logstash, ou seulement valable jusqu'au prochain restart (cohérent
avec le principe déjà noté que ce PUT est un levier d'action à chaud,
pas une modification de `logstash.yml`) ?

## Étape 5 — Retraiter les events depuis le DLQ

Pipeline séparé, avec l'input dédié :
```
input {
  dead_letter_queue {
    path => "/chemin/vers/dead_letter_queue"
    pipeline_id => "main"
    commit_offsets => true
  }
}
filter {
  # corriger ce qui causait l'échec de la condition d'origine
}
output {
  stdout { codec => rubydebug { metadata => true } }
}
```
Vérifier concrètement le contenu de `@metadata.dead_letter_queue`
(raison, plugin, horodatage — note 30) sur un event réellement
récupéré, pas juste sur l'exemple de la doc. Décider comment corriger
l'event avant de le renvoyer vers sa vraie destination : retirer/
convertir le champ qui faisait planter la comparaison d'origine.

## Ce qu'il faudra vérifier/clarifier en exécutant

- Comparaison précise qui déclenche une vraie erreur d'évaluation
  (pas juste un `if` qui renvoie `false`)
- Nom exact du logger à cibler pour l'étape 4 (`/_node/plugins` ou doc)
- Persistance ou non du changement de niveau de log après un
  redémarrage de Logstash
- Contenu réel de `@metadata.dead_letter_queue` sur un event
  effectivement récupéré, comparé à l'exemple de la doc
- `commit_offsets` : comportement si le pipeline de retraitement est
  relancé une deuxième fois — rejoue-t-il les mêmes events, ou reprend-
  il où il s'était arrêté ?

## Compétences pratiquées

- Utilisation de `/_node/logging` (PUT) en conditions réelles de
  diagnostic, pas juste en théorie (note 20)
- Déclenchement volontaire et observation du deuxième cas de DLQ
  (erreur de condition), le seul reproductible sans Elasticsearch
- Surveillance d'une métrique précise du node stats API en situation
  concrète de croissance du DLQ
- Écriture d'un pipeline de retraitement DLQ complet, correction puis
  ré-émission d'un event récupéré

## Lien avec les notes existantes

`20-panorama-api-monitoring.md` (`/_node/logging`, seul endpoint
d'action de l'API), `30-dead-letter-queue-native.md` (scope réel du
DLQ, les deux seuls cas couverts, configuration/retraitement),
`27-conditions-operateurs-breakonmatch.md` (comparaisons, `=~`/`==`
— base pour construire une condition qui plante réellement).
