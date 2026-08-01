# Logstash — Panorama Elastic Agent & Fleet

Complète les notes 01 (Palier 0) et 16 (Beats) — l'évolution plus
récente de l'écosystème de collecte Elastic, et la vraie question qui
nous intéresse : où Logstash reste-t-il nécessaire face à ça ?

## Elastic Agent : un agent unique plutôt que plusieurs Beats

Là où collecter logs + métriques + sécurité avec des Beats classiques
demande d'installer et maintenir **plusieurs process séparés**
(Filebeat + Metricbeat + Auditbeat...), Elastic Agent unifie tout ça
en **un seul agent**, avec une seule **policy** de configuration. Une
seule installation, une seule configuration à jour par machine.

## Fleet : gestion centralisée

**Fleet** (une interface dans Kibana) permet de gérer toutes les
policies d'agents depuis un seul endroit — appliquer une policy à des
centaines d'hôtes d'un coup, plutôt que d'éditer un fichier YAML par
machine comme avec les Beats classiques. Deux modes existent : géré
par Fleet (centralisé) ou **standalone** (policy déployée
manuellement, pas de mise à jour automatique des intégrations).

## Où Logstash reste-t-il nécessaire ? La vraie limite : les ingest pipelines

De nombreuses "intégrations" Agent embarquent leur propre **ingest
pipeline** — un pipeline de transformation qui tourne **à
l'intérieur d'Elasticsearch** (pas dans un process séparé), capable de
remplacer Logstash pour des cas standards (Nginx, Apache, MySQL...).

Question posée : est-ce que ça remplace Logstash pour **notre propre
cas** (log syslog custom, filtres conditionnels sur mesure) ? Réponse
construite en creusant les vraies limites d'un ingest pipeline,
confirmées par plusieurs sources concordantes :

- **Destination unique** — un ingest pipeline écrit **uniquement**
  vers Elasticsearch. Notre propre routage `_grokparsefailure` vers un
  fichier séparé (note 08) serait **impossible** avec un ingest
  pipeline seul.
- **Gestion d'erreur limitée** — pas de queue persistante ni de
  mécanisme de retry pour les échecs transitoires, contrairement à
  `queue.type: persisted` (note 12) ou une vraie DLQ.
- **Aucune logique inter-documents** — chaque document est traité
  **indépendamment**, pas de fenêtre glissante, agrégation ou
  corrélation entre plusieurs events.
- **Pas d'appel externe** — confirmé par le blog officiel Elastic :
  *"processors are generally not able to call out to other systems or
  read data from disk"* — pas d'équivalent au filtre `translate`
  (enrichissement par lookup externe, notes 44/45 sécurité).

**Conclusion** : un ingest pipeline convient à de la transformation
**simple, isolée, à destination unique**. Logstash reste nécessaire
dès qu'il faut du routage multi-destination, une vraie gestion
d'erreur robuste, ou de l'enrichissement par appel externe —
exactement ce que notre propre pipeline (routage d'échec, filtres
conditionnels multiples) illustre concrètement.

## Détour concret : Agent peut-il faire un audit RPM ?

Question posée en lien avec un outil d'audit RPM développé
séparément (autre conversation) : Agent peut-il remonter ce genre
d'inventaire ?

**Réponse** : oui, via l'intégration **Osquery Manager** — Osquery
déployé sur les agents via Fleet, interrogeable en SQL, avec des
tables dédiées `rpm_packages`/`rpm_package_files`, résultats stockés
dans Elasticsearch. Centralisable à l'échelle de nombreuses machines.

**Limite trouvée** (feature request encore ouverte sur le dépôt
Kibana) : Agent/Osquery liste les paquets installés mais **ne
corrèle pas nativement** avec des bases de vulnérabilités CVE —
demande encore un enrichissement manuel ou un outil externe.

**Conclusion** : les deux outils (Agent/Osquery et un outil d'audit
RPM personnalisé) ne se marchent pas dessus — la vraie valeur ajoutée
d'un outil sur mesure se situe sur l'**intégration** (format de
sortie, système cible) plutôt que sur la collecte brute elle-même,
qu'Agent/Osquery couvre déjà à grande échelle.

## Résumé

1. Elastic Agent unifie plusieurs Beats en un seul agent, une seule
   policy — gain de gestion, pas de fonctionnalité radicalement
   nouvelle en soi
2. Fleet centralise la gestion à l'échelle de nombreuses machines,
   remplaçant la config YAML éparpillée des Beats classiques
3. Les ingest pipelines (intégrations Agent) peuvent remplacer
   Logstash pour des cas **simples et standards**, mais butent sur
   destination unique, gestion d'erreur limitée, absence de logique
   inter-documents, pas d'appel externe
4. Deux outils répondant à des besoins différents peuvent coexister
   sans se substituer l'un à l'autre — confirmé concrètement avec le
   cas Agent/Osquery vs outil d'audit RPM personnalisé

## Lien avec les notes existantes

`01-panorama-alternatives-interfacage-securite.md` (panorama général
Palier 0), `16-panorama-beats.md` (Beats classiques, prédécesseurs
d'Agent), `08-grok-conditionnel-kernel-gestionechec.md` (routage
`_grokparsefailure`, exemple concret de ce qu'un ingest pipeline ne
peut pas faire), `12-pipelines-config.md` (queue persistée, comparée
à l'absence d'équivalent côté ingest pipeline).

## Sources

- [Fleet and Elastic Agent overview (Elastic, 8.19)](https://www.elastic.co/guide/en/fleet/8.19/fleet-overview.html)
- [Elastic Agent policies (Elastic Docs)](https://www.elastic.co/docs/reference/fleet/agent-policy)
- [Should I use Logstash or Elasticsearch ingest nodes? (Elastic Blog)](https://www.elastic.co/blog/should-i-use-logstash-or-elasticsearch-ingest-nodes)
- [Ingest Pipelines vs Logstash vs Beats Processors (NosqlRevolution)](https://www.nosqlrevolution.com/blog/posts/ingest-pipelines-logstash-beats.html)
- [Osquery Manager integration (Elastic Docs)](https://www.elastic.co/docs/reference/integrations/osquery_manager)
- [Enhance Elastic XDR with Vulnerability Discovery (GitHub Issue, feature request)](https://github.com/elastic/kibana/issues/237747)
