# TP — Persistent queue : simuler un crash, vérifier la reprise : résultat

Complète `tp-persistent-queue-crash-draft.md`. Pipeline `tp-pq-crash`,
1 worker, `CPUQuota` appliqué à chaud sur le service (`systemctl
set-property --runtime`), source TCP générée par script dédié.

## Partie 1 — Cas `queue.type: memory`

**Calibration du débit** : premier essai de générateur écarté —
`sleep` + `$(date ...)` à chaque ligne dans le script Bash coûtait
plus cher que le débit visé (5000 events à 1000/s réel → 31s au lieu
de 5s). Corrigé avec `${EPOCHREALTIME}` (natif, sans fork) et un
`sleep` groupé toutes les 50 lignes plutôt qu'à chaque ligne — débit
réel proche de la cible ensuite.

**Métrique `queue.events_count`/`queue_size_in_bytes` non
instrumentée pour `memory`** — reste à `0` en permanence quel que soit
le débit ou le `CPUQuota` appliqué, confirmé par un fil de discussion
Elastic où d'autres utilisateurs font le même constat (ces champs sont
alimentés pour `persisted`, pas pour `memory`, dont la structure interne
est une simple file bornée en JVM, pas un état matérialisé sur disque).
Basculé sur `flow.queue_backpressure.current`, qui, elle, réagit
réellement — montée jusqu'à `0.93` sous charge (`CPUQuota=5%`, débit
généré ≈ 3000/s).

Throttling appliqué à chaud, sans redémarrer le service :
```bash
systemctl set-property --runtime logstash.service CPUQuota=5%
```

Commande de monitoring utilisée en boucle (1x/s) :
```bash
curl -s localhost:9600/_node/stats/pipelines | jq -c '.pipelines."tp-pq-crash" | {queue, input_tp: .flow.input_throughput.current, output_tp: .flow.output_throughput.current, backpressure: .flow.queue_backpressure.current, events_in: .events.in}'
```
Sortie type, juste avant le kill :
```json
{"queue":{"type":"memory","events_count":0,"queue_size_in_bytes":0,"max_queue_size_in_bytes":0},"input_tp":137.7,"output_tp":137.7,"backpressure":0.9358,"events_in":8294}
```

