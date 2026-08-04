# Elasticsearch/Kibana : installation stock sur Rocky (infra habilitante)

Pas un TP à part entière — infra habilitante pour visualiser les
résultats des futurs TP (Palier 5, note théorique déjà posée dans le
README) plutôt que de rester en `stdout`/`journalctl`. Ajouté aux
rôles Ansible existants (`tp-filebeat-rh8103/ansible/`), nouveau
groupe d'inventaire `es_hosts` (Elasticsearch + Kibana, même host
Rocky que Logstash, groupe séparé pour rester flexible si ça bouge un
jour). Installation volontairement "stock" — sécurité par défaut
d'Elasticsearch 8.x **conservée**, pas désactivée pour simplifier.

## Décision d'architecture : pas de jeton d'enrôlement

Le flux "officiel" pour connecter Kibana à Elasticsearch en 8.x
passe par un jeton d'enrôlement éphémère (30 min de validité), pensé
pour un usage interactif — mal adapté à l'idempotence attendue d'un
rôle Ansible. Alternative retenue : `elasticsearch-reset-password`
pour fixer explicitement les mots de passe des users intégrés
(`elastic`, `kibana_system`), avec vérification préalable
(`uri` sur `/_security/_authenticate`) avant de les rejouer — même
principe d'idempotence que le Keystore Logstash (vérifier avant
d'agir).

## Bugs réels rencontrés et corrigés

**1. Liens symboliques `config`/`data`/`logs` absents après
installation du paquet RPM.** `/usr/share/elasticsearch/{config,data,logs}`
devraient être des liens vers `/etc/elasticsearch`,
`/var/lib/elasticsearch`, `/var/log/elasticsearch` respectivement —
absents après un `dnf install` frais, faisant échouer le premier
démarrage (`Unable to create logs dir`, exit code 78). Corrigé par
une task `file: state: link, force: true` en boucle sur les 3, ajoutée
à `install.yml` juste après le `dnf install` — pas un aléa isolé de
cette VM, reproductible sur toute installation fraîche.

**2. `elasticsearch.yml` écrasé par erreur — l'auto-configuration de
sécurité tourne dès l'installation du paquet, pas seulement au
premier démarrage.** Contrairement à l'hypothèse de départ, le
`%post` du RPM Elasticsearch peuple déjà le Keystore
(`xpack.security.*.ssl.*.secure_password`) et modifie
`elasticsearch.yml` **avant même** qu'Ansible n'exécute sa propre
task de configuration. Un premier `template` (qui remplace tout le
fichier) a écrasé ces réglages, laissant le Keystore avec des entrées
orphelines — erreur au démarrage
(`xpack.security.transport.ssl.enabled is not set, but ... secure_password`
configuré). Corrigé en remplaçant `template` par `blockinfile`
(ajoute/maintient un bloc marqué sans toucher au reste du fichier).
Contrairement à Elasticsearch, **Kibana n'a aucune auto-configuration
comparable** au moment de l'installation (vérifié : fichier par
défaut ne contient que 3 réglages de logging/pid) — `template` reste
donc sans risque pour `kibana.yml`.

**3. `cluster.initial_master_nodes` et `discovery.type: single-node`
sont mutuellement exclusifs, pas juste redondants.** L'auto-config
d'origine avait posé `cluster.initial_master_nodes: ["rocky.localdomain"]`
(nom **complet**), alors que notre `node.name` (via
`ansible_facts.hostname`) résout en nom **court** (`rocky`) — aucune
correspondance, donc le nœud ne pouvait jamais s'auto-bootstraper.
Symptôme trompeur : pas de crash, juste une boucle infinie de
`PeerFinder` qui cherche des pairs sur les ports 9300-9305 (jamais
trouvés sur un mono-nœud), visible uniquement dans les logs applicatifs
(`/var/log/elasticsearch/<cluster>.log`) — **pas** dans `journalctl`,
puisque contrairement à Logstash, Elasticsearch écrit ses logs dans
ses propres fichiers, pas vers `stdout`/systemd. Première tentative de
fix (ajouter `discovery.type: single-node` en plus) a fait planter le
démarrage explicitement
(`setting [cluster.initial_master_nodes] is not allowed when [discovery.type] is set to [single-node]`)
— il fallait **retirer** l'ancienne directive, pas cumuler les deux.

**4. `elasticsearch-reset-password -u <user> -i <valeur>` ne prend
pas la valeur en argument direct malgré la doc consultée — `-i` est
un flag qui bascule en mode interactif (prompt password + confirmation
via stdin).** Une valeur passée après `-i` sur la ligne de commande
est ignorée (traitée comme un argument superflu), laissant le process
bloqué en attente d'une saisie qui n'arrive jamais avec une task
`command` classique (pas de stdin fourni). Corrigé avec le module
`ansible.builtin.expect`, qui pilote les réponses aux prompts sans
jamais construire de ligne de commande shell contenant le secret —
contrairement à une première tentative via `printf ... | commande`,
qui faisait certes fonctionner l'authentification, mais laissait le
mot de passe visible en clair dans `ps aux` (le pipe/`printf` reste un
process avec ses arguments visibles, `no_log: true` ne protège que la
sortie Ansible, pas la ligne de commande réellement exécutée sur la
cible).

## Résultat final validé

- Cluster Elasticsearch mono-nœud `GREEN`, mots de passe `elastic`/
  `kibana_system` fixés explicitement et vérifiés (`_cluster/health`,
  `_authenticate`)
- Kibana accessible depuis l'host physique (`server.host: "0.0.0.0"`,
  port 5601 ouvert côté firewalld), connecté à Elasticsearch en HTTPS
  via le CA copié localement (`/etc/kibana/certs/ca.crt`, copie de
  `/etc/elasticsearch/certs/http_ca.crt`)
- Dimensionnement JVM fixé explicitement (`heap.options`, 2 Go) plutôt
  que laissé à l'auto-détection, VM passée à 8 Go de RAM pour ce test

## Reste à faire

- Brancher un `output elasticsearch` sur un pipeline Logstash existant
  pour voir de vraies données dans Discover
- Reprendre la phase 3 du TP `tp-filebeat-rh8103` (logrotate, cert
  expiré, permissions, retry/backoff) avec Kibana comme outil
  d'observation plutôt que `stdout`/`journalctl`

## Lien avec les notes existantes

`tp-filebeat-rh8103-resultat-phase1.md`/`-phase2.md` (mêmes familles
de bugs : ordre des tasks, chemins de fichiers non alignés, secrets
visibles en ligne de commande), `12-pipelines-config.md` (`sincedb`,
même vigilance sur ce qui persiste réellement au disque).
