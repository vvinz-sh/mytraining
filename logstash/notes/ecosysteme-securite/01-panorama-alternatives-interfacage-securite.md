# Logstash — Panorama : alternatives, interfaçage, sécurité

Palier 0 du module Logstash — vue d'ensemble avant toute pratique.
Objectif : savoir situer Logstash dans son écosystème plutôt que
d'apprendre l'outil en silence, sans savoir pourquoi lui plutôt qu'un
autre.

## Pourquoi ne pas se contenter d'un panorama de solutions ?

Sur la performance et la consommation mémoire pures, Logstash n'est
**pas** le champion de sa catégorie — il repose sur la JVM, ce qui
introduit un surcoût de ressources que les outils plus récents
évitent par construction. Comprendre où se situent ses vraies forces
(et ses vraies limites) évite d'apprendre un outil "par défaut" sans
recul critique.

## Les familles d'outils voisines

- **rsyslog / syslog-ng** — daemons syslog traditionnels, présents
  nativement sur quasi tout Linux. Rapides, peu gourmands, mais
  capacités de parsing/transformation plus limitées que Logstash —
  bons pour "collecter et router", moins pour "restructurer en
  profondeur".
- **Fluentd / Fluent Bit** — nés dans l'écosystème cloud-native,
  pensés JSON dès le départ. Fluent Bit (écrit en C) nettement plus
  léger, pensé edge/conteneurs. Fluentd plus polyvalent mais plus
  gourmand — d'où l'existence même de Fluent Bit comme version
  allégée.
- **Vector** — le plus récent, écrit en Rust, racheté par Datadog. Sur
  un benchmark du projet lui-même : 86 MiB/s contre 40.6 MiB/s pour
  Logstash — écart net, à relativiser (mesuré par l'éditeur
  concurrent, sur une version Logstash ancienne, ère 7.x).
- **NXLog** — collecteur de logs avec un point fort historique sur la
  collecte Windows Event Log (agent natif riche), tout en supportant
  Linux. Apparaît plus souvent dans les comparatifs orientés
  sécurité/SIEM (environnements mixtes Windows+Linux) que dans les
  comparatifs de performance pure entre outils Linux-first.

## Pourquoi Logstash malgré tout, dans ce contexte précis

1. **Grok reste une référence en richesse de parsing** — transformer
   un syslog hétérogène en champs structurés fins, avec des centaines
   de patterns prédéfinis, encore difficile à égaler en flexibilité
   pure aujourd'hui, même si les concurrents rattrapent leur retard.
2. **Intégration native avec Elasticsearch/Kibana** — écosystème fort,
   cohérent avec le Palier 5 déjà prévu (visualisation Kibana). Un
   autre outil impliquerait réapprendre une syntaxe différente le jour
   où Kibana entre en jeu.
3. **Techno historiquement associée au "ELK/Elastic Stack"** —
   largement documentée, cohérent avec l'objectif de stabilité/faible
   dette technique posé au démarrage du module.

**Nuance à garder** : apprendre Logstash aujourd'hui, c'est apprendre
des **concepts** (pipeline input/filter/output, parsing structuré) qui
se transposent bien à Vector/Fluent Bit — pas un choix d'outil
définitif et exclusif. Si un jour un vrai déploiement à fort débit ou
contraintes de ressources serrées se présente, reconsidérer ces
alternatives serait le bon réflexe.

## Vers quoi Logstash s'interface

Au-delà d'Elasticsearch/Kibana (déjà connu comme cible principale) :

- **Kafka** — découplage/mise en tampon avant traitement, utile pour
  absorber des pics de charge sans perdre d'events
- **Bases de données** via le plugin JDBC (lecture en entrée, écriture
  en sortie)
- **Stockage objet** (S3) — archivage long terme
- **SIEM tiers** — un plugin de sortie dédié existe pour **Microsoft
  Sentinel**, et Splunk via HEC (HTTP Event Collector)
- **Grafana/Loki** — alternative à Kibana pour la visualisation

## Sécurité du produit lui-même

- **Filtre `ruby`** : permet d'exécuter du code Ruby arbitraire à
  l'intérieur du pipeline — surface d'exécution de code à traiter avec
  la même prudence que n'importe quel input non fiable (même logique
  moindre privilège que sur `git-push-perso`)
- **ESA-2026-29** (avril 2026) : une traversée de chemin dans
  l'extraction d'archives peut mener à une écriture de fichier
  arbitraire, potentiellement à de l'exécution de code distant
- **Chaîne d'approvisionnement des plugins** : les plugins tiers
  viennent de RubyGems — à surveiller comme toute dépendance externe
- **Port d'API de monitoring (9600)** : exposé sans authentification
  par défaut si non explicitement protégé — classique à ne pas
  oublier de fermer/restreindre

## Logstash au service de la sécurité (usage SIEM)

- **Enrichissement threat intelligence à l'ingestion** — filtre
  `translate`, comparaison d'IP à des listes de menaces connues (ex :
  AlienVault OTX)
- **Plugin `threats_classifier`** — enrichit les logs selon le langage
  MITRE ATT&CK / cyber kill chain
- **Intégration SOAR** — Cortex XSOAR, Splunk SOAR, pour automatiser
  la réponse à incident une fois l'alerte détectée

## Résumé

1. Logstash n'est pas le plus performant/léger de sa catégorie — le
   choisir se justifie par la richesse Grok et l'intégration Elastic,
   pas par une supériorité brute
2. Les concepts appris (pipeline, parsing structuré) restent
   transposables à d'autres outils si le contexte change
3. Logstash s'interface bien au-delà d'Elasticsearch — Kafka, SIEM
   tiers, bases de données, stockage objet
4. Sa sécurité propre mérite la même vigilance que tout composant
   exécutant du code (filtre ruby) ou exposant une API (port 9600)
5. Logstash peut aussi être un outil de sécurité à part entière,
   côté détection/enrichissement plutôt que juste transport de logs

## Sources

- [Logstash Reference 8.19 (Elastic)](https://www.elastic.co/guide/en/logstash/8.19/index.html)
- [endoflife.date/logstash](https://endoflife.date/logstash)
- [ESA-2026-29 — avis de sécurité](https://discuss.elastic.co/t/logstash-8-19-14-9-2-8-9-3-3-security-update-esa-2026-29/385816)
- [NXLog — alternatives Logstash pour la sécurité (2026)](https://nxlog.co/news-and-blog/posts/logstash-alternatives-and-competitors)
- [Better Stack — Fluentd vs Logstash (2026)](https://betterstack.com/community/comparisons/fluentd-vs-logstash/)
