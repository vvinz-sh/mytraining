# TP — Dupliquer les erreurs Ansible vers un fichier lisible : résultat

Complète `tp-routage-echecs-ansible-draft.md`. Pipeline `ansible`
(Rocky) étendu : Elasticsearch inchangé + duplication des erreurs
(`FAILED`/`UNREACHABLE`) vers un fichier reconstruit lisible par un
humain, via le filtre `json` et le filtre `clone`.

## Résultat final validé

```
[vinz@rocky ~]$ cat /tmp/erreurs_ansible.log
rh8102.localdomain - filebeat : Autoriser filebeat en lecture sur /var/log/messages-tproutage-ko (fichier déjà existant) - Path not found or not accessible.
rh8109.localdomain - Gathering Facts - Task failed: Failed to connect to the host via ssh: ssh: Could not resolve hostname rh8109.localdomain: Name or service not known
```
Les deux cas testés (`FAILED` sur une task réelle, `UNREACHABLE` sur
un host injoignable dès `Gathering Facts`) produisent un message
lisible en une ligne, sans avoir eu besoin de deux constructions
différentes — même clé `.msg` dans `ansible_result_parsed` pour les
deux cas, confirmé par observation directe plutôt que supposé.
Documents Elasticsearch restés identiques à l'état d'avant ce TP
(aucun champ `mutate` ajouté dessus, seule la copie clonée en
bénéficie).

## Structure de `ansible_result` confirmée sur les deux cas

- **`FAILED`** : `{"changed": false, "msg": "Path not found or not accessible."}`
- **`UNREACHABLE`** : `{"changed": false, "msg": "Task failed: Failed to connect to the host via ssh: ...", "unreachable": true}`

Même clé `.msg` dans les deux cas — un seul `mutate` a suffi,
contrairement à ce que le draft envisageait par prudence (deux
constructions distinctes selon le cas).

## Piège découvert : le récap `finish` hérite du statut `FAILED`

Constat non anticipé : l'event `ansible_type: "finish"` (récap global
de fin de playbook) porte lui aussi `status: "FAILED"` dès qu'au moins
une task a échoué — pas seulement les events de task individuels.
Conséquence en cascade avant correction : le filtre `json` tournait
aussi sur cet event, dont `ansible_result` est le récap par host
(`{"rh8102.localdomain": {"ok": 11, ...}}`), sans clé `.msg` — le
`mutate` suivant, référençant des champs absents sur un `finish`
(`ansible_host`, `ansible_task`), produisait le **template littéral
non résolu** en sortie (`"%{[ansible_host]} - %{[ansible_task]} - ..."`),
plutôt qu'une erreur silencieuse. Corrigé en resserrant la condition
sur les deux blocs concernés :
```
([status] == "FAILED" or [status] == "UNREACHABLE") and [ansible_type] == "task"
```

## Piège découvert : collision de champ avec le filtre `clone`

Besoin identifié en cours de route : le filtre `json`/`mutate` doit
enrichir la copie destinée au fichier, **sans** que ces champs
n'atteignent Elasticsearch — impossible à faire avec un simple
`mutate { remove_field }` dans le `filter` (un seul état d'event,
partagé par les deux `output`, retirer un champ le retire pour les
deux sorties à la fois). Résolu avec le filtre `clone`, qui duplique
l'event **avant** les deux destins.

**Collision réelle rencontrée** : par défaut (mode ECS désactivé),
`clone` marque ses copies via un champ nommé... `type` — exactement
le même nom que celui posé par le callback lui-même
(`type = "ansible"`, configuré dans `ansible.cfg`). Confirmé par la
doc officielle : *"The original event is left unchanged and a `type`
field is added to the clone."* Corrigé en activant le mode ECS sur
`clone` (`ecs_compatibility => "v1"`), qui bascule le marquage vers le
champ `tags` (tableau) plutôt que `type` — plus de collision.

**Deuxième piège en cascade, après le premier fix** : la bascule vers
`tags` faite côté `clone` et côté condition d'`output`
(`if "copie_erreur" in [tags]`), mais **oubliée** dans la condition du
`filter` qui applique `json`/`mutate` (restée sur
`if [type] == "copie_erreur"`, jamais vraie après le changement).
Résultat : le fichier se créait bien, mais avec le template littéral
non résolu (`%{message_erreur}`) — même symptôme que le piège du
`finish`, cause différente. Corrigé en alignant les deux conditions
sur `tags`.

## Pipeline final

```
filter {
  if ([status] == "FAILED" or [status] == "UNREACHABLE") and [ansible_type] == "task" {
    clone {
      clones => ["copie_erreur"]
      ecs_compatibility => "v1"
    }
    if "copie_erreur" in [tags] {
      json {
        source => "ansible_result"
        target => "[ansible_result_parsed]"
      }
      mutate {
        add_field => {
          "message_erreur" => "%{[ansible_host]} - %{[ansible_task]} - %{[ansible_result_parsed][msg]}"
        }
      }
    }
  }
}

output {
  elasticsearch { ... }  # inchangé

  if "copie_erreur" in [tags] {
    file {
      path => "/tmp/erreurs_ansible.log"
      codec => line { format => "%{message_erreur}" }
    }
  }
}
```

On a bien un fichier en sortie qui indique les tâches en erreur/unreachable selon le format défini:
```
cat /tmp/erreurs_ansible.log

rh8102.localdomain - filebeat : Autoriser filebeat en lecture sur /var/log/messages-tproutage-ko (fichier déjà existant) - Path not found or not accessible.
rh8109.localdomain - Gathering Facts - Task failed: Failed to connect to the host via ssh: ssh: Could not resolve hostname rh8109.localdomain: Name or service not known
```

## Décision explicite : pipeline-to-pipeline écarté au profit de `clone`

Envisagé au moment de constater le besoin de deux traitements
différents sur le même event (motif jugé valable, contrairement au
premier réflexe écarté plus tôt dans le draft comme prématuré) — mais
`clone`, qui reste dans le **même** pipeline, s'est avéré suffisant
pour ce besoin précis (dupliquer puis traiter différemment, pas
distribuer vers des pipelines aux cycles de vie séparés). Le vrai
pipeline-to-pipeline resterait pertinent si les deux traitements
devenaient plus lourds ou nécessitaient un rechargement indépendant —
pas le cas ici.

## Compétences pratiquées

- Duplication en sortie (note 29) avec deux traitements distincts sur
  chaque copie, pas juste une même donnée envoyée deux fois telle quelle
- Filtre `json` avec un vrai objectif de lisibilité humaine en sortie
- Filtre `clone`, découverte de sa collision par défaut avec un champ
  `type` déjà posé par une source externe (le callback), corrigée via
  `ecs_compatibility`
- Diagnostic d'un template Logstash non résolu (`%{champ}` littéral en
  sortie) comme signal fiable d'un champ absent au moment du rendu,
  rencontré deux fois pour deux causes différentes

## Lien avec les notes existantes

`tp-callback-ansible-resultat.md` (pipeline d'entrée, `ansible_result`
identifié comme JSON encodé), `28-codec-filtre-json-approfondi.md`
(filtre `json`, `target`), `29-sorties-multiples.md` (duplication vs
routage — ce TP en est le premier vrai cas d'usage avec deux
traitements distincts par copie).
