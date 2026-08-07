# TP — `/_node/logging` à chaud + DLQ native (diagnostic + retraitement) : résultat

Complète `tp-logging-dlq-draft.md`. Toutes les étapes du draft
exécutées : activation du DLQ, les deux cas documentés (erreur de
condition, rejet Elasticsearch), observation via l'API, montée du
niveau de log à chaud, retraitement complet. Pipeline dédié `tp-dlq`
créé pour l'occasion (input `file` sur `/tmp/tp-dlq.log`, `codec =>
json`, output `elasticsearch` sur l'index `tp-dlq`).

## Étape 1 — Activer le DLQ

```yaml
# pipelines.yml, pour le pipeline tp-dlq
dead_letter_queue.enable: true
```
Désactivé par défaut (note 30), activé explicitement pour ce
pipeline précis avant toute chose.

## Bug de configuration résolu avant de commencer : `json_lines` vs `json`

`events.in: 0` en boucle malgré un pipeline démarré sans erreur.
Cause : `codec => json_lines` utilisé avec un input `file` — ce
codec attend de repérer lui-même les `\n` dans un flux continu
(`tcp`/`stdin`), or `file` les a déjà retirés avant transmission.
Confirmé par la doc officielle, qui déconseille explicitement ce
codec pour les inputs "line-oriented". Corrigé en passant à
`codec => json`.

## Étape 2a — Cas 1 : déclencher une erreur d'évaluation de condition

**Trois hypothèses testées avant de trouver celle qui fonctionne** :

1. `[un_champ_entier] =~ "^\d+$"` sur un champ entier — **ne plante
   pas**. Logstash coerce implicitement la valeur en string avant
   d'appliquer le match (comportement du compilateur d'expressions,
   pas du Ruby brut sans filet).
2. `[un_champ_entier] == "42"` (entier vs string) — **ne plante pas
   non plus**. `==` a un repli natif Ruby qui renvoie simplement
   `false` face à des types incompatibles, jamais une exception.
3. **Un opérateur d'ordre** (`>`, `<`, `<=`, `>=`) — celui-ci
   fonctionne, car ces opérateurs n'ont pas de repli "renvoie
   `false`" en Ruby : ils lèvent une vraie exception face à des
   types incomparables.

Filtre retenu :
```
filter {
  if [un_champ_entier] > "40" {
    mutate {
      add_field => { "[monfield]" => "test" }
    }
  }
}
```
Event envoyé : `{"un_champ_entier": 42}` (via
`echo '{"un_champ_entier": 42}' >> /tmp/tp-dlq.log`).

Erreur obtenue dans les logs Logstash :
```
[WARN][org.logstash.execution.AbstractPipelineExt][tp-dlq] (TypeError) no implicit conversion of nil into Integer. Failing event was sent to dead letter queue
```
Pas exactement l'erreur "comparaison Integer/String" anticipée par
la doc générale, mais un `TypeError` de la même famille (conversion
implicite impossible), suffisant pour déclencher le routage DLQ.

**Piège découvert en cours de route** : cette condition, laissée
active sans isolement, plante aussi sur les events sans le champ
`un_champ_entier` (`nil > "40"` échoue pour la même raison). Constaté
en enchaînant sur le Cas 2 (`{"RC": 0}` routé en DLQ par erreur, sans
rapport avec le mapping). Retirée temporairement pour le Cas 2 — à
isoler proprement si les deux doivent coexister
(`if [un_champ_entier] and [un_champ_entier] > "40"`).

## Étape 2b — Cas 2 : provoquer un vrai rejet Elasticsearch (conflit de mapping)

Repris de l'exemple `RC` de la note 32. Séquence de 3 lignes
envoyées dans `/tmp/tp-dlq.log` :

1. `{"RC": 0}` → mapping fixé en `long` (confirmé dans Kibana, Data
   View, type du champ `RC`)
2. `{"RC": "1"}` → **accepté sans erreur** — Elasticsearch **coerce**
   automatiquement une string qui a un sens numérique vers le type du
   champ (comportement par défaut, coercition activée sauf
   désactivation explicite) ; pas un vrai conflit, comportement non
   anticipé avant de tester
3. `{"RC": "erreur"}` → rejeté, `400`

Erreur exacte obtenue dans les logs Logstash :
```
[WARN][logstash.outputs.elasticsearch][tp-dlq] Events could not be indexed and routing to DLQ {..., :response=>{"index"=>{"status"=>400, "error"=>{"type"=>"document_parsing_exception", "reason"=>"[1:194] failed to parse field [RC] of type [long] in document with id '...'. Preview of field's value: 'erreur'", "caused_by"=>{"type"=>"illegal_argument_exception", "reason"=>"For input string: \"erreur\""}}}}}
```

## Étape 3 — Observer la croissance du DLQ via l'API

```bash
curl -s localhost:9600/_node/stats/pipelines | jq '.pipelines."tp-dlq".dead_letter_queue'
```
`queue_size_in_bytes` confirmé en hausse après chacun des deux cas
(`1` au départ, vide → `757` après le Cas 1 → nouvelle hausse après
le Cas 2) — les deux types d'erreurs atterrissent bien dans la
**même** DLQ (une seule queue par pipeline, pas une par type
d'erreur).

## Étape 4 — Monter le niveau de log à chaud via `/_node/logging`

**Identifier les loggers exacts, sans deviner** :
```bash
curl -s localhost:9600/_node/logging | jq | grep Abstract
curl -s localhost:9600/_node/logging | jq | grep outputs.elastic
```
Confirmé : `org.logstash.execution.AbstractPipelineExt` (Cas 1),
`logstash.outputs.elasticsearch` (Cas 2).

**Passer les deux en `DEBUG`** :
```bash
curl -s -X PUT localhost:9600/_node/logging \
  -H 'Content-Type: application/json' \
  -d '{
    "logger.org.logstash.execution.AbstractPipelineExt": "DEBUG",
    "logger.logstash.outputs.elasticsearch": "DEBUG"
  }'
