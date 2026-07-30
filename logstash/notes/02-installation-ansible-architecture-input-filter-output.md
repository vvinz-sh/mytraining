# Logstash — Installation via Ansible et rappel architecture

Palier 1 du module Logstash — premier déploiement réel, et
consolidation du concept input/filter/output vu en théorie au
Palier 0.

## Architecture du pipeline : rappel

Un pipeline Logstash suit un schéma en trois blocs, à rapprocher
d'ETL : `input` (Extract), `filter` (Transform), `output` (Load).

- **`input`** — ingère la donnée brute (fichier, `stdin`, réseau,
  Kafka...). En sortie, un **event** Logstash existe déjà sous forme
  minimale : un champ `message` contenant le texte brut, plus quelques
  métadonnées automatiques (`@timestamp`, `host`).
- **`filter`** — enrichit/restructure cet event. Plusieurs blocs
  `filter {}` peuvent se succéder dans un même fichier `.conf` ; ils
  s'exécutent **séquentiellement**, chaque bloc voyant les champs déjà
  ajoutés par le précédent — pas des étapes indépendantes.
- **`output`** — écrit l'event enrichi vers une ou plusieurs
  destinations.

Les filtres peuvent être conditionnés (`if [champ] == "x" { ... }`),
ce qui permettra au Palier 3 d'appliquer des traitements différents
selon le type de log.

## Choix d'installation : dépôt YUM officiel, version épinglée

Dépôt Elastic officiel retenu plutôt qu'un RPM téléchargé
manuellement — facilite les mises à jour via `dnf update` plutôt que
de re-livrer un paquet à chaque patch. Version néanmoins **épinglée**
(`logstash-1:8.19.17-1`) plutôt que `state: latest` — en contexte
d'apprentissage, mieux vaut savoir exactement sur quelle version on
débogue plutôt que de laisser Ansible réinstaller silencieusement une
version différente à chaque exécution du playbook.

## Architecture de lab retenue : une seule VM pour l'instant

Deux VM disponibles (Rocky9, RHEL8.10), mais Logstash installé
**uniquement sur Rocky9** pour ce premier pipeline. Décision motivée
par la découverte de **Filebeat** (agent léger de la famille Beats,
pensé pour transporter des logs depuis une machine source vers
Logstash, sans faire le parsing lourd lui-même) — l'architecture
réaliste serait `Filebeat (client) → Logstash (parsing) →
Elasticsearch → Kibana`.

Plutôt que d'introduire trois inconnues à la fois (Filebeat, le
transport réseau entre deux machines, et Logstash lui-même), le choix
a été de garder RHEL8.10 (`rh8103`) au repos pour l'instant — elle
entrera en jeu comme client Filebeat une fois le concept
input/filter/output solidement ancré sur une seule machine.

## Rôle Ansible

Structure retenue : chaque palier regroupe, dans son propre dossier
sous `pipelines/`, à la fois le(s) fichier(s) `.conf` **et** le pont
Ansible correspondant (inventaire, playbook, rôle) — cohérent avec le
pattern déjà utilisé côté `ia-concepts/exercices/tp-xxx/`.

pipelines/palier1-architecture/
├── (pipeline .conf à venir)
└── ansible/
├── inventory.ini
├── deployer_logstash.yml
└── roles/logstash/
├── defaults/main.yml
└── tasks/main.yml


Tâches du rôle, dans l'ordre : import de la clé GPG Elastic
(`rpm_key`), déclaration du dépôt YUM 8.x (`yum_repository`),
installation du paquet épinglé (`dnf`), activation/démarrage du
service (`systemd`).

**Point d'attention rencontré** : les deux VM n'ont pas le même
interpréteur Python par défaut (3.9 sur Rocky9 « historique », 3.12
installé manuellement sur RHEL8.10) — nécessite
`ansible_python_interpreter` défini **par hôte** dans l'inventaire,
pas une valeur globale unique.

## Vérification post-déploiement

```bash
ansible logstash_hosts -i inventory.ini -m command -a "systemctl status logstash --no-pager"
```

Confirmé `active (running)`, JDK bundlé démarré (`Using bundled JDK`),
heap JVM par défaut à 1 Go (`-Xms1g -Xmx1g`) — cohérent avec le
dimensionnement de 4 Go de RAM recommandé pour cette VM au moment du
calibrage de l'environnement.

## Résumé

1. `input`/`filter`/`output` ≈ Extract/Transform/Load — plusieurs
   `filter` possibles, exécutés séquentiellement, pas indépendamment
2. Dépôt officiel + version épinglée = compromis maintenabilité (mises
   à jour faciles) / reproductibilité (savoir sur quoi on débogue)
3. Une seule VM pour ce premier pipeline — introduire une inconnue à
   la fois (Filebeat/réseau viendront après, une fois input/filter/
   output bien ancré)
4. Attention aux interpréteurs Python hétérogènes entre hôtes dans un
   inventaire Ansible réel

## Lien avec les notes existantes

`01-panorama-alternatives-interfacage-securite.md` (panorama théorique
précédent ce déploiement).
