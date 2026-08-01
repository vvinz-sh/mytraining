# Logstash — Codecs : structuration à l'entrée et à la sortie

Complète le Palier 1 — dernière brique d'architecture manquante avant
de passer au Palier 3 (`codec json` sur des logs applicatifs/IA).

## Codec ≠ filtre : où et comment il intervient

Un `filter` est un **bloc indépendant** du pipeline, au même niveau que
`input`/`output` (`filter { grok {...} }`). Un codec, lui, est un
**paramètre attaché directement** à un plugin `input` ou `output` —
jamais un bloc séparé :
```
input {
  stdin {
    codec => json
  }
}
```

Il agit **au moment où la donnée brute arrive**, avant même que
l'event ne soit pleinement formé — contrairement à un filtre qui
opère sur un event déjà construit.

## Test réalisé — codec en entrée

```
input {
  stdin {
    codec => json
  }
}

output {
  stdout {}
}
```

Entrée :
```
{"service": "app", "log_line": "user login failed for admin from 10.0.0.5"}
```

Sortie :
```
{
      "log_line" => "user login failed for admin from 10.0.0.5",
       "service" => "app",
         "event" => { "original" => "{\"service\": \"app\", \"log_line\": \"user login failed for admin from 10.0.0.5\"}\n" },
    "@timestamp" => 2026-07-31T22:24:44.863137462Z,
          "host" => { "hostname" => "rocky.localdomain" },
      "@version" => "1"
}
```

`service` et `log_line` deviennent directement de vrais champs de
l'event, **sans passer par Grok**. Différence notable avec
`stdin {}` seul (sans codec) : plus aucun champ `message` — le codec
JSON peuple l'event avec les clés du JSON plutôt que d'empiler tout le
texte brut dans un seul champ.

## Découverte : un codec de sortie était déjà utilisé, implicitement, depuis le début

Question posée après le test d'entrée : existe-t-il aussi des codecs
côté `output` ? Réponse en creusant le code source du plugin `stdout` :
```ruby
default :codec, "rubydebug"
```

**`rubydebug` est le codec par défaut de `stdout`** — c'est exactement
le format `{ "champ" => "valeur" }`, affiché sur plusieurs lignes,
qu'on observe depuis le tout premier test du Palier 1. Chaque
`stdout {}` de ce module utilisait donc déjà, implicitement, ce codec,
sans qu'on l'ait jamais précisé.

### Autres codecs de sortie utiles

- **`json`** — sortie en une seule ligne JSON compacte, plutôt que le
  format lisible multi-lignes de `rubydebug` :
```
  output {
    stdout { codec => json }
  }
```
  Rendrait par exemple l'event du test précédent sous la forme
  `{"log_line":"...","service":"app","@timestamp":"...","@version":"1", ...}`
  sur une seule ligne — plus adapté à un traitement automatisé en aval
  qu'à la lecture humaine.
- **`plain`** — sortie texte brute sans délimitation particulière
  entre les events.
- **`json_lines`** — un JSON compact par ligne, couramment utilisé
  avec le plugin `file` en sortie (un event = une ligne JSON dans le
  fichier), pratique pour être ré-ingéré facilement par un autre
  outil ensuite.

## Codec et Grok ne se remplacent pas — ils opèrent à des niveaux différents

Question clé posée avant de conclure : un codec JSON rend-il Grok
inutile ? Réponse construite par l'exemple : sur un JSON simple avec
des valeurs déjà structurées (`nom`, `valeur`...), Grok n'apporte rien
de plus — le codec a déjà fait le travail. Mais sur un JSON dont
**une valeur** est elle-même du texte libre non structuré (ici,
`log_line`), ce champ reste un bon candidat pour un futur `grok`
conditionnel — le codec structure l'enveloppe, Grok reste utile pour
le contenu texte niché à l'intérieur.

**Portée pour la suite** : le schéma de logging LLM conçu en note 46
(`tokens_entree`, `finish_reason`, `params_generation`) est
précisément le type de structure JSON propre qu'un `codec => json` en
entrée saurait exploiter directement — sans repasser par Grok pour ces
champs-là, contenu prévu du Palier 3.

## Résumé

1. Un codec est un paramètre de plugin (`input`/`output`), pas un bloc
   indépendant comme `filter`
2. Il structure la donnée **avant** la pleine construction de l'event
   (entrée) ou **au moment de l'écrire** (sortie)
3. `rubydebug` est le codec de sortie par défaut de `stdout` — utilisé
   implicitement depuis le tout premier test du module, sans jamais
   avoir été nommé explicitement jusqu'ici
4. Codec et Grok se complètent : le codec structure l'enveloppe
   globale, Grok reste nécessaire pour du texte libre niché à
   l'intérieur d'un champ déjà structuré

## Lien avec les notes existantes

`03-premier-pipeline-stdin-stdout-filter-mutate.md` (`stdin {}` sans
codec d'entrée, mais `rubydebug` déjà utilisé sans le savoir en
sortie), `04-construction-premier-pattern-grok.md` (rôle de Grok sur
du texte non structuré), note 46 module IA (schéma de logging LLM,
cible du Palier 3).

## Sources

- [Stdout output plugin (Elastic Plugins)](https://www.elastic.co/docs/reference/logstash/plugins/plugins-outputs-stdout)
- [logstash-output-stdout source (GitHub)](https://github.com/logstash-plugins/logstash-output-stdout/blob/main/lib/logstash/outputs/stdout.rb)
