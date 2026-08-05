 # TP — Visualiser des logs LLM structurés dans Kibana (note 46) (draft, refondu)

Statut : **design refondu, pas encore exécuté**. Version précédente
abandonnée en l'état — objectif initial ("ingestion + observation
`/_node/stats/pipelines`") jugé trop mince côté Logstash après
discussion (le schéma est déjà du JSON propre, pas de grok à écrire,
`/_node/stats/pipelines` déjà pratiqué en note 14). Recentré sur ce
qui manquait vraiment : **vérifier concrètement, dans Kibana**,
l'affirmation de la note 46 elle-même — qu'un signal comme la montée
de `finish_reason: "length"` "aurait été immédiatement visible sur un
graphique". Jamais montré jusqu'ici, seulement affirmé.

## Contexte

Schéma cible (note 46, module `ia-concepts`) : champs plats stables
(`tokens_entree`, `tokens_sortie`, `temps_execution_s`,
`finish_reason`) + sous-objet `params_generation`. Origine du schéma :
reconstruit après coup à partir de frictions réelles du TP LLM local
(troncature silencieuse, confusion de config de génération) — un
exercice de préparation à un usage futur (modèle servi en continu),
pas une réparation rétroactive de ce TP passé (clarifié en session :
un run d'entraînement séquentiel unique se débogue très bien avec
TensorBoard/un simple graphique, sans avoir besoin d'un pipeline
d'ingestion centralisé).

## Étape 1 — Générer deux scénarios distincts, pas juste des logs au hasard

Reprendre l'exemple de diagnostic croisé exact de la note 46 : un
lot où `finish_reason: "length"` grimpe **et** `tokens_entree` grimpe
en même temps (cohérent, pas un problème) et un lot où
`finish_reason: "length"` grimpe **alors que** `tokens_entree` reste
stable (suspect — signal de dérive du modèle). Générer un jeu
synthétique en JSON Lines qui simule ces deux situations
distinctement dans le temps (par exemple : une première fenêtre
temporelle "normale", puis une fenêtre "dérive suspecte"), pour que
la distinction soit visuellement testable a posteriori — pas juste
des valeurs aléatoires sans scénario.

Question à trancher : génération manuelle (quelques dizaines de
lignes soigneusement construites) ou script qui génère les deux
scénarios avec un peu de bruit aléatoire réaliste par-dessus ? Le
script est probablement préférable ici — le scénario est précis, mais
un peu de variance rend le résultat moins "trop parfait pour être
vrai".

Point resté ouvert du draft d'origine, toujours à trancher : ajouter
un **timestamp explicite** de l'appel LLM (distinct de `@timestamp`
d'ingestion), important cette fois puisque le scénario dépend d'un
vrai découpage temporel entre les deux fenêtres (normal vs suspect).

## Étape 2 — Ingérer via `codec => json_lines`

Premier vrai usage pratique de ce codec (jusqu'ici seulement
mentionné en théorie, notes 10/28) :
```
input {
  file {
    path => "/chemin/vers/logs-llm.jsonl"
    start_position => "beginning"
    sincedb_path => "/dev/null"
    codec => json_lines
  }
}
output {
  elasticsearch {
    hosts => ["https://localhost:9200"]
    ...
  }
}
```
Question héritée de la note 28, toujours pertinente : `target`
nécessaire ou pas pour ce schéma (les champs `tokens_entree`,
`finish_reason`... n'entrent a priori pas en collision avec les
champs standards, à vérifier plutôt que supposer).

## Étape 3 — Data view + visualisations Kibana

1. Créer un data view sur l'index cible
2. **Visualisation 1** — répartition de `finish_reason` (camembert ou
   barres) sur l'ensemble de la période — confirme visuellement les
   valeurs possibles (`stop`, `length`, `content_filter`,
   `tool_calls`) et leur proportion globale
3. **Visualisation 2** — `tokens_entree` et proportion de
   `finish_reason: "length"` dans le temps, **côte à côte** (deux
   séries sur le même axe temporel, ou deux graphiques synchronisés)
   — le test réel de l'exercice : est-ce que la fenêtre "suspecte"
   (length qui grimpe, tokens_entree stable) ressort clairement à
   l'œil, sans calcul, comme l'affirmait la note 46 ?

## Ce qu'il faudra vérifier/clarifier en exécutant

- Le scénario "suspect" est-il réellement identifiable **à l'œil**
  sur le graphique, sans avoir besoin de connaître à l'avance lequel
  des deux lots est lequel — sinon, l'affirmation de la note 46
  mérite d'être nuancée plutôt que confirmée telle quelle
- `target` nécessaire ou pas pour ce schéma précis (note 28)
- Format exact du timestamp explicite si retenu, et comment Kibana
  s'en sert (champ de temps du data view : `@timestamp` d'ingestion,
  ou le timestamp applicatif de l'appel LLM ?)

## Compétences pratiquées

- `codec => json_lines` en pratique, première fois
- Construction de deux visualisations Kibana simples à partir de
  champs structurés, avec un objectif de démonstration précis
  (confirmer/infirmer une affirmation de la note 46) plutôt qu'un
  exercice Kibana abstrait
- Distinction entre un TP de préparation (schéma pensé pour un futur
  déploiement) et une réparation rétroactive d'un TP déjà terminé

## Lien avec les notes existantes

`46-logging-structure-llm.md` (ia-concepts — schéma cible, exemple de
diagnostic croisé repris ici concrètement), `28-codec-filtre-json-approfondi.md`
(codec `json`/`json_lines`, `target`), `33-kibana-decouverte-interface.md`
(navigation Discover/Data Views), point théorique Palier 5 (Discover
vs Dashboard — ce TP en est le premier cas pratique).