**Piège méthodologique supplémentaire** : l'API de monitoring
(`localhost:9600`) tourne dans le même process que le pipeline, donc
soumise au même `CPUQuota` — sous forte charge, l'API elle-même
devient lente/muette, rendant le timing du `kill -9` difficile à piloter
précisément ("chance/pas de chance" plutôt qu'un geste fiable).

**Résultat du crash** : `COUNT = 5000` envoyés, `kill -9` déclenché en
pleine charge (`events_in` autour de `2757` juste avant que l'API
cesse de répondre) → **`2506` lignes en sortie après redémarrage,
aucune reprise du reste** (queue mémoire non persistée, source TCP
déjà fermée par le générateur avant le crash). Perte totale :
**2494 events, soit ~50% du volume envoyé**.

Décomposition de la perte en deux catégories, pas une seule :
- Les events déjà **en vol** (reçus par l'input, comptés dans
  `events_in`, mais pas encore écrits en sortie au moment du kill) —
  perdus car la queue mémoire disparaît avec le process
  (`events_in ≈ 2757` vs `2506` en sortie à cet instant, soit ~250
  events en transit)
- Les events **jamais lus du tout** (encore dans le buffer TCP du
  système, jamais comptabilisés côté Logstash) — perdus car la
  connexion TCP est fermée avec le process, rien à récupérer

Cas `memory` confirmé : perte réelle et significative, comportement
"poof" démontré concrètement plutôt que supposé.

## Partie 2 — Cas `queue.type: persisted`

Même procédure (`COUNT = 5000`, `CPUQuota = 5%`), redémarrage complet
nécessaire pour changer `queue.type` (pas de bascule à chaud). Kill
déclenché manuellement, séparément du générateur, une fois le
`backpressure`/`events` en queue confirmés en hausse.

**`queue.events`/`events_count`/`queue_size_in_bytes` bien
instrumentés pour `persisted`**, contrairement à `memory` — vraie
accumulation observée en direct (jusqu'à `1159` events en attente,
`queue_size_in_bytes` grimpant régulièrement jusqu'à `2,3` Mo).

Même `CPUQuota` réappliqué après le redémarrage complet (nécessaire
pour changer `queue.type`, non modifiable à chaud) :
```bash
systemctl set-property --runtime logstash.service CPUQuota=5%
```
Même commande de monitoring que la partie 1. Sortie type, en pleine
accumulation :
```json
{"queue":{"type":"persisted","events":993,"events_count":993,"queue_size_in_bytes":1272008,"max_queue_size_in_bytes":1073741824},"input_tp":127.3,"output_tp":10.29,"backpressure":0.6786,"events_in":2447}
```

**Résultat brut trompeur au premier regard** : `4748` lignes en
sortie après redémarrage complet, sur `5000` envoyés — un chiffre qui
suggérait une perte de `252`, comme sur `memory` mais en moins grave.
Vérification plus poussée (comptage des numéros de séquence
distincts, pas juste le nombre de lignes) a révélé une réalité
différente :

```bash
grep -oP 'EVT-\K[0-9]+' /tmp/tp-pq-crash-out.log | sort -n | uniq -c | sort -rn | head
# certains numéros présents jusqu'à 4 fois

grep -oP 'EVT-\K[0-9]+' /tmp/tp-pq-crash-out.log | sort -n | uniq | wc -l
# 4658 numéros distincts
```

**Décomposition réelle** :
- **`EVT-1` à `EVT-4658` : tous présents, aucun trou** — le total
  brut de `4748` lignes s'explique par des **doublons** (`90` lignes
  en trop), pas des trous. Comportement "at-least-once" documenté :
  des events déjà entrés dans la queue mais pas encore formellement
  acquittés au moment du crash ont été **rejoués** au redémarrage.
- **`EVT-4659` à `EVT-5000` (342 events) : jamais reçus du tout**,
  hors de la plage couverte.

**Cause de cette deuxième catégorie, confirmée par la doc
officielle** : l'input `tcp` n'a **aucun mécanisme d'accusé de
réception** vers l'émetteur — *"Tcp, udp, zeromq push+pull, and many
other inputs do not have a mechanism to acknowledge receipt to the
sender"* (contrairement à `beats`/`http`, explicitement cités comme
protégés). Tout ce qui restait dans le buffer réseau côté OS, jamais
lu/décodé par le plugin avant le `kill -9`, disparaît avec le
process — la queue persistée ne protège que ce qu'elle a déjà reçu,
pas ce qui traîne encore en amont d'elle. Mécanisme distinct et
cumulatif avec le checkpoint (`queue.checkpoint.writes`/`.interval`,
1024 écritures ou 1000ms par défaut) : même un event déjà entré dans
la queue mais pas encore checkpointé au moment du crash peut aussi ne
pas survivre.

**Bilan `persisted`** : zéro perte définitive parmi ce que Logstash
avait déjà commencé à recevoir (juste des doublons, cohérent avec
"at-least-once", pas des trous) — mais pas une garantie absolue de
zéro perte tout court : la vraie limite vient de la nature de
l'input choisi (`tcp`, sans accusé de réception), pas d'un défaut du
mécanisme `persisted` en lui-même. Un input `beats`/`http` aurait
probablement donné un résultat encore plus net.

## Comparaison finale

| | `memory` | `persisted` |
|---|---|---|
| Envoyés | 5000 | 5000 |
| Perte réelle | 2494 (~50%) | 342 (~7%, uniquement le résiduel réseau jamais reçu) |
| Doublons | 0 | 90 (rejeu "at-least-once" des events non acquittés) |
| Mécanisme de perte | Queue disparaît entièrement avec le process | Seul ce qui n'a jamais atteint le plugin input survit à la perte |



## Sources