```
Réponse confirmant l'application : `"acknowledged": true`.

**Impact réel, très différent selon le plugin concerné** :
- **Cas 2 (`elasticsearch`)** : quasiment aucun gain — le `WARN` par
  défaut contenait déjà le détail complet de l'erreur
  (`document_parsing_exception`, la cause précise). `DEBUG` n'ajoute
  qu'une ligne de contexte sur l'envoi du batch, rien de plus.
- **Cas 1 (`AbstractPipelineExt`)** : gain net — le `WARN` par défaut
  ne donnait qu'une ligne (`TypeError: no implicit conversion of nil
  into Integer`), sans dire *quel* event ni *où*. `DEBUG` ajoute le
  **contenu complet de l'event fautif**
  (`Event generating the fault: {...un_champ_entier=42...}`) et la
  **stack trace Java complète**
  (`ConditionalEvaluationError` → `TypeError`, jusqu'au point exact
  dans le pipeline compilé, `CompiledDataset1.compute`).

**Conclusion** : l'intérêt de monter le niveau de log à chaud dépend
fortement du plugin concerné — pas une action à appliquer par
réflexe partout, seulement là où le niveau par défaut est
effectivement trop laconique.

**Persistance testée, pas supposée** : après `systemctl restart
logstash` (sans repasser par l'API), les deux loggers étaient
revenus à leur niveau par défaut (`INFO`/`WARN`) — confirmé par une
découverte non planifiée en retestant le Cas 1 (le filtre avait été
retiré puis rétabli, nécessitant un restart, qui a remis les niveaux
à zéro sans qu'on le cherche explicitement). Confirme le principe
déjà noté en théorie (note 20) : `/_node/logging` est un levier
d'action à chaud pour du diagnostic ponctuel, pas un réglage
durable — pour un changement permanent, il faudrait le poser dans
`logstash.yml`.

## Étape 5 — Retraiter les events depuis la DLQ

Pipeline `tp-dlq-reprocess` dédié, exécuté **en parallèle** de
`tp-dlq` (pas besoin de l'arrêter — aucune contention constatée sur
le fichier DLQ, les deux process peuvent lire/écrire simultanément).

**Distinguer les deux cas** — vérifié via
`@metadata.dead_letter_queue.plugin_type`, suffisant à lui seul, pas
besoin de parser `reason` en texte libre. Pipeline d'observation,
volontairement sans suppression (`commit_offsets => false`, pour
pouvoir relire plusieurs fois pendant les ajustements) :
```
input {
  dead_letter_queue {
    path => "/var/lib/logstash/dead_letter_queue"
    pipeline_id => "tp-dlq"
    commit_offsets => false   # d'abord en observation, avant la version finale
  }
}
output {
  stdout { codec => rubydebug { metadata => true } }
}
```
Résultat observé : `plugin_type: "if-statement"` pour le Cas 1,
`plugin_type: "elasticsearch"` pour le Cas 2 — critère net et fiable
pour appliquer une correction différenciée.

**Correction appliquée** : Cas 1 renvoyé tel quel (la faute était
dans le filtre du pipeline d'origine, pas dans la donnée — rien à
corriger sur l'event lui-même) ; Cas 2 corrigé en castant `RC` à
`-1` (valeur sentinelle) avant renvoi :
```
filter {
  if [@metadata][dead_letter_queue][plugin_type] == "elasticsearch" {
    mutate {
      replace => { "RC" => -1 }
      convert => { "RC" => "integer" }
    }
  }
}
```
Vérifié : `RC` ressort bien en entier (`-1`, sans guillemets) dans
la sortie, `replace` suivi de `convert` dans le même bloc `mutate`
fonctionne sans souci d'ordre.

**Pipeline final** (`commit_offsets => true`, renvoi vers le même
index `tp-dlq` que le flux normal — décision assumée plutôt qu'un
index séparé) :
```
input {
  dead_letter_queue {
    path => "/var/lib/logstash/dead_letter_queue"
    pipeline_id => "tp-dlq"
    commit_offsets => true
  }
}
filter {
  if [@metadata][dead_letter_queue][plugin_type] == "elasticsearch" {
    mutate {
      replace => { "RC" => -1 }
      convert => { "RC" => "integer" }
    }
  }
}
output {
  elasticsearch {
    hosts => ["https://localhost:9200"]
    ssl_verification_mode => "none"
    index => "tp-dlq"
    user => "elastic"
    password => "${es_pwd}"
  }
}
```
Les deux events corrigés confirmés arrivés dans l'index `tp-dlq`
via Kibana.

**Nettoyage des segments DLQ : `commit_offsets` seul ne suffit pas.**
Constaté en testant, confirmé ensuite par la doc officielle :
`commit_offsets => true` marque juste la position de lecture, il ne
supprime rien du disque. Il faut le réglage séparé
`clean_consumed => true` (nécessite `commit_offsets => true` en même
temps, sinon erreur de config) pour déclencher la suppression réelle
des segments entièrement lus :
```
input {
  dead_letter_queue {
    path => "/var/lib/logstash/dead_letter_queue"
    pipeline_id => "tp-dlq"
    commit_offsets => true
    clean_consumed => true
  }
}
```
Vérification de la croissance/décroissance via :
```bash
curl -s localhost:9600/_node/stats/pipelines | jq '.pipelines | to_entries[] | {pipeline: .key, dlq: .value.dead_letter_queue}'
```
Résultat après activation : 7 segments sur 9 supprimés
(`queue_size_in_bytes` retombé de `8103` à `1511`, stable sur
plusieurs vérifications successives — pas une fuite continue). Les 2
segments restants (`8.log`, `9.log.tmp`) forment un plancher stable :
le segment actif (`.tmp`) ne peut jamais être nettoyé tant qu'il
reste ouvert en écriture par le pipeline source, et le segment juste
avant attend la même condition pour être définitivement clos.

## Lien avec les notes existantes

`20-panorama-api-monitoring.md` (`/_node/logging`), `30-dead-letter-queue-native.md`
(scope du DLQ, les deux cas — confirmés ici en pratique),
`27-conditions-operateurs-breakonmatch.md` (`=~`/`==`, hypothèses
écartées ici), `32-architecture-elasticsearch-base.md` (mapping
dynamique, exemple `RC` repris en pratique, coercition numérique
découverte en testant).

## Sources

- [Dead letter queues (DLQ) — Logstash Reference (Elastic)](https://www.elastic.co/docs/reference/logstash/dead-letter-queues) — `commit_offsets`, `clean_consumed`, comportement par défaut du nettoyage
- [Dead_letter_queue input plugin — Logstash Reference (Elastic)](https://www.elastic.co/docs/reference/logstash/plugins/plugins-inputs-dead_letter_queue) — options exactes, dépendance `clean_consumed`/`commit_offsets`
- [JSON_lines codec plugin — Logstash Reference (Elastic)](https://www.elastic.co/docs/reference/logstash/plugins/plugins-codecs-json_lines) — mise en garde explicite contre l'usage avec un input line-oriented (`file`)
