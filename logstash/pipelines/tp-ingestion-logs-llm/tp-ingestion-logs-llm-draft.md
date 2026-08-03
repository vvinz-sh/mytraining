# TP — Ingérer le schéma de logging LLM (note 46) et observer `/_node/stats/pipelines` (draft)

Statut : **design posé, pas encore exécuté**. Dernier des 3 TP
pratiques du Palier 3, le seul à croiser explicitement le module
IA/ML (note 46, `ia-concepts/notes/monitoring/`) avec Logstash.
Terrain d'application direct de la note 28 (codec/filtre `json` en
profondeur) et deuxième usage pratique de `/_node/stats/pipelines`
(premier usage : note 14, Palier 1).

## Contexte

Schéma cible (note 46) : champs plats stables
(`tokens_entree`, `tokens_sortie`, `temps_execution_s`,
`finish_reason`) + un sous-objet de détail (`params_generation`) —
choix de structure pensé précisément pour rester comparable dans le
temps même quand le détail interne change. Exemple du schéma :
```json
{
  "model": "qwen3-4b-logs-lora-final",
  "tokens_entree": 3267,
  "tokens_sortie": 187,
  "temps_execution_s": 4.2,
  "finish_reason": "stop",
  "params_generation": {
    "do_sample": false,
    "repetition_penalty": 1.3
  }
}
```

Ce schéma étant déjà pleinement structuré, l'objectif du TP n'est pas
d'écrire du grok — c'est d'ingérer proprement du JSON déjà propre et
d'observer le comportement du pipeline en conditions de suivi
(monitoring), pas de parsing.

## Étape 1 — Constituer un jeu de logs synthétiques suivant le schéma

Question ouverte : génération manuelle (quelques lignes JSON écrites
à la main, rapide mais peu volumineux) ou script rapide qui en génère
un volume plus réaliste (utile pour que les métriques de
`/_node/stats/pipelines` aient un peu de matière à montrer) ? Format
JSON Lines (un objet JSON par ligne), cohérent avec le `codec
json_lines` déjà repéré en note 10/28 mais jamais mis en pratique.

Point à trancher, absent du schéma actuel de la note 46 : y ajouter un
**timestamp explicite** de l'appel LLM lui-même, ou laisser Logstash
poser son propre `@timestamp` à l'ingestion ? Repense au pattern
`event.created`/`event.ingested` déjà posé au Palier 2 (note 15,
filtre `date`) — un appel LLM et son ingestion dans Logstash ne se
produisent pas forcément au même instant, notamment si les logs sont
rejoués après coup depuis un fichier plutôt qu'ingérés en direct.

## Étape 2 — Construire un pipeline nommé dédié

Cohérent avec la pratique multi-pipeline déjà posée au Palier 1
(`pipelines.yml`) : ce pipeline JSON/IA devrait avoir son **propre
nom** dans `pipelines.yml`, plutôt que de tourner sous `main` comme la
plupart des TP précédents — condition nécessaire pour pouvoir
l'identifier distinctement dans la sortie de
`/_node/stats/pipelines` une fois plusieurs pipelines actifs en
même temps sur la même instance.

```
input {
  file {
    path => "/chemin/vers/logs-llm.jsonl"
    start_position => "beginning"
    sincedb_path => "/dev/null"
    codec => json_lines
  }
}
```

Question directement héritée de la note 28 : `target` doit-il être
précisé ici ? Les champs du schéma (`tokens_entree`, `model`,
`finish_reason`...) n'entrent a priori pas en collision avec les
champs standards de Logstash (`@timestamp`, `host`, `tags`) — mais
vaut le coup de vérifier ce raisonnement plutôt que de le supposer
vrai par défaut, vu ce qu'on a appris sur les collisions silencieuses.

## Étape 3 — Vérifier la structure imbriquée obtenue

Sur un event reçu, `params_generation` doit ressortir comme un vrai
sous-objet (`params_generation.do_sample`,
`params_generation.repetition_penalty`), pas aplati ni sous forme de
texte — validation directe de ce qu'on a établi en note 28 sur la
préservation de la structure imbriquée par le codec `json`, cette
fois sur un vrai schéma applicatif plutôt qu'un exemple jouet.

## Étape 4 — Observer `/_node/stats/pipelines` sur ce pipeline précis

Deuxième usage pratique de cet endpoint (le premier, note 14, portait
sur `duration_in_millis` par plugin filter). Nouveauté cette fois :
plusieurs pipelines nommés coexistent probablement sur la même
instance Logstash du lab — à vérifier comment la réponse JSON de
l'endpoint distingue les pipelines entre eux (une clé par nom de
pipeline ?), pour être sûr de lire les métriques du bon pipeline et
pas d'un autre.

Métriques à observer, sans présumer lesquelles seront les plus
parlantes avant de les avoir vues : `events.in`/`events.out` (tout
event ingéré ressort-il bien, aucune perte silencieuse ?), et le détail
par plugin si un filtre a finalement été ajouté à l'étape 1/2.

## Ce qu'il faudra vérifier/clarifier en exécutant

- Volume de logs synthétiques suffisant pour que les métriques aient
  du sens (à calibrer, pas deviné à l'avance)
- Décision sur le timestamp explicite (event.created/ingested) —
  prise en observant un vrai décalage ou pas entre génération et
  ingestion, pas par principe
- `target` nécessaire ou pas pour ce schéma précis — à vérifier plutôt
  que présumer
- Format exact de la réponse `/_node/stats/pipelines` avec plusieurs
  pipelines nommés actifs — structure à observer, pas anticipée ici

## Compétences pratiquées

- Ingestion de JSON structuré applicatif réel (pas un exemple jouet),
  via `codec => json_lines`
- Vérification empirique de la préservation de structure imbriquée
  (note 28) sur un schéma métier concret
- Deuxième usage de `/_node/stats/pipelines`, cette fois avec
  plusieurs pipelines nommés à distinguer entre eux
- Pont explicite entre le module IA/ML (note 46, conception du
  schéma) et le module Logstash (ingestion + observation) — les deux
  volets d'un même problème (capturer puis exploiter la donnée)

## Lien avec les notes existantes

`46-logging-structure-llm.md` (ia-concepts — schéma cible complet,
raisonnement champs plats vs sous-objet), `28-codec-filtre-json-approfondi.md`
(codec `json`/`json_lines`, `target`, structure imbriquée),
`20-panorama-api-monitoring.md` et `14-test-dissect.md`
(`/_node/stats/pipelines`, premier usage), `15-filtre-date-timestamp.md`
(`event.created`/`event.ingested`, pertinent si timestamp explicite
retenu).
