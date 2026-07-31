# Logstash — Filtre conditionnel kernel, gestion des échecs de parsing (_grokparsefailure)

Suite du Palier 2 — troisième bloc conditionnel selon `processus`
(après `java-app` note 05, `backup-job` note 07), et mise en place
d'une vraie gestion d'erreur pour les échecs de parsing, plutôt que de
les laisser filer silencieusement.

## Lignes de test

```
Jul 21 08:22:10 rh8102 kernel: EXT4-fs warning: /var running low on free space (2% remaining)
Jul 21 08:23:01 rh8102 kernel: EXT4-fs error: No space left on device
Jul 21 08:25:00 rh8102 kernel: EXT4-fs error: /var: filesystem full
```

## Vérification préalable : `LOGLEVEL` couvre-t-il `warning`/`error` en minuscules ?

Doute légitime avant de réutiliser `LOGLEVEL` (déjà vu en majuscules,
`WARN`, pour `java-app`). Vérifié dans le fichier officiel :
```
LOGLEVEL (...|[Ww]arn?(?:ing)?|WARN?(?:ING)?|[Ee]rr?(?:or)?|ERR?(?:OR)?|...)
```
Le `?` après certaines lettres couvre les variantes courtes/longues et
casse — `warning`/`error` en minuscules sont bien pris en charge.

## Construction du pattern, erreurs successives

1. **Mauvais champ ciblé au départ** : premier essai avec `match =>
   { "message" => ... }` en re-matchant `SYSLOGTIMESTAMP`/`HOSTNAME`/
   `PROG` — refaisait le travail déjà accompli par le pattern de base
   (note 04). Corrigé en ciblant `message_parse` (le reste de la ligne
   après extraction du préfixe), avec un pattern plus court.
2. **Groupe optionnel injustifié** : `(?:%{DATA:fs} %{LOGLEVEL:level})?`
   — aucune des trois lignes de test n'omet ce préfixe EXT4-fs+niveau,
   donc le rendre optionnel ajoutait de la complexité sans besoin
   avéré (contrairement au PID sur `kernel`/`systemd`, où l'absence
   était réellement observée). Retiré.
3. **`GREEDYDATA` sans nom de champ** — capturait le texte mais ne le
   stockait nulle part. Nommé `details`.

## Pattern final, avec regroupement façon ECS

Repris le principe de regroupement des champs liés (`[fs][format]`,
`[fs][level]`) déjà mis en place pour `backup-job` (note 07) :

```
if [processus] == "kernel" {
  grok {
    match => { "message_parse" => "%{DATA:[fs][format]} %{LOGLEVEL:[fs][level]}: %{GREEDYDATA:details}" }
  }
}
```

Résultat sur les trois variantes : `fs.format` (`EXT4-fs`), `fs.level`
(`warning`/`error`), `details` (le reste) — tous correctement
extraits, PID absent (kernel) toujours géré par le groupe optionnel du
pattern de base.

## Que se passe-t-il en cas d'échec de parsing ?

Question posée avant d'aller plus loin : si une ligne `kernel` sans
rapport avec un système de fichiers apparaît (ex : message USB,
réseau), le pattern ci-dessus échouerait. Qu'arrive-t-il à l'event
dans ce cas ?

**Comportement par défaut confirmé** : un échec de `grok` n'interrompt
**pas** la chaîne de filtres. L'event continue son chemin jusqu'à
`output`, simplement marqué d'un tag `_grokparsefailure` dans le champ
`tags` — aucune donnée perdue, juste un signal d'échec ajouté,
silencieux par défaut si on ne fait rien de ce tag.

## Décision : ni silence total, ni perte de données

Un échec silencieux n'est jamais souhaitable, mais perdre l'event ne
l'est pas non plus. Solution retenue : utiliser le tag comme point
d'accroche pour **router** l'event vers une sortie séparée plutôt que
de le laisser filer vers la sortie normale sans distinction — garde la
donnée, tout en fournissant un signal exploitable (base pour un futur
alerting si ce fichier séparé n'est pas vide).

**Erreur de syntaxe corrigée en cours de route** : `if _grokparsefailure
in [tags]` sans guillemets — `_grokparsefailure` est une **valeur
littérale** cherchée à l'intérieur du champ `tags`, pas un nom de
champ ; elle doit être entre guillemets (`"_grokparsefailure"`), comme
toute valeur comparée dans une condition (cohérent avec
`[processus] == "java-app"` déjà vu).

## Pipeline complet testé

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

  if [processus] == "backup-job" {
    grok {
      match => { "message_parse" => "Writing archive... %{NUMBER:[backup][size]}(?<[backup][unit]>[A-Za-z]+) written" }
    }
  }

  if [processus] == "kernel" {
    grok {
      match => { "message_parse" => "%{DATA:[fs][format]} %{LOGLEVEL:[fs][level]}: %{GREEDYDATA:details}" }
    }
  }
}

output {
  if "_grokparsefailure" in [tags] {
    file {
      path => "/home/vinz/logstash-lab/logstash_failed_logs.log"
    }
  } else {
    stdout {}
  }
}
```

## Résultat validé

Ligne EXT4 normale → `stdout`, tous les champs correctement extraits
(`fs.format`, `fs.level`, `details`). Ligne USB (hors périmètre du
pattern EXT4) → redirigée vers `logstash_failed_logs.log`, tag
`_grokparsefailure` visible dans le fichier — comportement conforme à
ce qui était visé.

## Résumé

1. Un échec de `grok` n'arrête jamais la chaîne de filtres — l'event
   continue, juste tagué `_grokparsefailure`, silencieusement si rien
   n'exploite ce tag
2. Router les events en échec vers une sortie séparée (plutôt que de
   les laisser se mélanger avec les events réussis) préserve la
   donnée tout en la rendant détectable — base pour un futur alerting
3. Ne pas rendre un groupe optionnel "par précaution" sans avoir
   observé un vrai cas qui le justifie — complexité inutile sinon
4. Une valeur littérale recherchée dans un champ tableau (`"x" in
   [tags]`) nécessite les guillemets, au même titre qu'une valeur
   comparée dans un `==`

## Lien avec les notes existantes

`04-construction-premier-pattern-grok.md` (pattern de base),
`05-grok-filtre-conditionnel-greedydata-data.md` (premier conditionnel,
`java-app`), `07-grok-conditionnel-regex-brute.md` (`backup-job`,
regroupement ECS repris ici pour `kernel`).

## Sources

- [How to Handle Non-matching Logstash Grok Filters (Better Stack)](https://betterstack.com/community/questions/how-to-handle-non-matching-logstash-grok-filters/)
- [Log Analysis - Troubleshoot Logstash with Its Logs (IBM)](https://www.ibm.com/support/pages/log-analysis-troubleshoot-logstash-its-logs)
- [logstash-patterns-core — grok-patterns (ECS v1)](https://github.com/logstash-plugins/logstash-patterns-core/blob/main/patterns/ecs-v1/grok-patterns)
