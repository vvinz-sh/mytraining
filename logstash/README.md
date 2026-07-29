# Logstash — Suivi détaillé

Détail complet du module Logstash, extrait du README racine pour
rester lisible si le module grossit au-delà du prévu initial (comme
pour le module IA). Structure : `notes/` (numérotation indépendante,
repart à 1), `pipelines/` (fichiers `.conf` par palier/TP),
`ressources-externes.md`.

## Radar de couverture des paliers

![Radar covering](rsc/radar.png)

Tous les paliers à 0/10 au démarrage — normal, le module vient d'être
structuré, aucun contenu (note/pipeline) n'a encore été écrit.

## Environnement

- Version ciblée : **Logstash 8.19.x** (LTS, support jusqu'au 15 juillet
  2027) — choisie plutôt que la 9.x pour rester sur la ligne la plus
  stable/documentée sans contrainte JDK 21
- Deux VM disponibles : RHEL8 existante (déjà utilisée pour
  Ansible/RHCSA), et Rocky/Alma 9 fraîche (équivalent binaire RHEL9)
- Dimensionnement lab : 2 vCPU / 4 Go RAM / 20 Go disque pour Logstash
  seul ; prévoir 16 Go RAM si Elasticsearch/Kibana s'ajoutent plus tard
  (Palier 5)

## Palier 0 — Panorama (théorique, pas encore rédigé en note)

- [ ] Comparatif Logstash vs rsyslog/syslog-ng, Fluentd/Fluent Bit,
      Vector — où Logstash se situe (JVM plus lourd, mais parsing Grok
      riche + intégration Elastic native)
- [ ] Interfaçage au-delà d'Elasticsearch/Kibana — Kafka, JDBC, S3,
      SIEM tiers (Sentinel, Splunk), Grafana/Loki
- [ ] Sécurité du produit — filtre `ruby` (exécution de code), CVE
      ESA-2026-29 (traversée de chemin), chaîne d'approvisionnement des
      plugins, port API 9600 non authentifié
- [ ] Logstash au service de la sécurité — enrichissement threat intel
      (`translate`), plugin `threats_classifier` (MITRE ATT&CK),
      intégration SOAR

## Palier 1 — Architecture (input/filter/output), premier pipeline

- [ ] Structure d'un fichier `.conf`, notion d'event Logstash
- [ ] Premier pipeline trivial (`stdin`/`stdout`)

**Pont prévu** : écho avec la notion de "log structuré dès l'entrée"
posée en note 46 (module IA).

**Pont Ansible** : écrire un rôle Ansible pour déployer Logstash
lui-même (install + template `logstash.yml`/premier `.conf`) sur les
deux VM plutôt qu'une install manuelle — réactive rôles/idempotence
sur un cas neuf.

## Palier 2 — Parsing Grok

- [ ] Filtre `grok` (patterns prédéfinis), `mutate`, `date`

**Pont prévu** : reparser le log d'incident `tp-ansible-agent`
(520 lignes, disque plein) avec un pattern grok sur mesure — remplacer
la lecture manuelle faite à l'œil ce soir-là par un vrai pipeline.

**Pont Ansible (complémentaire)** : parser la sortie verbeuse d'un
`ansible-playbook -v` avec un pattern grok sur mesure.

## Palier 3 — Logs applicatifs/IA structurés

- [ ] Codec `json`, filtres conditionnels

**Pont prévu** : ingérer le schéma de logging LLM conçu en note 46
(`tokens_entree`, `finish_reason`, `params_generation`...) — valider
concrètement un schéma resté jusque-là théorique.

**Pont Ansible (officiel)** : le callback plugin
`community.general.logstash` envoie directement les événements
d'exécution d'un playbook (tâche par tâche, succès/échec, hôte) vers
Logstash en JSON structuré — brancher un vrai playbook existant en
direct plutôt qu'ingérer un fichier statique.

## Palier 4 — Multi-pipelines, gestion d'erreurs

- [ ] `pipelines.yml`, sorties multiples, dead letter queue
**Pont Ansible (piste)** : router les échecs de tâches (via le

callback ci-dessus) vers une sortie séparée — écho à la gestion
d'erreurs/handlers déjà vue côté Ansible.

## Palier 5 — Sortie Elasticsearch/Kibana

- [ ] Sortie vers Elasticsearch, visualisation Kibana

**Pont prévu** : débloquerait potentiellement le TP Monitoring IA
(golden dataset/recall@k, resté en draft) — visualiser les résultats
d'évaluation dans un vrai dashboard plutôt qu'en `print()` console,
ce qui à son tour débloquerait le TP CI/CD qui en dépend.

## Niveau visé en sortie

"Junior solide / confirmé débutant" — voir discussion complète dans
la session ayant initialisé ce module. Suffisant pour construire,
déboguer et faire évoluer des pipelines non triviaux ; pas encore le
niveau tuning de performance à grande échelle, cluster/HA, ou
développement de plugin custom.
