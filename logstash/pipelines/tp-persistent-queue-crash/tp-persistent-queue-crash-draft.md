# TP — Persistent queue : simuler un crash en cours de traitement, vérifier la reprise (draft)

Statut : **design posé, pas encore exécuté**. Dernier TP du Palier 4.
Met en pratique la théorie déjà posée au Palier 1 (note 09,
`queue.type: memory` vs `persisted`) — jamais testé concrètement
jusqu'ici, uniquement raisonné sur le papier.

## Contexte

Note 09 avait établi, sans le tester : `queue.type: memory` (défaut)
perd tout ce qui n'a pas atteint `output` en cas de crash — "poof",
sans trace. `queue.type: persisted` comble ce trou via un accusé de
réception ("acked"), un event n'étant retiré de la queue qu'une fois
confirmé jusqu'au bout. Ce TP construit un scénario de crash
reproductible pour observer, sur les deux configurations, ce qui
survit réellement — pas seulement ce que la doc affirme.

## Étape 1 — Construire un scénario où le crash a une fenêtre d'impact prévisible

Deux leviers retenus, sans `sleep` artificiel :
- **Fichier source volumineux déjà disponible** : `dataset_entrainement`
  (module `ia-concepts`, >3 Mo) — élargit naturellement la fenêtre de
  traitement, sans fabriquer un cas de test artificiel
- **Réduction du nombre de vCPU** alloués à la VM — ralentit le débit
  réel de traitement, comportement plus honnête qu'un délai artificiel
  injecté dans la config elle-même

Objectif : pouvoir tuer le process (`kill -9`, pas un arrêt propre)
**pendant** que des events sont encore "en vol" — lus en entrée, pas
encore confirmés en sortie.

## Étape 2 — Baseline avec `queue.type: memory` (comportement attendu : perte)

1. Lancer le pipeline sur un jeu de N lignes connu (compter précisément)
2. `kill -9` le process à un moment délibérément choisi en cours de
   traitement
3. Relancer le pipeline, laisser terminer
4. Compter les events réellement arrivés en sortie — comparer à N

Attendu (à confirmer, pas à supposer) : moins de N events arrivés,
perte silencieuse des events qui étaient "en vol" au moment du kill.

## Étape 2bis — Observer la queue via l'API pendant le traitement

```
GET /_node/stats/pipelines
```
Champ à surveiller, distinct de celui du DLQ (note 30) :
```json
"queue": {
  "type": "persisted",
  "events": 42,
  "capacity": { "queue_size_in_bytes": ..., "max_queue_size_in_bytes": ... },
  "data": { "path": "/chemin/vers/queue/main" }
}
```
`queue.events` (nombre d'events actuellement dans la queue) et
`queue.capacity.queue_size_in_bytes` (taille réelle sur disque) — à
observer croître pendant le traitement du fichier volumineux, avant
même de déclencher le crash. Point de vigilance repéré dans un ticket
Elastic (#13832) : ces stats peuvent se figer pendant un drain propre
(`queue.drain: true` sur `SIGTERM`) — sans impact ici puisque le kill
utilisé est un `kill -9`, pas un arrêt propre, mais à garder en tête
si un jour la comparaison inclut aussi un arrêt propre.

## Étape 3 — Même scénario avec `queue.type: persisted`

Répéter exactement la même procédure (même N, même point de kill si
possible pour une comparaison honnête), avec `queue.type: persisted`
activé cette fois. Attendu : N events arrivés en sortie au final,
sans perte — à vérifier par comptage, pas par confiance dans la doc.

## Étape 4 — Vérifier le mécanisme exact de la récupération

Point resté flou dans la note 09, à trancher ici par l'observation :
la récupération après crash avec `persisted` vient-elle (a) du fait
que les events "en vol" restent physiquement stockés sur disque dans
la queue persistée elle-même (indépendamment du `sincedb` du plugin
`file`), ou (b) du fait que le `sincedb` n'avance sa position de
lecture qu'une fois l'event acquitté, donc le fichier source est
simplement **relu** depuis ce point après redémarrage ? Les deux
mécanismes aboutissent au même résultat visible (pas de perte), mais
ne sont pas la même chose — à distinguer en inspectant le contenu du
répertoire `queue.type: persisted` (`path.queue`) et l'état du
`sincedb` juste après le crash, avant le redémarrage.

## Ce qu'il faudra vérifier/clarifier en exécutant

- Mécanisme de ralentissement retenu pour élargir la fenêtre de crash
  (à choisir en pratique, pas deviné à l'avance)
- Nombre exact d'events perdus en `memory` (comparé à N) — pour avoir
  un vrai chiffre, pas juste "il y a une perte"
- Confirmation qu'aucun event n'est perdu en `persisted`, par comptage
- Mécanisme réel de la récupération (queue sur disque vs `sincedb`
  retardé) — à trancher en observant, pas en supposant depuis la note 09
- Coût réel observé (latence, taille disque) de `persisted` par
  rapport à `memory` sur ce volume de test
- Confirmer que `queue.events`/`queue.capacity.queue_size_in_bytes`
  (persisted queue) et `dead_letter_queue.queue_size_in_bytes` (note
  30) sont bien deux métriques distinctes de l'API, pas la même chose
  sous deux noms

## Compétences pratiquées

- Construction d'un scénario de crash reproductible et mesurable
  (comptage avant/après, pas une impression qualitative)
- Vérification empirique d'un mécanisme jusqu'ici seulement raisonné
  sur le papier (note 09)
- Distinction entre deux mécanismes plausibles produisant le même
  résultat observable en surface

## Lien avec les notes existantes

`09-configuration-logstash-java.md` (`queue.type`, `sincedb` — théorie
posée, jamais testée jusqu'ici), `16-panorama-beats.md` (triptyque de
fiabilité — contre-pression, persisted queue, DLQ, chacun pour un
scénario différent), `30-dead-letter-queue-native.md` (DLQ, mécanisme
complémentaire mais disjoint de la persisted queue).
