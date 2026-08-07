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

## Phase 2 à prévoir : input `beats` (avec accusé de réception)

Ce TP a isolé la vraie cause du `~7%` résiduel perdu sur `persisted` :
la nature de l'input `tcp`, sans accusé de réception, pas le mécanisme
`persisted` en lui-même. À vérifier concrètement dans une prochaine
session : reprendre le même protocole de crash (générateur à débit
contrôlé, `CPUQuota` bridé, kill en pleine charge) sur le pipeline
`beats-tls` existant (TP `tp-filebeat-rh8103`) plutôt que sur un
input `tcp` brut — la doc cite `beats` explicitement comme "bien
protégé" par la persisted queue. Si l'hypothèse est juste, cette
perte résiduelle devrait disparaître complètement, ne laissant que le
comportement "at-least-once" (doublons, zéro trou) déjà observé ici.
