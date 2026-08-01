# Logstash — Filtre date : réécrire @timestamp correctement

Clôture le thème Parsing — dernier point en attente depuis le début
du module. Répond à une question de fond, pas juste mécanique :
pourquoi et comment réécrire `@timestamp`, et comment préserver
l'information perdue en le faisant.

## Pourquoi un simple `rename` ne suffit pas

Tentative naïve envisagée : `mutate { rename => { "timestamp" =>
"@timestamp" } }`. Insuffisant, et pas seulement à cause de la perte
d'info (année, précision, fuseau) — le vrai problème est le **type**
de la donnée. `@timestamp` n'est pas qu'un champ bien nommé, c'est un
objet **date typé** en interne, sur lequel Elasticsearch (Palier 5)
sait faire tris chronologiques et agrégations par intervalle. Un
`rename` ne change jamais le type : le champ s'appellerait
`@timestamp` mais resterait une simple chaîne de texte brute. Le
filtre `date` **parse** le texte pour produire une vraie valeur
temporelle typée — un travail que `rename` ne fait jamais.

## Syntaxe Joda-Time et test réel

```
filter {
  dissect {
    mapping => { "message" => "%{timestamp} %{+timestamp} %{+timestamp} %{hostname} %{prog}[%{pid}]: %{msg}" }
  }
  date {
    match => [ "timestamp", "MMM dd HH:mm:ss" ]
    timezone => "Europe/Paris"
  }
}
```

Testé sur :
```
Jul 21 08:30:1 rh8102 cron[2001]: (root) CMD (run-parts /etc/cron.hourly)
```

Deux points vérifiés empiriquement plutôt que devinés depuis la doc :

- **Seconde sans zéro initial (`1` au lieu de `01`)** : parsée
  correctement malgré le motif `ss` (deux chiffres attendus a priori)
  — la tolérance concerne le *parsing*, pas le *formatage* en sortie,
  où le zéro-padding s'appliquerait strictement
- **Année absente du texte source** : `@timestamp` a affiché
  `2026-07-21` — confirmé que l'année manquante est comblée par
  l'**année en cours au moment du traitement**, pas une valeur fixe
  comme 1970

## Piège concret : logs historiques et année manquante

Conséquence directe du point précédent, pour un scénario réel
(traiter un lot d'anciens logs syslog aujourd'hui) : si le texte
source ne contient pas d'année, le filtre `date` y substituera
silencieusement l'année **du traitement**, pas l'année réelle de
l'événement — une corruption de donnée sans la moindre erreur ni
warning.

**Stratégie de mitigation retenue** : prioriser une source fiable
d'année (métadonnée externe — nom de fichier, date de modification du
fichier) plutôt que le texte du log lui-même ; si cette source
n'existe pas, injecter manuellement l'année connue dans le champ
avant le filtre `date`, en dernier recours.

## Fuseau horaire : implicite vs explicite

Sans `timezone` précisé, le filtre utilise le fuseau **système** de
la machine qui exécute Logstash (confirmé dans la doc officielle :
*"Custom parsing formats use the JVM's default locale and time
zone"*). Risque identifié : de nombreuses VM/conteneurs sont réglés en
UTC par défaut, indépendamment de leur localisation physique réelle —
déplacer le même pipeline sur une autre machine changerait le résultat
silencieusement, sans toucher à la config. Cohérent avec la discipline
déjà suivie sur ce module (préférer l'explicite à l'implicite,
`queue.type`/`pipeline.workers` déjà traités ainsi) : `timezone` fixé
explicitement (`Europe/Paris`), plutôt que de dépendre du réglage
système ambiant.

## Pourquoi réécrire @timestamp est la bonne pratique (et pas une perte)

Question de fond posée avant de conclure : `@timestamp` par défaut
indique l'heure de **réception** par Logstash — une information jugée
utile à ne pas perdre en l'écrasant par le vrai timestamp de
l'événement.

**Réponse trouvée dans ECS** (Elastic Common Schema, référentiel
officiel) : trois timestamps distincts sont prévus, avec un ordre
chronologique attendu :
```
@timestamp < event.created < event.ingested
```

- **`@timestamp`** — *"quand l'événement s'est réellement produit"*
  (champ obligatoire ECS) — c'est précisément ce que le filtre `date`
  doit écraser avec le vrai timestamp syslog, **conformément** à la
  norme, pas en contradiction avec elle
- **`event.created`** — *"le moment où un agent ou un pipeline a vu
  l'événement"* — exactement l'information qu'on voulait préserver
- **`event.ingested`** — le moment d'arrivée dans le stockage final
  (Elasticsearch), une troisième étape plus tardive

Pas besoin d'inventer un nom personnalisé (`@timestamp_syslog`
envisagé un temps) — le champ standard existe déjà.

## Pattern final testé

```
filter {
  dissect {
    mapping => { "message" => "%{timestamp} %{+timestamp} %{+timestamp} %{hostname} %{prog}[%{pid}]: %{msg}" }
  }
  mutate {
    copy => { "@timestamp" => "[event][created]" }
  }
  date {
    match => [ "timestamp", "MMM dd HH:mm:ss" ]
    timezone => "Europe/Paris"
  }
}
```

Résultat validé : `event.created` conserve l'heure de réception
réelle, `@timestamp` affiche le vrai timestamp extrait — les deux
coexistent, avec les noms de champs standards ECS plutôt qu'une
convention personnelle.

## Piste ouverte

ECS mérite sa propre présentation dédiée (principes, autres field
sets courants) plutôt qu'une simple mention au détour du filtre
`date` — prévu pour le thème Logs structurés & écosystème Elastic.

## Résumé

1. `rename` change le nom d'un champ, jamais son type — le filtre
   `date` fait un vrai travail de parsing que `rename` ne fait jamais
2. Le parsing Joda-Time tolère l'absence de zéro initial ; l'année
   manquante est comblée par l'année du traitement, pas une valeur
   fixe — piège réel pour du traitement de logs historiques
3. `timezone` doit être explicite, jamais laissé au réglage système
   implicite de la machine d'exécution
4. Écraser `@timestamp` avec le vrai timestamp de l'événement est la
   pratique ECS standard, pas une perte d'information — `event.created`
   est le champ prévu pour préserver l'heure de réception

## Lien avec les notes existantes

`04-construction-premier-pattern-grok.md` (pattern de base),
`12-pipelines-config.md` (note sur l'ordre d'arrivée non garanti,
motivant l'intérêt du vrai timestamp), `14-test-dissect.md` (pattern
`+timestamp` réutilisé ici).

## Sources

- [Date filter plugin (Elastic, 8.19)](https://www.elastic.co/docs/reference/logstash/plugins/plugins-filters-date)
- [ECS — Implementation patterns (Elastic)](https://www.elastic.co/docs/reference/ecs/ecs-principles-implementation)
- [Logstash Date Filter Plugin (Pulse)](https://pulse.support/kb/logstash-date-filter-plugin)
