# Logstash — Suivi détaillé

Détail complet du module Logstash, extrait du README racine pour
rester lisible si le module grossit au-delà du prévu initial (comme
pour le module IA). Structure : `notes/` (numérotation indépendante,
repart à 1), `pipelines/` (fichiers `.conf` par palier/TP),
`ressources-externes.md`.

## Radar de couverture des paliers

![Radar covering](rsc/radar.png)


## Environnement

- Version ciblée : **Logstash 8.19.x** (LTS, support jusqu'au 15 juillet
  2027) — choisie plutôt que la 9.x pour rester sur la ligne la plus
  stable/documentée sans contrainte JDK 21
- Deux VM disponibles : RHEL8 existante (déjà utilisée pour
  Ansible/RHCSA), et Rocky/Alma 9 fraîche (équivalent binaire RHEL9)
- Dimensionnement lab : 2 vCPU / 4 Go RAM / 20 Go disque pour Logstash
  seul ; prévoir 16 Go RAM si Elasticsearch/Kibana s'ajoutent plus tard
  (Palier 5)

## Palier 0 — Panorama 

- [x] Comparatif Logstash vs rsyslog/syslog-ng, Fluentd/Fluent Bit,
      Vector — où Logstash se situe (JVM plus lourd, mais parsing Grok
      riche + intégration Elastic native)
- [x] Interfaçage au-delà d'Elasticsearch/Kibana — Kafka, JDBC, S3,
      SIEM tiers (Sentinel, Splunk), Grafana/Loki
- [x] Sécurité du produit — filtre `ruby` (exécution de code), CVE
      ESA-2026-29 (traversée de chemin), chaîne d'approvisionnement des
      plugins, port API 9600 non authentifié
- [x] Logstash au service de la sécurité — enrichissement threat intel
      (`translate`), plugin `threats_classifier` (MITRE ATT&CK),
      intégration SOAR
- [x] Options CLI de confort `notes/06-options-cli-confort.md`

## Palier 1 — Architecture (input/filter/output), premier pipeline, présentation configuration générale

- [x] Structure d'un fichier `.conf` de pipeline, notion d'event Logstash
- [x] Premier pipeline trivial (`stdin`/`stdout`), filtre `mutate`
- [x] Démarrage en ligne de commande (`-f`, `--path.data`,
      `--config.reload.automatic`, `-t`, `--config.debug`)
- [x] `logstash.yml` — config globale de l'instance (nom du nœud,
      taille des batchs, nombre de workers, type de queue)
- [ ] `pipelines.yml` — définition de plusieurs pipelines (aperçu
      accidentel lors du diagnostic de la boucle de crash du service,
      jamais expliqué en tant que mécanisme à part entière)
- [x] Type de queue interne (mémoire vs persistante sur disque) —
      impact sur la fiabilité en cas de crash en cours de traitement
- [x] `jvm.options` — d'où viennent les valeurs `-Xms1g -Xmx1g` vues
      au démarrage, comment les ajuster proprement
- [x] Codecs — brique distincte des filtres, à présenter avant de la
      croiser concrètement au Palier 3 (`codec json`)
- [ ] Patterns Grok personnalisés (`patterns_dir`) — notion théorique

**Pont prévu** : écho avec la notion de "log structuré dès l'entrée"
posée en note 46 (module IA).

**Pont Ansible** : écrire un rôle Ansible pour déployer Logstash
lui-même (install + template `logstash.yml`/premier `.conf`) sur les
deux VM plutôt qu'une install manuelle — réactive rôles/idempotence
sur un cas neuf.

## Palier 2 — Parsing Grok

- [x] Filtre `grok` (patterns prédéfinis), `mutate`
- [x] Filtres conditionnels basiques (`if [champ] == "valeur"`)
- [ ] Filtre `date` (remplacer `@timestamp` par le vrai timestamp du log)

**Pont prévu** : reparser le log d'incident `tp-ansible-agent`
(520 lignes, disque plein) avec un pattern grok sur mesure — remplacer
la lecture manuelle faite à l'œil ce soir-là par un vrai pipeline. 

**Pont Ansible (complémentaire)** : parser la sortie verbeuse d'un
`ansible-playbook -v` avec un pattern grok sur mesure.

## Palier 3 — Logs applicatifs/IA structurés (renforcement du Palier 2)

- [ ] Codec `json` en profondeur (amorcé en Palier 1, note 10)
- [ ] Filtres conditionnels avancés (`and`/`or`, `=~`, `in`, `!`)
- [ ] Liste de patterns dans un `match` + `break_on_match`, vs blocs `if`
- [ ] Patterns Grok personnalisés en pratique (`patterns_dir`)

**Pont prévu** : ingérer le schéma de logging LLM (note 46).

**Pont Ansible (officiel)** : callback plugin
`community.general.logstash` — playbook en direct vers Logstash.

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
