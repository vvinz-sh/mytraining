# Logstash — Configuration globale : logstash.yml et jvm.options

Complète le Palier 1 — fondations laissées de côté au moment du
premier pipeline, comblées ici : `logstash.yml` (queue, workers) et
`jvm.options` (heap, GC, diagnostic mémoire).

## `logstash.yml` : réglages actifs par défaut sur le paquet officiel

Sur 396 lignes, seulement deux réglages actifs (le reste en
commentaires) :
```
path.data: /var/lib/logstash
path.logs: /var/log/logstash
```

Cohérent avec le standard FHS (Filesystem Hierarchy Standard) déjà
identifié en pratique au Palier 1 : `/usr/share/logstash` contient les
binaires immuables (gérés par le paquet, remplacés à chaque mise à
jour), `/var` contient les données mutables qui doivent survivre à une
mise à jour — c'est précisément pourquoi un dossier `path.data` perso
avait dû être créé pour les tests manuels (le vrai `/var/lib/logstash`
appartient à l'utilisateur système `logstash`, pas à l'utilisateur
courant).

## Type de queue interne : `queue.type`

Commenté par défaut (`memory`) :
```
# queue.type: memory
```

- **`memory`** (défaut) : queue en RAM. Si le process crash, tout ce
  qui n'a pas encore atteint `output` est perdu, sans trace — "poof".
- **`persisted`** : queue sur disque, avec accusé de réception
  ("acked") — un event n'est retiré de la queue qu'une fois confirmé
  jusqu'au bout de `output`. Coût : écriture/lecture disque plus
  lentes que la RAM, surtout en écriture.

### Piège découvert : le sincedb ne protège pas contre ce risque

Question posée : le plugin `file` (via son mécanisme `sincedb`, qui
retient la position de lecture dans le fichier) protège-t-il contre la
perte d'events en cas de crash avec `queue.type: memory` ?

**Réponse, vérifiée** : non, seulement partiellement. Le sincedb avance
dès que Logstash **lit** une ligne — pas quand cette ligne a fini son
trajet complet jusqu'à `output`. Scénario de perte réel : ligne lue
(sincedb avance) → entre dans la queue mémoire → crash avant
d'atteindre `output` → au redémarrage, le sincedb indique "déjà lu",
donc la ligne n'est **jamais** relue, et elle n'a jamais atteint sa
destination non plus. `queue.type: persisted` comble précisément ce
trou en ne faisant avancer la progression qu'une fois l'event confirmé
jusqu'au bout.

### Décision pour notre lab

`queue.type: memory` conservé — le coût de `persisted` (lenteur
disque) ne se justifie pas pour un pipeline `stdin` de test sans
notion de criticité. À reconsidérer explicitement pour un vrai
environnement de production, ou à déléguer à un système externe
(Kafka) pour des enjeux plus élevés — la queue persistée de Logstash
étant plutôt un filet de sécurité pour des volumes modestes, pas la
solution ultime à fort enjeu.

## `pipeline.workers` : parallélisme entre events, pas entre filtres

```
# pipeline.workers: 2  (défaut : nombre de cœurs CPU de la machine)
```

Clarification importante : le parallélisme s'applique **entre events
différents**, pas entre les filtres d'un même event — la séquentialité
`filter` par `filter` pour un event donné (vue dès la note 03) reste
intacte. Plusieurs events distincts peuvent traverser le pipeline
**simultanément**, chacun sur son propre worker.

**Conséquence pratique** : l'ordre d'arrivée à `output` n'est **pas**
garanti identique à l'ordre d'arrivée en entrée. Un event traversant
moins de filtres (ex : une ligne `systemd` simple) peut dépasser à
`output` un event arrivé avant lui mais plus long à traiter (ex : une
ligne `java-app` passant par un second `grok` conditionnel).

**Pourquoi ça ne pose pas de problème si on capture le vrai
timestamp** : reconstituer l'ordre chronologique reste possible après
coup en triant sur le `timestamp` extrait du contenu du log (Grok),
pas sur l'ordre physique d'arrivée dans le fichier de sortie ni sur
`@timestamp` (heure de réception, elle-même potentiellement dans le
désordre). Ça donne un sens concret au filtre `date` resté en attente
depuis le début du Palier 2 : remplacer `@timestamp` par le vrai
timestamp du log n'est pas qu'une question de propreté, c'est ce qui
rend un tri chronologique fiable possible malgré le parallélisme.

