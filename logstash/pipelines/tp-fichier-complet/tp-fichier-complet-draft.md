# TP — Reparser le fichier complet (520 lignes) via input file (draft)

Statut : **design posé, pas encore exécuté**. Clôture pratique du
Palier 2 (Parsing) — premier test à l'échelle du **fichier entier**,
plutôt que ligne par ligne via `stdin` comme jusqu'ici.

## Objectif

Consolider tous les patterns/filtres construits séparément (notes
04, 05, 07, 08, 13, 24) en un **seul** `.conf` définitif, testé sur
le vrai fichier `tp-ansible-agent` (520 lignes, disque plein en
cascade) présent sur Rocky9 : `/var/log/messages-incident`.

## Étape 1 — Consolidation du pipeline

Assembler dans un seul fichier :
- Pattern de base externalisé (`SYSLOGBASE_PERSO`, `patterns_dir`,
  note 13)
- Bloc `if [processus] == "java-app"` — niveau + % heap (note 05)
- Bloc `if [processus] == "backup-job"` — taille/unité/bytes/dossiers
  inclus-exclus (notes 07, 24)
- Bloc `if [processus] == "kernel"` — format/niveau/détails (note 08)
- Filtre `date` — remplacer `@timestamp`, préserver `event.created`
  (note 15)
- Routage de sortie : `_grokparsefailure` → fichier séparé,
  sinon → sortie normale (note 08)

## Étape 2 — Passage de `stdin` à `input file`

Changement d'input, jamais testé jusqu'ici sur un vrai fichier statique
complet :
```
input {
  file {
    path => "/var/log/messages-incident"
    start_position => "beginning"
    sincedb_path => "/dev/null"
  }
}
```

**Point de vigilance à vérifier en pratique** : `sincedb_path => "/dev/null"`
force une relecture depuis le début à **chaque redémarrage** du
pipeline (utile pour un test répétable), mais rappelle-toi la note 12
— ce réglage seul ne garantit pas un vrai comportement de "boucle
automatique" en cours d'exécution (déjà expérimenté avec `exec`
récemment) ; ici l'objectif est juste une lecture complète unique par
lancement, pas un rejeu périodique.

**Permissions à vérifier avant de lancer** : le fichier
`/var/log/messages-incident` est-il lisible par l'utilisateur système
`logstash` (celui qui exécute le service), ou faut-il ajuster les
permissions/le groupe comme on l'a fait pour `conf.d.perso` (note 12) ?

## Étape 3 — Vérification quantitative des échecs

Compter le nombre de lignes traitées avec succès vs en échec :
```bash
wc -l /home/vinz/logstash-lab/logstash_failed_logs.log
```
Comparer au total de 520 lignes du fichier source, pour avoir un
vrai ratio succès/échec plutôt qu'une impression qualitative.

## Ce qu'il faudra vérifier/clarifier en exécutant

- Est-ce que des lignes `nginx`/`sshd`/`postfix`/autres (non couvertes
  par un bloc conditionnel dédié) génèrent un vrai `_grokparsefailure`,
  ou passent-elles simplement avec le socle de base seul (pas un échec
  au sens strict, juste sans enrichissement) — **scope volontairement
  limité au binaire ok/nok pour ce TP**, sans creuser cette nuance
  (réservée à un futur TP, pour ne pas empiéter dessus)
- Le volume réel d'échecs sur 520 lignes — attendu non nul, mais
  ampleur à mesurer plutôt que supposer

## Compétences pratiquées

- Consolidation de plusieurs filtres construits séparément en un seul
  pipeline de production cohérent
- Premier test `input file` à l'échelle d'un vrai fichier complet,
  après plusieurs sessions de test ligne par ligne via `stdin`
- Mesure quantitative d'un taux de succès/échec de parsing, plutôt
  qu'une observation qualitative

## Lien avec les notes existantes

Toutes les notes du thème `parsing/` (04, 05, 07, 08, 13, 15, 24),
`12-pipelines-config.md` (permissions filesystem pour le service
`logstash`, limite du "rejeu" via `sincedb_path`).
