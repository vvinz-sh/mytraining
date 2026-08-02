# TP — Reparser le fichier complet (520 lignes) via input file : résultat

Complète `tp-fichier-complet-draft.md`. Premier test à l'échelle du
fichier entier, après plusieurs sessions de test ligne par ligne via
`stdin`.

## Pipeline consolidé

Assemblage de tout ce qui avait été construit séparément : pattern de
base externalisé (`SYSLOGBASE_PERSO`), filtre `date` (préservation
`event.created`), et trois blocs conditionnels (`java-app`,
`backup-job`, `kernel`), avec routage `_grokparsefailure` vers un
fichier séparé.

Voir `./pipeline-consolide.conf`


## Bug 1 découvert : cascade de filtres après un grok raté

Sur des lignes `backup-job` avec un format non couvert au départ,
observation de **deux** tags simultanés : `_grokparsefailure` **et**
`_bytesparsefailure`. Diagnostic : un échec de `grok` n'interrompt pas
la chaîne de filtres (principe déjà connu, note 08) — mais `mutate`/
`bytes`, placés juste après **dans le même bloc conditionnel**,
continuaient de s'exécuter sur des champs vides, produisant un
second échec en cascade.

**Recherche menée** : pas de paramètre natif pour "n'exécuter la
suite que si le grok précédent a réussi" — la pratique standard,
confirmée par plusieurs sources concordantes, est une condition
manuelle sur l'absence du tag :
```
if "_grokparsefailure" not in [tags] {
  ...
}
```

## Bug 2 découvert : le pattern MINUTE officiel n'accepte pas un seul chiffre

9 lignes `systemd` du type `"Jul 21 07:1:00 rh8102 systemd[1]:
Started Session 1 of user root."` échouaient sur le pattern de base
lui-même, pas un bloc conditionnel.

**Diagnostic, vérifié dans les définitions officielles** :
```
HOUR   (?:2[0123]|[01]?[0-9])
MINUTE (?:[0-5][0-9])
SECOND (?:(?:[0-5]?[0-9]|60)(?:[:.,][0-9]+)?)
```
`MINUTE` exige strictement **2 chiffres** (`[0-5][0-9]`, aucun `?`
optionnel) — contrairement à `SECOND` (`[0-5]?[0-9]`, 1 ou 2 chiffres
acceptés) et `HOUR` (`[01]?[0-9]`, également tolérant). Explique
directement pourquoi `08:30:1` (seconde à un chiffre, note 15)
fonctionnait, mais `07:1:00` (minute à un chiffre) échoue — une
asymétrie réelle dans la définition officielle, pas un hasard.

**Décision retenue** : accepté comme échec légitime — le log source
est mal formé au regard du standard syslog, pas notre pipeline qui
est en défaut. Pas de correction du pattern de base pour ce TP.

## Extension : backup-job couvre maintenant 4 formulations

Découverte de 3 formulations `backup-job` jamais couvertes
(`"Starting full backup..."`, `"Backup failed..."`, `"Cleanup
incomplete..."`), en plus de `"Writing archive..."` déjà connu.

**Choix de conception** : plutôt que d'empiler des blocs `if`
imbriqués (comme pour `kernel`), utilisation d'une **liste de
patterns** dans un seul `match`, essayés dans l'ordre — première
mise en pratique réelle de ce point resté en attente au programme
(README, Palier 3). Erreurs de syntaxe corrigées en cours de route :
- Clé `"message_parse"` répétée plusieurs fois dans le même hash
  (silencieusement écrasée) au lieu d'un tableau unique
- Tentative d'utiliser une syntaxe clé/valeur (`"nom" => "pattern"`)
  à l'intérieur du tableau, alors qu'un tableau ne contient qu'une
  **liste de valeurs**, sans nom devant chacune

## Découverte méthodologique : le fichier d'échec est cumulatif entre les runs

Une confusion en cours de session (résolue) a révélé un point
important, confirmé via plusieurs sources concordantes : le plugin
`output { file {...} }` **n'écrase jamais** automatiquement à chaque
redémarrage — `write_behavior => "append"` par défaut, sans
mécanisme natif pour vider le fichier au démarrage. Une trace d'un
test précédent (fait via `stdin` en note 08) était donc restée mêlée
aux résultats de ce nouveau TP, faussant le premier comptage.

**Bonne pratique retenue** : toujours vider explicitement
`logstash_failed_logs.log` avant un nouveau test propre, plutôt que
de laisser les runs s'accumuler silencieusement.

## Résultat final

Sur les 520 lignes réelles du fichier : **9 vrais échecs**, tous des
sessions `systemd` avec minute à un chiffre (log source mal formé,
limite légitime du pattern officiel) — soit **97,7% de réussite**.
`backup-job` entièrement couvert (4 formulations), `java-app` et
`kernel` inchangés et toujours fonctionnels.

## Compétences pratiquées

- Consolidation de plusieurs filtres construits séparément en un
  seul pipeline de production cohérent
- Premier test `input file` à l'échelle d'un vrai fichier complet
- Garde-fou explicite contre la cascade d'échecs de filtres
- Liste de patterns Grok essayés dans l'ordre, alternative aux blocs
  `if` imbriqués
- Diagnostic d'une anomalie de comptage par élimination méthodique
  (vérification du fichier source, du comportement du plugin de
  sortie, avant de conclure à un bug de pipeline)

## Lien avec les notes existantes

Toutes les notes du thème `parsing/` (04, 05, 07, 08, 13, 15, 24),
`12-pipelines-config.md` (permissions filesystem).
