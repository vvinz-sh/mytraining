# Logstash — Panorama des endpoints de l'API (port 9600)

Clôture le dernier point théorique du Palier 1. Panorama d'ensemble
avant la pratique déjà amorcée (note 14, `duration_in_millis`) et
prévue plus tard (`/_node/logging` en Palier 4, `http_poller` vers
Elasticsearch en Palier 5).

## Vue d'ensemble : très majoritairement de la lecture

- **`/`** — infos générales (host, version)
- **`/_node`** — infos statiques (OS, JVM, réglages de pipeline)
- **`/_node/plugins`** — liste des plugins installés
- **`/_node/stats`** (et sous-types : `process`, `jvm`, `pipelines`,
  `os`, `reloads`) — métriques runtime, déjà utilisé en note 14
  (`duration_in_millis` par plugin filter)
- **`/_node/hot_threads`** — threads Java les plus consommateurs de
  CPU, utile pour du diagnostic de performance en direct

## L'exception : `/_node/logging`, seul endpoint d'action

Tous les endpoints ci-dessus sont en **lecture seule** (GET). Un seul
sort de ce cadre : **`/_node/logging`** accepte un **PUT**, permettant
de changer le **niveau de log à chaud**, sans redémarrer l'instance —
un vrai levier d'action, pas juste du monitoring passif. Prévu en
pratique au Palier 4, pour diagnostiquer une hausse d'échecs
(`_grokparsefailure`) sans interrompre le pipeline en pleine
investigation.

## Piège vérifié : pas d'endpoint pour déclencher un rechargement

Question posée en amont (avant de documenter le reste) : existe-t-il
un endpoint pour **déclencher** un rechargement de pipeline via
l'API, en complément de `/_node/logging` ?

**Réponse, vérifiée** : non. `/_node/stats/reloads` existe bien, mais
il est **lui aussi en lecture seule** — il rapporte des statistiques
sur les rechargements déjà survenus (succès/échecs), il n'en
**déclenche** aucun. Le vrai déclenchement se fait uniquement par
`config.reload.automatic` (surveillance de fichier, note 06) ou par
signal `SIGHUP` au niveau OS — jamais par un appel HTTP.

Trouvaille amusante : un **ticket ouvert** sur le dépôt officiel
Logstash (depuis 2020) demande précisément l'ajout d'un endpoint
`PUT /_node/pipelines/:id/_reload` — une fonctionnalité réclamée par
la communauté, toujours absente de l'API actuelle.

## Résumé

1. L'API est très majoritairement en lecture — monitoring, pas
   pilotage
2. `/_node/logging` (PUT) est la seule vraie exception, un endpoint
   d'action réel
3. Aucun endpoint de déclenchement de rechargement n'existe —
   `/_node/stats/reloads` ne fait que rapporter, jamais déclencher ;
   le vrai rechargement passe par surveillance de fichier ou SIGHUP

## Lien avec les notes existantes

`14-test-dissect.md` (première utilisation pratique de
`/_node/stats/pipelines`), `06-options-cli-confort.md`
(`--config.reload.automatic`, mécanisme réel de rechargement),
README Palier 4 (`/_node/logging` en pratique prévue), README
Palier 5 (`http_poller` vers Elasticsearch).

## Sources

- [Node Stats API (Elastic, 8.19)](https://www.elastic.co/guide/en/logstash/8.19/node-stats-api.html)
- [Monitoring Logstash Filters (Elastic Blog)](https://www.elastic.co/blog/monitoring-logstash-filters)
- [Logstash pour les devs — série (Blog Pal'Temps, fr)](https://blog.paltemps.fr/logstash-00-introduction)
