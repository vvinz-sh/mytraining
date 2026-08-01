# Logstash — Pipeline-to-pipeline : distributor pattern testé en pratique

Clôture le Palier 1 (dernier point restant). Complète la note 12
(pipelines isolés de `pipelines.yml`) avec un mécanisme distinct :
la communication **en mémoire** entre pipelines au sein de la même
instance.

## Distinction fondamentale avec les pipelines isolés (note 12)

Les pipelines `pipelines.yml` testés précédemment (`main`, `syslog`,
`test-generator`) étaient **isolés** — aucune communication entre eux.
`pipeline-to-pipeline` est différent : `input { pipeline { address =>
"xxx" } }` agit comme un **serveur virtuel local**, et `output {
pipeline { send_to => "xxx" } }` envoie des events **directement**
vers cette adresse, en mémoire, sans passer par le disque ni le
réseau.

## Le "distributor pattern" (exemple officiel)

```
input { beats { port => 5044 } }
output {
  if [type] == apache { pipeline { send_to => weblogs } }
  else if [type] == system { pipeline { send_to => syslog } }
  else { pipeline { send_to => fallback } }
}
```
Un premier pipeline reçoit tout, puis **route** chaque event vers un
pipeline dédié selon son type — chacun avec son propre traitement, et
potentiellement sa propre sortie (même vers des clusters
Elasticsearch différents).

## Comparaison avec notre propre approche (blocs `if` dans un seul pipeline)

Question posée : quel est l'avantage réel de séparer chaque type
(`java-app`/`backup-job`/`kernel`) en pipelines distincts plutôt que
de garder les blocs conditionnels dans un seul pipeline comme on l'a
fait (notes 05/07/08) ?

**Au-delà de la simple lisibilité** : rappel de la note 12 —
`pipeline.workers` s'applique **par pipeline**, pas globalement.
Dans un seul pipeline partagé, un filtre lent/gourmand sur un type
(ex : `kernel`) **affame** les workers des autres types
(`java-app`/`backup-job`), puisqu'ils partagent le même pool. Avec
des pipelines séparés via `pipeline-to-pipeline`, chaque type peut
avoir son propre dimensionnement (`pipeline.workers`, `queue.type`)
— un ralentissement sur l'un n'affecte plus les autres.

## Contrepartie : coût mémoire de la duplication

Trouvé dans la doc officielle : *"Logstash must duplicate each event
in full on the Java heap for each downstream pipeline"* — chaque
event envoyé via `send_to` est **entièrement dupliqué** en mémoire,
pas juste référencé. Rappel direct du TP LLM local : la mémoire heap
JVM est une ressource finie (`-Xms1g -Xmx1g`), et cette duplication
pèse dessus.

**Décision retenue pour notre lab** : le compromis (isolation de
performance contre coût mémoire de duplication) ne se justifie pas
pour un volume de test aussi faible que le nôtre (3-4 types de
processus) — mécanisme à réserver pour un vrai contexte de production
à fort volume, où l'isolation devient réellement nécessaire. Même
logique de proportionnalité déjà appliquée pour écarter
`queue.type: persisted` en lab, et pour choisir `grok` seul plutôt
que le combo `dissect`+`grok` au début du Palier 2.

## Test réalisé

`pipelines.yml` (copie versionnée dans `pipeline-to-pipelines.yml`) :

```yaml
- pipeline.id: distributeur
  config.string: |
    input {
      generator { count => 3 type => "typeA" }
      generator { count => 3 type => "typeB" }
    }
    output {
      if [type] == "typeA" {
        pipeline { send_to => branche_a }
      } else if [type] == "typeB" {
        pipeline { send_to => branche_b }
      }
    }

- pipeline.id: branche-a
  config.string: |
    input { pipeline { address => branche_a } }
    filter { mutate { add_field => { "traite_par" => "pipeline_a" } } }
    output { stdout {} }

- pipeline.id: branche-b
  config.string: |
    input { pipeline { address => branche_b } }
    filter { mutate { add_field => { "traite_par" => "pipeline_b" } } }
    output { stdout {} }
```

**Résultat validé** : `traite_par: pipeline_a` pour les events
`typeA`, `traite_par: pipeline_b` pour `typeB` — le routage via
`send_to` fonctionne exactement comme prévu, chaque branche
applique son propre filtre distinct. `distributeur` se termine après
épuisement de ses deux `generator` (auto-terminaison déjà connue,
note 12) — comportement attendu, pas un bug.

## Résumé

1. `pipeline-to-pipeline` communique **en mémoire** entre pipelines
   de la même instance — distinct des pipelines isolés testés
   précédemment
2. Le vrai avantage n'est pas juste la lisibilité : isoler le
   dimensionnement (`pipeline.workers`) par type évite qu'un type
   lent n'affame les autres, contrairement à des blocs `if` partagés
   dans un seul pipeline
3. Contrepartie réelle : duplication complète de chaque event en
   mémoire par pipeline destinataire — un coût à mettre en balance
   avec le volume réel, pas un mécanisme à activer par défaut
4. Pour notre lab, le compromis ne se justifie pas — cohérent avec
   les décisions similaires déjà prises (queue persistée, dissect
   seul)

## Lien avec les notes existantes

`12-pipelines-config.md` (pipelines isolés, `pipeline.workers` par
pipeline, `generator` auto-terminaison), `05-grok-filtre-conditionnel-greedydata-data.md`
et suivantes (notre propre approche par blocs `if` dans un seul
pipeline, point de comparaison), `tp-llm-local-phase3-resultat.md`
(gestion de la mémoire heap JVM, contrainte comparable).

## Sources

- [Pipeline-to-pipeline communication (Elastic, 8.19)](https://www.elastic.co/guide/en/logstash/8.19/pipeline-to-pipeline.html)
