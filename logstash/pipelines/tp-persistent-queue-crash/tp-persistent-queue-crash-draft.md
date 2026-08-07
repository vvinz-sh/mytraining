# TP — Persistent queue : simuler un crash en cours de traitement, vérifier la reprise (draft)

Statut : **design posé, pas encore exécuté**. Dernier TP du Palier 4.
Met en pratique la théorie déjà posée au Palier 1 (note 09,
`queue.type: memory` vs `persisted`).

## Contexte

`queue.type: memory` (défaut) perd tout ce qui n'a pas atteint
`output` en cas de crash. `queue.type: persisted` comble ce trou via
un accusé de réception ("acked"), un event n'étant retiré de la queue
qu'une fois confirmé jusqu'au bout. Objectif : provoquer une vraie
accumulation mesurable dans la queue avant de tuer le process, sur
les deux configurations, pour comparer perte réelle vs récupération
réelle — pas juste la théorie.

Source : flux TCP généré par un script dédié, débit contrôlé,
supérieur à ce que Logstash peut absorber une fois bridé en CPU. Un
flux TCP transitoire (pas de fichier, pas de sincedb) élimine tout
risque de rejeu depuis une source qui garderait sa propre mémoire de
progression — seule la queue elle-même peut expliquer ce qui est
récupéré après un crash.

## Étape 1 — Script générateur d'events

```bash
#!/bin/bash
# Usage : ./send-events.sh <host> <port> <count> <rate_par_seconde>
HOST="$1"
PORT="$2"
COUNT="$3"
RATE="$4"
DELAY=$(echo "scale=6; 1/$RATE" | bc)

exec 3<>"/dev/tcp/$HOST/$PORT"
for i in $(seq 1 "$COUNT"); do
    echo "EVT-${i}-$(date +%s%N)" >&3
    sleep "$DELAY"
done
exec 3<&-
exec 3>&-
echo "=== Envoyé : $COUNT events vers $HOST:$PORT (débit visé : $RATE/s) ==="
```
Connexion TCP persistante (pas de reconnexion par ligne), chaque
event numéroté séquentiellement + timestamp nanoseconde — comptage
final trivial, identifiable individuellement si besoin.

## Étape 2 — Pipeline Logstash

```
input {
  tcp {
    port => 6000
  }
}
output {
  file {
    path => "/tmp/tp-pq-crash-out.log"
  }
}
```
Codec `line` par défaut sur `tcp` — chaque ligne devient directement
`message`, pas besoin de JSON pour ce test.

## Étape 3 — Calibrer le débit et le throttling CPU

Limitation CPU appliquée **à chaud** sur le process déjà lancé (pas
via override systemd au démarrage, pour ne pas ralentir
anormalement le boot de la JVM elle-même) :
```bash
systemctl set-property --runtime logstash.service CPUQuota=20%
```
`--runtime` = changement transitoire, non persisté.

`RATE` du générateur doit dépasser clairement ce que Logstash peut
absorber une fois bridé — à calibrer en pratique : lancer un premier
petit test à un débit arbitraire et observer si `queue.events_count`
bouge réellement. Si non, monter le débit ou resserrer encore le
quota CPU.

## Étape 4 — Métriques à surveiller

```bash
curl -s localhost:9600/_node/stats/pipelines | jq '.pipelines."tp-pq-crash" | {queue, input_tp: .flow.input_throughput.current, output_tp: .flow.output_throughput.current, backpressure: .flow.queue_backpressure.current, events_in: .events.in}'
```
- `queue.events_count` — mesure centrale, ce qu'on cherche à voir
  monter
- `queue.queue_size_in_bytes` — même chose côté taille disque/mémoire
- `flow.input_throughput.current` vs `flow.output_throughput.current`
  — signal causal : si l'entrée dépasse durablement la sortie, c'est
  mécaniquement ce qui remplit la queue
- `flow.queue_backpressure.current` — jamais exploitée jusqu'ici,
  mesure directement la pression d'une queue qui sature
- `events.in` — total cumulé, à comparer à `COUNT` envoyé une fois
  terminé

## Étape 5 — Cas `queue.type: memory`

1. Lancer le pipeline, appliquer le `CPUQuota`
2. Lancer le générateur avec `COUNT`/`RATE` calibrés
3. Surveiller les métriques ci-dessus, relever précisément
   `queue.events_count` **juste avant** le kill (pas après coup)
4. `kill -9` le process
5. Relancer, laisser terminer, compter `/tmp/tp-pq-crash-out.log`

Objectif : perte mesurable, et surtout **cohérente** avec le
`events_count` relevé juste avant le crash — pas juste "il manque des
events", mais un écart qui colle à la valeur observée. Confirmer
aussi qu'aucun crash du pipeline lui-même, juste une perte silencieuse.

## Étape 6 — Cas `queue.type: persisted`

Même procédure, `queue.type: persisted` cette fois. Objectif
principal : zéro perte, comparé à `COUNT` envoyé. Objectif secondaire,
rendu possible par le choix de source TCP transitoire : tout event
récupéré après le crash ne peut venir **que** du disque de la queue
persistée elle-même — preuve propre du mécanisme, sans ambiguïté
possible avec une source qui rejouerait depuis sa propre mémoire.
Noter aussi le coût observé (latence de reprise, taille sur disque de
la queue au moment du crash).

## Ce qu'il faudra vérifier/clarifier en exécutant

- `RATE`/`COUNT` et `CPUQuota` réellement calibrés pour créer une
  accumulation visible — à ajuster en pratique, pas deviné à l'avance
- Écart de perte (cas `memory`) cohérent avec `events_count` relevé
  juste avant le kill
- Coût réel (latence, taille disque) de `persisted` par rapport à
  `memory` sur ce test

## Compétences pratiquées

- Construction d'un scénario de charge/crash reproductible et
  mesurable, avec une source qui élimine toute ambiguïté sur l'origine
  des events récupérés
- Limitation de ressources à chaud sur un service déjà lancé
  (`systemctl set-property --runtime`)
- Lecture de métriques de flux (`input_throughput`/`output_throughput`/
  `queue_backpressure`) jamais exploitées jusqu'ici

## Lien avec les notes existantes

`09-configuration-logstash-java.md` (`queue.type` — théorie posée,
testée ici), `16-panorama-beats.md` (triptyque de fiabilité —
contre-pression, persisted queue, DLQ), `30-dead-letter-queue-native.md`
(DLQ, mécanisme complémentaire mais disjoint de la persisted queue).