## `jvm.options` : réglages actifs

```
-Xms1g
-Xmx1g
11-13:-XX:+UseConcMarkSweepGC
11-13:-XX:CMSInitiatingOccupancyFraction=75
11-13:-XX:+UseCMSInitiatingOccupancyOnly
-Djava.awt.headless=true
-Dfile.encoding=UTF-8
-Djruby.compile.invokedynamic=true
-XX:+HeapDumpOnOutOfMemoryError
-Djava.security.egd=file:/dev/urandom
-Dlog4j2.isThreadContextMapInheritable=true
```

### `Xms` = `Xmx` : pourquoi une taille fixe plutôt qu'élastique

Les deux valeurs identiques (1 Go) empêchent la JVM de redimensionner
son heap en cours d'exécution. Raison : un redimensionnement de heap
s'accompagne d'une pause de l'application (garbage collection complet,
voire arrêt momentané) — inacceptable sur un pipeline de streaming où
les events doivent circuler sans à-coups.

**Contrepartie** : ce 1 Go est réservé en **continu**, même quand
Logstash ne traite rien — indisponible pour le reste de la machine.
Écho direct au TP LLM local : l'empreinte VRAM du modèle chargé (7.38
Go pour le 8B) posait exactement ce même type de contrainte, occupée
en permanence indépendamment de l'activité réelle du calcul.

### Syntaxe conditionnelle par version JVM : `11-13:`

Les trois lignes CMS (Concurrent Mark Sweep, un garbage collector
déprécié et retiré des JDK récents) ne s'appliquent que si la JVM
détectée est en version 11 à 13. Sur cette VM (JDK 21 bundlé), ces
lignes sont silencieusement **ignorées** — du code mort en pratique
ici, mais utile pour un fichier `jvm.options` distribué tel quel à des
environnements plus anciens n'ayant pas encore mis à jour leur Java
système. Permet à Elastic de couvrir plusieurs générations de JVM dans
un seul fichier, sans en maintenir des variantes séparées.

### `HeapDumpOnOutOfMemoryError` : l'équivalent JVM de ce qui a manqué en QLoRA

Génère un instantané complet de la mémoire Java au moment précis d'un
`OutOfMemoryError`, sauvegardé sur disque pour analyse a posteriori
(ex : Eclipse MAT) — précisément ce qui a manqué lors du diagnostic
des multiples `CUDA out of memory` du TP LLM local, où il avait fallu
procéder par élimination successive (`nvidia-smi`, tracebacks Python,
tests d'hypothèses un par un) faute d'un instantané direct de l'état
mémoire au moment du crash.

## Résumé

1. `path.data`/`path.logs` séparés du répertoire d'installation — même
   logique FHS que `/usr` vs `/var`, déjà rencontrée en pratique
2. `queue.type: memory` (défaut) perd tout en cas de crash ; le
   sincedb du plugin `file` ne protège que la position de lecture, pas
   la garantie de traitement complet — nuance importante à ne pas
   confondre
3. `pipeline.workers` parallélise entre events, pas entre filtres d'un
   même event — casse la garantie d'ordre d'arrivée à `output`, d'où
   l'intérêt réel du futur filtre `date`
4. `Xms = Xmx` sacrifie la flexibilité mémoire pour éviter les pauses
   de redimensionnement en cours d'exécution — écho direct au
   dimensionnement VRAM du TP LLM local
5. La syntaxe `version:option` dans `jvm.options` permet de couvrir
   plusieurs générations de JDK dans un seul fichier
6. `HeapDumpOnOutOfMemoryError` aurait fourni un diagnostic direct là
   où on avait dû procéder par élimination lors des crashs CUDA

## Lien avec les notes existantes

`03-premier-pipeline-stdin-stdout-filter-mutate.md` (`path.data` perso
déjà créé en pratique), `tp-llm-local-phase3-resultat.md` (diagnostic
VRAM par élimination, dimensionnement mémoire fixe vs élastique).

## Sources

- [logstash.yml (Elastic, 8.19)](https://www.elastic.co/guide/en/logstash/8.19/logstash-settings-file.html)
- [Persistent Queues (Elastic, 8.19)](https://www.elastic.co/guide/en/logstash/8.19/persistent-queues.html)
- [File input plugin (Elastic Plugins)](https://www.elastic.co/docs/reference/logstash/plugins/plugins-inputs-file)
