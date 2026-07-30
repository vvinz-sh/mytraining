# Logstash — Filtre conditionnel selon le processus, GREEDYDATA vs DATA

Suite du Palier 2 — parsing spécifique selon le type de ligne
(`if [processus] == "..."`), anticipant le principe du Palier 3
(logs applicatifs structurés selon leur source).

## Objectif

Extraire le pourcentage de heap JVM sur les lignes `java-app`
uniquement, sans affecter le traitement des autres types de ligne
(`systemd`, `kernel`, `cron`...).

## GREEDYDATA vs DATA : la nuance qui a failli passer inaperçue

En construisant le second pattern (`%{LOGLEVEL} %{GREEDYDATA} Heap
usage at %{NUMBER:heap}%`), question soulevée avant de tester : que se
passerait-il si la ligne contenait **plusieurs** occurrences de
`"Heap usage at N%"` ?

Rappel du mécanisme regex : une correspondance **gourmande**
(`GREEDYDATA`, défini `.*`) avale tout jusqu'à la fin de la chaîne,
puis recule **au minimum nécessaire** pour que la suite du pattern
puisse encore matcher — elle capture donc la **dernière** occurrence
possible, pas la première. À l'inverse, `DATA` (défini `.*?`, non
gourmand) s'arrête dès la **première** occasion où le reste du
pattern matche.

Vérifié dans le fichier officiel `grok-patterns` :
```
DATA .*?
GREEDYDATA .*
```

Sur la ligne de test réelle (une seule occurrence de "Heap usage
at"), les deux se comportent identiquement — la différence n'est
visible que sur une ligne hypothétique à occurrences multiples. Reste
une bonne pratique par défaut : préférer `DATA` quand on ne cherche
qu'à "sauter" du texte sans intention de capturer plusieurs fois le
même motif.

## Bug rencontré : `%{WORD}` ne capture pas `java-app`

Premier essai avec `%{WORD:processus}` (réutilisé du pattern de base,
note 04) : échec total sur la ligne `java-app[15234]:...` — tag
`_grokparsefailure`, aucun champ extrait.

**Diagnostic** : `WORD` est défini `\b\w+\b` — `\w` ne matche que
lettres/chiffres/underscore, **pas le tiret**. `java-app` contient un
tiret, donc `WORD` s'arrête net à `java` et le reste du pattern
(`\[%{POSINT}\]`) ne correspond plus à ce qui suit (`-app[15234]`).

**Correction** : remplacer `%{WORD:processus}` par `%{PROG:processus}`
— pattern dédié, défini `[\x21-\x5a\x5c\x5e-\x7e]+` (plage ASCII
couvrant lettres, chiffres, ponctuation courante, **à l'exclusion
volontaire des crochets** `[` et `]`, codes `\x5b`/`\x5d` sautés entre
les deux plages). `PROG` accepte le tiret et tout caractère hors
crochet — exactement pensé pour matcher un nom de processus jusqu'au
`[PID]` qui suit, sans jamais avaler les crochets par erreur. C'est
d'ailleurs le pattern utilisé dans `SYSLOGPROG` officiel, pas `WORD`.

## Pattern final

```
input {
  stdin {}
}

filter {
  grok {
    match => { "message" => "%{SYSLOGTIMESTAMP:timestamp} %{HOSTNAME:hostname} %{PROG:processus}(?:\[%{POSINT}\])?: %{GREEDYDATA:message_parse}" }
  }

  if [processus] == "java-app" {
    grok {
      match => { "message_parse" => "%{LOGLEVEL:niveau} %{DATA}Heap usage at %{NUMBER:heap}%" }
    }
  }
}

output {
  stdout {}
}
```

## Résultat validé

Sur `java-app` : `processus`, `niveau` (`WARN`), `heap` (`89`) tous
correctement extraits, en plus des champs de base (`timestamp`,
`hostname`). Sur `systemd` : uniquement les champs de base, le
second filtre grok ne s'est pas déclenché — le conditionnel
fonctionne comme prévu.

## Résumé

1. `GREEDYDATA` (gourmand) capture la **dernière** occurrence
   possible en cas d'ambiguïté ; `DATA` (non gourmand) la **première**
   — préférer `DATA` par défaut pour "sauter" du texte sans intention
   de capture répétée
2. `WORD` (`\w`) n'accepte pas le tiret — `PROG` est le bon choix pour
   un nom de processus, car conçu pour s'arrêter avant les crochets du
   PID sans les avaler
3. Le conditionnel `if [champ] == "valeur"` permet d'appliquer un
   second filtre grok ciblé, sans perturber le traitement des autres
   types de ligne

## Lien avec les notes existantes

`04-construction-premier-pattern-grok.md` (pattern de base, `PROG`
déjà présent dans `SYSLOGPROG` officiel sans qu'on l'ait remarqué à
l'époque).

## Sources

- [logstash-patterns-core — grok-patterns (ECS v1)](https://github.com/logstash-plugins/logstash-patterns-core/blob/main/patterns/ecs-v1/grok-patterns)
