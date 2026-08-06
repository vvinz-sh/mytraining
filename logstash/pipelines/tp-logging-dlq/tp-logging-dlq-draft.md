# TP — `/_node/logging` à chaud + DLQ native (diagnostic + retraitement) (draft)

Statut : **design posé, pas encore exécuté**. Complète le Palier 4,
regroupe deux items du README en un seul TP cohérent : monter le
niveau de log à chaud sans redémarrer le pipeline, **et** le
retraitement du DLQ.

## Contexte

Le DLQ natif ne couvre que deux cas précis (note 30) : une erreur
d'évaluation de condition, et un document rejeté individuellement par
Elasticsearch (code 400/404). Le draft d'origine n'avait accès qu'au
premier cas (Elasticsearch pas encore déployé, Palier 5) — les deux
sont maintenant testés, pour couvrir empiriquement les deux
déclencheurs documentés plutôt qu'un seul.

## Étape 1 — Activer le DLQ sur un pipeline de test

```yaml
# logstash.yml ou pipelines.yml (par pipeline)
dead_letter_queue.enable: true
```
Désactivé par défaut (note 30) — à activer explicitement avant toute
chose.

## Étape 2a — Cas 1 : déclencher une erreur d'évaluation de condition

Écrire un filtre avec une condition qui compare des types
incompatibles d'une façon qui plante littéralement l'évaluation (pas
juste un `if` qui renvoie `false` proprement). Question à trancher en
expérimentant plutôt qu'en écrivant une regex trouvée toute faite :
quelle comparaison précise fait planter l'évaluation elle-même,
distincte d'une comparaison qui renvoie simplement `false` ? Repense
à ce qui a été observé sur `=~`/`==` (note 27) — pas toutes les
comparaisons "qui échouent" échouent de la même façon.

## Étape 2b — Cas 2 : provoquer un vrai rejet Elasticsearch (conflit de mapping)

Exploiter le mécanisme déjà détaillé en note 32 (mapping dynamique,
`RC: 0` vs `RC: "erreur"`) : envoyer un premier event avec un champ
numérique (mapping dynamique décide `integer`), puis un second event
avec le même nom de champ en string incompatible. Vérifier que :
- La requête bulk globale réussit (`200 OK` côté Logstash, pas
  d'erreur visible en surface)
- Le document en conflit est bien rejeté **individuellement**
  (`400`, `mapping_exception`) — à confirmer en observant le contenu
  réel de la réponse Elasticsearch, pas juste en supposant
- Ce rejet précis, et lui seul (pas une requête HTTP totalement en
  échec, cas non couvert par le DLQ — note 30), finit bien dans la
  DLQ plutôt que d'être perdu

## Étape 3 — Observer la croissance du DLQ via l'API

```
GET /_node/stats/pipelines
```
Repérer `pipelines.${pipeline_id}.dead_letter_queue.queue_size_in_bytes`
(note 30) — vérifier qu'il croît à mesure que des events déclenchent
l'un ou l'autre des deux cas, sans avoir besoin d'ouvrir le fichier
DLQ sur disque pour le constater.

## Étape 4 — Monter le niveau de log à chaud via `/_node/logging`

```
PUT /_node/logging
{ "logger.logstash.filters.conditional" => "DEBUG" }
```
(nom exact du logger à vérifier — à confirmer via `/_node/plugins`
ou la doc, pas à deviner ; un logger différent sera probablement
pertinent pour le cas 2, côté plugin `elasticsearch` plutôt que
`conditional`). Objectif : obtenir plus de détail sur *pourquoi*
l'un ou l'autre échoue, sans redémarrer le pipeline (donc sans perdre
l'état en cours, ni interrompre le flux d'events restants).

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
  # corriger différemment selon la cause d'origine (cas 1 vs cas 2)
}
output {
  stdout { codec => rubydebug { metadata => true } }
}
```
Vérifier concrètement le contenu de `@metadata.dead_letter_queue`
(raison, plugin, horodatage — note 30) sur des events des **deux**
cas récupérés depuis la même queue — est-ce que ce metadata suffit à
distinguer clairement de quel cas chaque event récupéré provient
(utile pour appliquer une correction différente selon l'origine), ou
faut-il une autre logique de distinction ?

## Ce qu'il faudra vérifier/clarifier en exécutant

- Comparaison précise qui déclenche une vraie erreur d'évaluation
  (cas 1, pas juste un `if` qui renvoie `false`)
- Contenu réel de la réponse Elasticsearch sur le rejet individuel
  (cas 2) — code, message d'erreur exact
- Nom exact du/des loggers à cibler pour l'étape 4 (`/_node/plugins`
  ou doc) — probablement différents entre les deux cas
- Persistance ou non du changement de niveau de log après un
  redémarrage de Logstash
- Contenu réel de `@metadata.dead_letter_queue` sur les events des
  deux cas, et si ce metadata permet de les distinguer proprement
- `commit_offsets` : comportement si le pipeline de retraitement est
  relancé une deuxième fois — rejoue-t-il les mêmes events, ou
  reprend-il où il s'était arrêté ?

## Compétences pratiquées

- Utilisation de `/_node/logging` (PUT) en conditions réelles de
  diagnostic, pas juste en théorie (note 20)
- Déclenchement volontaire et observation des **deux** cas documentés
  du DLQ natif, pas un seul
- Surveillance d'une métrique précise du node stats API en situation
  concrète de croissance du DLQ
- Écriture d'un pipeline de retraitement DLQ complet, capable de
  distinguer et corriger différemment selon la cause d'origine

## Lien avec les notes existantes

`20-panorama-api-monitoring.md` (`/_node/logging`, seul endpoint
d'action de l'API), `30-dead-letter-queue-native.md` (scope réel du
DLQ, les deux seuls cas couverts, configuration/retraitement),
`27-conditions-operateurs-breakonmatch.md` (comparaisons, `=~`/`==`
— base pour construire une condition qui plante réellement),
`32-architecture-elasticsearch-base.md` (mapping dynamique, exemple
`RC` repris ici en pratique pour le cas 2).
