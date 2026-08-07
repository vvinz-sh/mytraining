# Logstash — DLQ : tour d'horizon des options de configuration

Complète les notes 30 (scope du DLQ) et le TP `tp-logging-dlq`
(activation, retraitement, `clean_consumed`). Passage en revue des
réglages disponibles, sans nouveau test pratique — juste la lecture
de la doc officielle pour fixer ce qui existe.

## Portée : global (`logstash.yml`) vs par pipeline (`pipelines.yml`)

La plupart des réglages `dead_letter_queue.*` peuvent se poser aux
deux niveaux — `logstash.yml` pour un défaut global, ou directement
dans `pipelines.yml` pour surcharger ce défaut sur un pipeline
précis. Confirmé en pratique dans le TP : `dead_letter_queue.enable`
posé uniquement pour `tp-dlq`, sans toucher au comportement des
autres pipelines de l'instance.

**Chaque pipeline a sa propre queue**, jamais partagée — stockée par
défaut sous `path.data/dead_letter_queue/<pipeline_id>/` (donc
`.../dead_letter_queue/tp-dlq/` dans le TP). `path.dead_letter_queue`
permet de changer cet emplacement racine. Un même chemin de DLQ ne
peut pas être utilisé par deux instances Logstash différentes.

## Réglages côté écriture (le pipeline qui produit des erreurs)

- **`dead_letter_queue.enable`** (bool, défaut `false`) — désactivé
  par défaut, à activer explicitement (déjà pratiqué)
- **`dead_letter_queue.max_bytes`** (défaut `1024mb`) — taille max
  par pipeline ; au-delà, les nouvelles entrées sont refusées ou de
  vieilles entrées supprimées, selon `storage_policy`
- **`dead_letter_queue.storage_policy`** — `drop_newer` (défaut :
  arrête d'accepter du nouveau une fois la limite atteinte) ou
  `drop_older` (supprime les plus anciennes pour faire de la place)
- **`dead_letter_queue.retain.age`** — purge automatique par âge
  (`2d`, `1h`...), pas de défaut, unité obligatoire. Vérifiée au
  moment des écritures et à l'arrêt du pipeline — donc des events
  expirés peuvent rester visibles un moment avant la purge effective,
  un lecteur pourrait tomber dessus entre-temps
- **`dead_letter_queue.flush_interval`** (défaut `5000` ms, min
  `1000`) — délai avant qu'un fichier temporaire d'écriture soit
  scellé en segment définitif et devienne lisible. Une valeur basse
  = plus de petits segments sur des écritures peu fréquentes ; une
  valeur haute = plus de latence avant qu'un event devienne
  disponible en lecture
- **`dead_letter_queue.flush_check_interval`** (défaut `1000` ms, min
  `1000`) — fréquence de vérification des segments à sceller ; latence
  pire cas = `flush_interval` + `flush_check_interval`

## Réglages côté lecture (l'input `dead_letter_queue`, pipeline de retraitement)

- **`path`** — dossier racine du DLQ (le même que celui du pipeline
  producteur)
- **`pipeline_id`** (défaut `"main"`) — quel pipeline producteur lire
- **`commit_offsets`** — retenir la position de lecture pour ne pas
  rejouer deux fois ; `false` pour explorer/itérer plusieurs fois sans
  garder d'état (déjà pratiqué en observation avant la version finale
  du TP)
- **`clean_consumed`** — supprime réellement les segments
  entièrement lus, nécessite `commit_offsets => true` (sinon erreur
  de config), disponible depuis Logstash 8.4.0. Sans lui,
  `commit_offsets` seul ne fait que suivre la position, sans jamais
  libérer d'espace disque (constaté dans le TP)
- **`start_timestamp`** — reprendre la lecture à partir d'un instant
  précis, utile pour ignorer un historique ancien plutôt que tout
  relire depuis le début

## Vider complètement le DLQ

Pas d'action API pour ça — nécessite d'**arrêter le pipeline
producteur**, puis de supprimer directement le dossier
`path.data/dead_letter_queue/<pipeline_id>/` sur le disque. Le
pipeline recrée une DLQ neuve à son prochain démarrage.

## Résumé

1. Réglages disponibles aux deux niveaux (global `logstash.yml`,
   ou par pipeline dans `pipelines.yml`) — chaque pipeline garde sa
   propre queue, jamais partagée
2. Taille et rétention pilotées par `max_bytes`/`storage_policy`
   (limite dure) et `retain.age` (purge par âge, appliquée de façon
   différée, pas immédiate)
3. `flush_interval`/`flush_check_interval` gouvernent le compromis
   taille des segments vs latence avant disponibilité en lecture
4. Côté lecture, `commit_offsets` ≠ suppression — `clean_consumed`
   est le réglage qui libère vraiment l'espace disque, et dépend de
   `commit_offsets => true`
5. Vider le DLQ à la main nécessite d'arrêter le pipeline producteur,
   pas d'API pour le faire à chaud

## Lien avec les notes existantes

`30-dead-letter-queue-native.md` (scope du DLQ, les deux cas
couverts), `tp-logging-dlq-resultat.md` (activation, `plugin_type`
pour distinguer les causes, découverte de `clean_consumed` en
pratique).

## Sources

- [Dead letter queues (DLQ) — Logstash Reference (Elastic)](https://www.elastic.co/docs/reference/logstash/dead-letter-queues)
- [Dead_letter_queue input plugin — Logstash Reference (Elastic)](https://www.elastic.co/docs/reference/logstash/plugins/plugins-inputs-dead_letter_queue)
