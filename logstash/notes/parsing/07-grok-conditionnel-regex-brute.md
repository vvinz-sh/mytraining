# Logstash — Filtre conditionnel backup-job, groupes nommés en regex brute

Suite du Palier 2 — deuxième bloc conditionnel selon `processus`
(après `java-app`, note 05), extraction de la taille d'archive
sur les lignes `backup-job`.

## Log de test

```
Jul 21 08:15:33 rh8102 backup-job[1234]: Writing archive... 45GB written
```

Après le pattern de base (note 04), `message_parse` contient
`"Writing archive... 45GB written"`.

## Premier essai : pattern hardcodé, corrigé en cours de route

Essai initial : `"Writing archive... %{NUMBER:backup_gb_written}GB
written"` — fonctionne, mais code en dur l'unité `GB`. Si
`backup-job` loggue un jour en `MB` (archive plus petite), ce pattern
échouerait purement et simplement.

**Correction 1** : capturer aussi l'unité, avec `%{DATA:backup_size_unit}`
à la place du texte figé `GB`. Fonctionne, mais `DATA` (`.*?`) est
trop permissif sémantiquement — il pourrait capturer n'importe quoi,
pas seulement une unité de taille.

## Pourquoi `%{WORD}` échoue ici — leçon sur les limites de mot (`\b`)

Tentative de remplacer `DATA` par `WORD` pour être plus précis : échec.

**Diagnostic** : `WORD` est défini `\b\w+\b` — les `\b` (limites de
mot) exigent une transition entre un caractère `\w`
(lettre/chiffre/underscore) et un caractère qui n'en est pas. Dans
`45GB`, le `5` et le `G` sont **tous deux** des caractères `\w` —
aucune transition, donc aucune limite de mot à cet endroit. `WORD` ne
peut même pas **démarrer** à cette position, contrairement à `PROG`
(pas de `\b` dans sa définition).

`PROG` fonctionnerait, mais reste trop large (accepte aussi la
ponctuation) pour capturer strictement une unité alphabétique.

**Constat** : il n'existe pas de pattern Grok générique du type
`UNIT` — logique, une unité de taille (`GB`), de température (`°C`)
ou de temps (`ms`) n'ont rien de commun au niveau caractères. À un
moment, écrire une regex sur mesure devient la bonne solution, pas un
aveu d'échec.

## Groupes nommés en regex brute : `(?<nom>...)`

Une fois la regex `[A-Za-z]+` choisie (lettres uniquement, strictement
adapté à une unité), tentative erronée de la nommer avec la syntaxe
Grok classique (`%{...}`) — ne fonctionne pas, car `[A-Za-z]+` n'est
pas un pattern Grok nommé, c'est de la regex brute.

**Syntaxe correcte** (Oniguruma, moteur regex de Grok) :
```
(?<nom_du_champ>regex)
```
Les chevrons `<` et `>` sont une syntaxe **obligatoire**, pas une
convention stylistique — un piège facile à l'écrit
(`(?<backup_size_unit>[A-Za-z]+)`, pas
`(?backup_size_unit[A-Za-z]+)`).

## Pattern final

```
if [processus] == "backup-job" {
  grok {
    match => { "message_parse" => "Writing archive... %{NUMBER:backup_size}(?<backup_size_unit>[A-Za-z]+) written" }
  }
}
```

## Amélioration : regrouper les champs liés sous un objet parent

Observation faite après coup : `backup_size` et `backup_size_unit`
apparaissaient comme deux champs plats et sans lien visible entre eux
dans l'event, malgré une relation logique évidente (une taille et son
unité).

**Solution** : la même notation entre crochets déjà vue dans
`SYSLOGPROG` officiel (`%{PROG:[process][name]}`) permet de créer une
structure imbriquée directement dans le nom de champ :

```"Writing archive... %{NUMBER:[backup][size]}(?<[backup][unit]>[A-Za-z]+) written"```

Résultat : `backup: { size: "45", unit: "GB" }` plutôt que deux champs
plats séparés — Logstash fusionne automatiquement les deux valeurs
sous le même objet parent `backup`.

**Portée au-delà de l'esthétique** : ce principe de regroupement est
exactement celui suivi par l'**ECS** (Elastic Common Schema, déjà
croisé dans le nom du fichier `ecs-v1` des patterns officiels) —
grouper les champs liés sous un objet commun (`backup.size`,
`process.name`) plutôt que tout mettre à plat, pour une cohérence
exploitable ensuite par des dashboards Kibana génériques (Palier 5).

## Résumé

1. Pas de pattern Grok générique pour une "unité" — écrire une petite
   regex sur mesure (`[A-Za-z]+`) est la bonne solution ici, pas un
   échec de recherche du bon pattern nommé
2. `WORD` échoue quand le texte à capturer touche directement un
   chiffre sans transition — cause : les `\b` exigent un changement
   de catégorie de caractère, absent entre chiffre et lettre
3. Nommer une capture en regex brute nécessite `(?<nom>...)`, syntaxe
   obligatoire (chevrons compris), distincte de `%{nom:pattern}`
   réservée aux patterns Grok prédéfinis
4. `stdin` n'est jamais compatible avec `--config.reload.automatic` —
   limitation du plugin, pas de la configuration

## Lien avec les notes existantes

`04-construction-premier-pattern-grok.md` (pattern de base),
`05-grok-filtre-conditionnel-greedydata-data.md` (premier filtre
conditionnel, leçon `WORD` vs `PROG`), `06-options-cli-confort.md`
(`--config.reload.automatic`, limite découverte ici).
