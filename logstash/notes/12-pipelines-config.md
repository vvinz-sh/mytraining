# Logstash — pipelines.yml : plusieurs pipelines, isolation, pièges pratiques

## Pourquoi plusieurs pipelines, pas juste des blocs conditionnels

Nos filtres conditionnels (`if [processus] == "..."`, notes 05/07/08)
évitent déjà le traitement inutile **au sein d'un même pipeline** — un
event `systemd` n'entre jamais dans le bloc `kernel`. La vraie
justification de pipelines **séparés** est ailleurs : deux flux avec
des besoins de performance/durabilité différents (ex : `queue.type`
propre à chacun, isolé — confirmé dans la doc officielle : *"Persistent
queues and dead letter queues are isolated per pipeline"*), et une
meilleure maintenabilité qu'un unique `.conf` qui grossit
indéfiniment.

## Correction d'une fausse piste : `pipeline.workers` n'est pas global

Hypothèse initiale erronée : `pipeline.workers` serait partagé entre
tous les pipelines de l'instance. Vérifié faux — chaque pipeline peut
avoir son **propre** `pipeline.workers` dans `pipelines.yml`, isolé des
autres (retombe sur la valeur de `logstash.yml` seulement si non
précisé).

**Ce qui est réellement partagé** : les ressources physiques sous-jacentes
(cœurs CPU réels de la VM). Si deux pipelines n'ont chacun aucun
`pipeline.workers` explicite, ils prennent chacun "le nombre de cœurs"
par défaut — sur une VM à 4 cœurs, ça donne 8 workers en concurrence
pour seulement 4 cœurs physiques. La doc officielle avertit
explicitement : *"it's important to take into account resource
competition between the pipelines, given that the default values are
tuned for a single pipeline."*

## Bug 1 : le pipeline `generator` s'épuise tout seul

Premier test avec `generator { count => 3 }` : génère exactement 3
events ("Hello world!") puis **termine naturellement** — contrairement
à `stdin`, qui reste ouvert indéfiniment en usage interactif normal.

**Conséquence en cascade découverte** : avec `main` vide (conf.d
toujours sans fichier), `syslog` en échec de chemin (bug 3), et
`test-generator` épuisé après ses 3 events — **tous** les pipelines de
l'instance finissent par s'arrêter, donc le **process Logstash entier**
se termine. C'est **systemd** (`Restart=always`, déjà rencontré en
note 03) qui relance alors toute l'instance depuis zéro, redéclenchant
la même cascade d'échecs — le "restart counter" qui grimpe n'est donc
pas un mécanisme interne à `pipelines.yml`, c'est le même piège
systemd vu au Palier 1, juste déclenché différemment (épuisement
naturel plutôt qu'échec de démarrage immédiat).

**Correction** : `count => 0` fait tourner `generator` indéfiniment.

## Bug 2 : permission refusée sur le fichier de config personnel

`path.config: "/home/vinz/test-grok-kernel.conf"` — fichier bien
présent, contenu correct, mais `"No config files found in path"`.

**Diagnostic** : le service systemd tourne sous l'utilisateur système
`logstash`, pas `vinz`. `$HOME` de `vinz` était en `0700` — seul
`vinz` peut même **entrer** dans ce répertoire (le bit d'exécution sur
un dossier contrôle l'accès, pas seulement le listage). `logstash`
n'avait donc littéralement aucun moyen d'atteindre le fichier,
indépendamment de ses propres permissions.

**Correction retenue (choix pragmatique pour un lab)** : copie du
fichier vers un dossier dédié, `chown` complet à `logstash` :
```bash
sudo mkdir -p /etc/logstash/conf.d.perso
sudo cp /home/vinz/test-grok-kernel.conf /etc/logstash/conf.d.perso/
sudo chown -R logstash:logstash /etc/logstash/conf.d.perso
```
En vraie production, un `chgrp` + permissions de groupe serait
préférable (cohérent avec le principe déjà appliqué au TP git-push,
`vinz:code`) — jugé disproportionné pour ce lab précis.

## Bug 3 (conceptuel, découvert sans plantage) : `stdin` incompatible avec un service

Une fois les bugs 1-2 corrigés, `syslog` (avec `input { stdin {} }`)
démarre bien mais **se termine immédiatement** — `Pipeline terminated`
quelques millisecondes après `Pipeline started`.

**Diagnostic** : un service lancé par systemd n'a **aucun terminal**
attaché. Son `stdin` pointe vers `/dev/null` plutôt que vers un
clavier réel. Le plugin `stdin` lit ce flux, atteint immédiatement
l'EOF (`/dev/null` ne produit jamais de données), et considère
légitimement qu'il n'y a plus rien à lire — il se termine
proprement, comme un fichier entièrement lu.

**Portée générale** : `stdin` n'a de sens que pour un usage interactif
manuel — jamais pour un service tournant en arrière-plan sans
supervision humaine. Un vrai déploiement nécessiterait un input conçu
pour ça (`file`, port réseau, Kafka).

## Configuration finale fonctionnelle

```yaml
- pipeline.id: main
  path.config: "/etc/logstash/conf.d/*.conf"

- pipeline.id: syslog
  path.config: "/etc/logstash/conf.d.perso/test-grok-kernel.conf"

- pipeline.id: test-generator
  config.string: "input { generator { count => 0 } } output { stdout {} }"
```

Résultat : `test-generator` tourne en continu (`sequence` grimpant
sans fin), `main` et `syslog` restent des cas particuliers instructifs
plutôt que des pipelines réellement utiles en l'état (vide pour
`main`, incompatible avec un service pour `syslog` tant qu'il utilise
`stdin`).

## Résumé

1. Chaque pipeline dans `pipelines.yml` a ses propres réglages
   (workers, queue) isolés des autres — mais tous se partagent les
   mêmes ressources physiques (CPU, RAM) de la machine
2. Un pipeline dont **tous** les inputs s'épuisent (naturellement ou
   par erreur) entraîne l'arrêt du process entier — et c'est systemd,
   pas Logstash, qui relance alors toute l'instance en boucle
3. Les permissions d'un service tournant sous un utilisateur système
   dédié (`logstash`) s'appliquent aussi aux répertoires parents, pas
   seulement au fichier final — un `$HOME` personnel en `0700` bloque
   l'accès même à un fichier par ailleurs correctement configuré
4. `stdin` n'est utilisable qu'en contexte interactif — incompatible
   par nature avec un service systemd sans terminal attaché (`/dev/null`
   → EOF immédiat)

## Lien avec les notes existantes

`03-premier-pipeline-stdin-stdout-filter-mutate.md` (`path.data` perso,
même logique de permissions rencontrée dès le Palier 1),
`08-grok-conditionnel-kernel-gestionechec.md` (fichier `.conf` réutilisé
ici), `01-panorama-alternatives-interfacage-securite.md` (boucle de
crash systemd déjà diagnostiquée une première fois).

## Sources

- [Multiple Pipelines (Elastic, docs)](https://www.elastic.co/docs/reference/logstash/multiple-pipelines)
- [Introducing Multiple Pipelines in Logstash (Elastic Blog)](https://www.elastic.co/blog/logstash-multiple-pipelines)
- [Question about pipeline.workers (Elastic Discuss)](https://discuss.elastic.co/t/question-about-pipelines-workers/297759/2)
