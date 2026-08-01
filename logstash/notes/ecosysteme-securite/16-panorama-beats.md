# Logstash — Panorama des outils Beats

Complète la note 01 (Palier 0) — les Beats sont l'autre pilier de
l'écosystème de collecte Elastic, jamais détaillés jusqu'ici malgré
plusieurs mentions de Filebeat en passant (notes 02, README Palier 3).

## Principe commun : libbeat

Tous les Beats sont construits sur **libbeat**, une bibliothèque
commune écrite en Go, qui fournit l'API partagée pour envoyer la
donnée, configurer les inputs, gérer les logs internes. Chaque Beat
est **mono-tâche** — il fait une seule chose, contrairement à
Logstash qui peut tout enchaîner (input/filter/output) dans un seul
process.

## La famille

- **Filebeat** — suit et expédie des fichiers de logs. Le plus
  répandu, celui prévu pour notre futur TP RH8103.
- **Metricbeat** — récupère des métriques système/services (CPU,
  mémoire, services applicatifs).
- **Packetbeat** — surveille le réseau en analysant les paquets
  directement (sniffing).
- **Winlogbeat** — expédie les journaux d'événements Windows,
  installable comme service Windows ; conserve la position de lecture
  sur disque pour reprendre après un redémarrage (même logique que le
  `sincedb` du plugin `file` de Logstash, note 12).
- **Heartbeat** — ping des services distants pour vérifier leur
  disponibilité.
- **Auditbeat** — collecte des données d'audit/sécurité système.
- **Osquerybeat** — exécute Osquery et gère l'interaction avec lui
  (plus récent que les Beats historiques).

## Beats vers Logstash ou directement Elasticsearch

Un Beat peut envoyer sa donnée **directement** à Elasticsearch, ou
**via Logstash** pour un traitement/enrichissement supplémentaire
avant indexation — c'est ce second cas qui concerne notre futur TP
(Filebeat sur RH8103 → Logstash sur Rocky9).

## Découverte : un mécanisme de contre-pression intégré

Point intéressant, qui recoupe directement la note 12 (queue interne,
fiabilité) : *"Filebeat utilise un protocole sensible à la
contre-pression en envoyant vers Logstash ou Elasticsearch — si
Logstash est occupé à traiter de la donnée, il en informe Filebeat
pour qu'il ralentisse sa lecture. Une fois la congestion résolue,
Filebeat reprend son rythme initial."*

Un mécanisme de flux différent de `queue.type: persisted` (qui
protège contre la perte en cas de **crash**), mais complémentaire :
la contre-pression protège contre la **saturation** en cas de
ralentissement temporaire, sans qu'aucune donnée ne soit perdue ni
qu'un crash ne survienne. Deux garde-fous distincts pour deux
problèmes distincts.

**Filebeat n'est pas un remplaçant de Logstash** — les deux sont
pensés pour fonctionner ensemble, pas l'un à la place de l'autre.

## Triptyque des mécanismes de fiabilité (synthèse)

Trois mécanismes distincts croisés dans ce module, chacun protégeant
contre un scénario différent, pas redondants entre eux :

1. **Contre-pression** (Filebeat ↔ Logstash) — agit **en amont**,
   avant même que la donnée n'arrive : évite que la queue ne se
   remplisse en premier lieu, en ralentissant la source
2. **`queue.type: persisted`** (note 12) — protège contre un
   **crash soudain** de Logstash, en gardant les events déjà reçus
   sur disque. Ne protège **pas** contre un débordement progressif :
   si la queue grossit plus vite qu'elle ne se vide, le disque finit
   par se remplir — même "poof" que la queue mémoire, juste après un
   délai plus long
3. **Dead Letter Queue** (Palier 4, pas encore pratiquée) — récupère
   les events qui **échouent au traitement** une fois arrivés (ex :
   `_grokparsefailure`), un problème de contenu, pas de volume ou de
   crash

La contre-pression traite la cause (trop de volume, trop vite) ; la
persisted queue traite la conséquence d'un arrêt brutal ; la DLQ
traite un problème de qualité de la donnée elle-même — trois couches
complémentaires, pas une hiérarchie où l'une remplacerait les autres.

## Beats vs Elastic Agent (aperçu, détail prévu séparément)

**Elastic Agent** est l'évolution plus récente : un agent **unique**
capable de gérer plusieurs types de collecte à la fois (logs +
métriques + sécurité), géré centralement via **Fleet** (une
interface dans Kibana) plutôt que configuré fichier par fichier sur
chaque machine. Les Beats restent configurés individuellement en
YAML sur chaque hôte — plus simple pour un cas isolé, plus lourd à
gérer à grande échelle avec plusieurs machines.

Détail complet (où Logstash reste pertinent face à Agent) prévu
séparément — item déjà tracé au programme.

## Résumé

1. Tous les Beats partagent `libbeat`, chacun mono-tâche
2. Filebeat (logs) est le Beat pertinent pour notre futur TP RH8103
3. Un Beat peut envoyer direct à Elasticsearch ou via Logstash —
   Filebeat n'est jamais un remplaçant de Logstash
4. Mécanisme de contre-pression intégré (Filebeat ↔ Logstash) —
   protège contre la saturation, distinct de la protection contre la
   perte en cas de crash (`queue.type: persisted`, note 12)
5. Elastic Agent/Fleet est l'évolution centralisée, face aux Beats
   configurés individuellement — détail complet à venir séparément

## Lien avec les notes existantes

`01-panorama-alternatives-interfacage-securite.md` (panorama général
du Palier 0), `12-pipelines-config.md` (queue interne, sincedb —
mécanismes de fiabilité comparables), README Palier 3 (TP Filebeat
RH8103 prévu).

## Sources

- [Beats (Elastic Docs)](https://www.elastic.co/docs/reference/beats)
- [Beats — Data Shippers for Elasticsearch (Elastic)](https://www.elastic.co/beats)
- [Persistent Queues — section Backpressure (Elastic Docs)](https://www.elastic.co/guide/en/logstash/current/persistent-queues.html#backpressure-persistent-queue)
- [Winlogbeat (Elastic Docs)](https://www.elastic.co/docs/reference/beats/winlogbeat)
- [Let's Learn Elastic Stack — Filebeat Architecture](https://is-rajapaksha.medium.com/lets-learn-elastic-stack-part-5-filebeat-architecture-4578f4b20d24)
- [Difference Between Beats and Elastic Agent (DevOpsSchool)](https://www.devopsschool.com/blog/difference-between-beats-and-elastic-agent/)