- [Persistent queues (PQ) — Logstash Reference (Elastic)](https://www.elastic.co/guide/en/logstash/8.19/persistent-queues.html) — mécanisme de checkpoint, limite des inputs sans accusé de réception (`tcp`, `udp`...)
- [Logstash Persistent Queue — Elastic Blog](https://www.elastic.co/blog/logstash-persistent-queue) — `queue.checkpoint.writes`, scénarios de perte possibles

## Phase 2 — Input `beats` (avec accusé de réception)

Hypothèse de départ (issue de la partie 2) : la perte résiduelle
observée sur `persisted`+`tcp` venait de la nature de l'input `tcp`,
sans accusé de réception — un input `beats` devrait faire mieux.
Testé avec un objectif plus large : comparer `memory`+`beats` **et**
`persisted`+`beats`, pas seulement confirmer l'hypothèse sur
`persisted`, pour distinguer ce qui protège réellement — la queue
Logstash, ou le protocole d'ack propre à Filebeat, indépendant de
`queue.type`.

Pipeline `beats-tls` (mTLS, TP `tp-filebeat-rh8103`) réutilisé tel
quel, sortie fichier. Source : script `logger` sur RH8102
(`echo ... | logger -t tag`, un seul fork, écrit dans
`/var/log/messages` que Filebeat surveille déjà). `CPUQuota` réglé à
`15%` — `5%` s'est révélé trop sévère : Filebeat lui-même se met en
pause synchronisée avec Logstash sous cette contrainte, empêchant
toute accumulation observable côté queue.

```bash
systemctl set-property --runtime logstash.service CPUQuota=15%
```

Même commande de monitoring, adaptée au pipeline `beats-tls` :
```bash
curl -s localhost:9600/_node/stats/pipelines | jq -c '.pipelines."beats-tls" | {queue, input_tp: .flow.input_throughput.current, output_tp: .flow.output_throughput.current, backpressure: .flow.queue_backpressure.current, events_in: .events.in}'
```
Sortie type, juste avant le kill :
```json
{"queue":{"type":"memory","events_count":0,"queue_size_in_bytes":0,"max_queue_size_in_bytes":0},"input_tp":199.2,"output_tp":184.3,"backpressure":0.4119,"events_in":13784}
```

**Cas `queue.type: memory` + `beats`** — 20000 events envoyés,
`kill -9` déclenché en pleine charge (`backpressure` jusqu'à
`0,41`). Comptage par numéro de séquence distinct (pas `wc -l` brut,
faussé par le bruit système normal de `/var/log/messages`) :
```bash
grep -oP 'SEQ-tp-pq-fb-\K[0-9]+' /tmp/tp-pq-fb-crash-out.log | sort -n | uniq | wc -l
# 19978
seq 1 19978 > expected.txt
grep -oP 'SEQ-tp-pq-fb-\K[0-9]+' /tmp/tp-pq-fb-crash-out.log | sort -n | uniq > actual.txt
diff expected.txt actual.txt
# vide — zéro trou
```
**Résultat : zéro perte de contenu réellement transmis**, malgré
`queue.type: memory` (celui qui perdait ~50% avec l'input `tcp` en
partie 1). Seuls les 22 derniers numéros (`19979`-`20000`) manquent.

**Cette perte de 22 n'est pas imputable à Logstash ni à Filebeat** —
vérifié directement à la source :
```bash
grep -c 'SEQ-tp-pq-fb-' /var/log/messages   # s'arrête à 19978
```
Le générateur (`echo ... | logger`) a lui-même perdu ses 22 dernières
lignes avant même d'atteindre `/var/log/messages` — limite de
l'outillage de test, pas du système observé.

**Doublons réels : 533 sur 19978 (~2,7%)**, un vrai rejeu
"at-least-once", cohérent avec ce qu'on cherchait à confirmer. Un
premier comptage naïf avait donné un résultat aberrant
(`19445` valeurs vues "2 fois", `533` vues "4 fois") — piège de
méthode, pas un vrai phénomène : chaque event JSON produit par
Logstash contient le motif recherché **deux fois par ligne**
(`event.original` et `message` portent tous les deux la même
valeur), donc `grep -oP` comptait le mauvais niveau. Corrigé en
divisant les occurrences par 2 avant de les regrouper — révèle la
vraie distribution : `19445` events vus une seule fois, `533` vus
deux fois.

**Conclusion** : c'est le protocole d'accusé de réception de Filebeat
qui protège contre la perte, **indépendamment de `queue.type`** côté
Logstash. La queue mémoire disparaît bien avec le crash comme
toujours, mais Filebeat, n'ayant reçu aucune confirmation pour les
events non traités, les retransmet après coup — sans avoir besoin
d'une queue persistée en face. Contraste net avec la partie 1 : avec
l'input `tcp` (sans ack), `memory` perdait ~50% et `persisted`
limitait déjà la casse à ~7% résiduel — ici, `memory` seul avec
`beats` fait mieux que `persisted` seul avec `tcp`. La nature de
l'input compte au moins autant que `queue.type`, sinon plus, pour la
fiabilité réelle d'un pipeline.

`persisted`+`beats` non testé séparément — le résultat `memory`+`beats`
déjà sans perte rend la comparaison peu susceptible d'apporter plus
d'information à ce stade.

## Confirmation par la doc officielle

Les deux résultats de la phase 2 (zéro perte, doublons) correspondent
mot pour mot au comportement documenté de Filebeat, pas une
coïncidence :

> "Filebeat guarantees that events will be delivered to the
> configured output **at least once and with no data loss**."

> "If Filebeat shuts down while it's in the process of sending
> events, it does not wait for the output to acknowledge all events
> before shutting down. Any events that are sent to the output, but
> not acknowledged before Filebeat shuts down, are sent again when
> Filebeat is restarted. **This ensures that each event is sent at
> least once, but you can end up with duplicate events being sent to
> the output.**"

Confirme aussi *pourquoi* `queue.type` n'a pas été le facteur
déterminant — la garantie repose sur le **registre Filebeat**, côté
client, pas sur la queue Logstash côté serveur :

> "Filebeat is able to achieve this behavior because it stores the
> delivery state of each event in the registry file."

**Pourquoi seulement `533` doublons, pas plus** : l'ACK fonctionne par
accumulation façon fenêtre glissante (*"A reader can acknowledge the
'last event' received to support bulk acknowledgements"*), pas event
par event. Si le crash survient avant que le point de confirmation
n'ait atteint un lot en cours, Filebeat renvoie ce lot **entier**, même
la portion déjà réellement écrite côté sortie — d'où un rejeu limité
au(x) dernier(s) lot(s) non confirmés, pas tout le flux.

Piste repérée en marge, non explorée : `output.logstash` propose un
réglage `pipelining` (nombre de batches envoyés sans attendre l'ACK
avant que Filebeat ne bloque) — influence directement la taille de la
fenêtre "en vol" au moment d'un crash, potentiellement à creuser dans
un futur raffinement de ce test.

## Comparaison finale (toutes configurations testées)

| | `memory`+`tcp` | `persisted`+`tcp` | `memory`+`beats` |
|---|---|---|---|
| Envoyés | 5000 | 5000 | 20000 (dont 19978 réellement écrits à la source) |
| Perte réelle | 2494 (~50%) | 342 (~7%, résiduel réseau jamais reçu) | 0 (les 22 manquants imputables au générateur, pas au pipeline) |
| Doublons | 0 | 90 (rejeu "at-least-once" des events non acquittés) | 533 (~2,7% des events distincts, rejeu "at-least-once" — comptage initial faussé par `event.original`+`message` comptés deux fois par ligne dans le grep, corrigé en divisant par 2) |
| Facteur déterminant | Aucune protection (ni queue, ni input) | Queue persistée, mais input `tcp` sans ack limite la protection | Protocole d'ack de l'input `beats`, suffisant à lui seul même avec la queue la plus fragile |



## Sources (phase 2)

- [How Filebeat works — Filebeat Reference 8.19 (Elastic)](https://www.elastic.co/guide/en/beats/filebeat/8.19/how-filebeat-works.html) — garantie "at-least-once", registre, comportement au shutdown
- [Configure the Logstash output — Filebeat Reference 8.19 (Elastic)](https://www.elastic.co/guide/en/beats/filebeat/8.19/logstash-output.html) — option `pipelining`, ACK Logstash
- [Lumberjack PROTOCOL.md — logstash-forwarder (Elastic)](https://github.com/elastic/logstash-forwarder/blob/master/PROTOCOL.md) — ACK par fenêtre glissante ("last event received"), pas event par event
