# TP — Parser une sortie `ansible-playbook -v` avec un pattern grok sur mesure (draft)

Statut : **design posé, pas encore exécuté**. Dernier TP du Palier 2
(Parsing). Fait suite au TP fichier complet — même logique (grok
custom, routage des échecs), mais sur une sortie structurée
différente : `ansible-playbook -v`, plutôt qu'un syslog.

## Contexte

Log source : `deployer_filebeat.log`, sortie réelle d'un
`ansible-playbook -v` exécutant le rôle d'installation de Filebeat
sur `rh8103.localdomain` (en cours de construction pour le Palier 3).
Aucune task en échec dans cette exécution (`failed=0` au `PLAY RECAP`)
— ce TP porte donc uniquement sur `ok`/`changed`, pas sur `failed`.

**Option retenue : plusieurs patterns grok
indépendants, plusieurs types d'event, sans corrélation entre eux.** Le
nom de la task et son statut vivent sur deux lignes séparées dans la
sortie `-v` ; les recoller en un seul event demanderait le filtre
`multiline` (ou `aggregate`), pas encore vu — hors scope volontaire de
ce TP, réservé au Palier 3.

**Scope étendu : la ligne de récap
(`rh8103.localdomain : ok=5 changed=4 ...`) entre aussi dans le
périmètre** — troisième pattern grok à écrire, en plus de `TASK` et du
statut. Les lignes `PLAY [...]` et `PLAY RECAP ****...` (les deux
en-têtes, pas la ligne de données qui suit) restent hors scope pour
l'instant, sauf si tu changes d'avis en cours de route.

**Fixture (décision prise) : `deployer_filebeat.log` sera committé
dans le repo**, dans ce même dossier, comme fixture de test.

## Étape 1 — Repérer les formats de ligne présents dans le fichier

Avant d'écrire un seul pattern, lister à l'œil les familles de lignes
réellement présentes dans `deployer_filebeat.log` :

1. `PLAY [Déployer Filebeat sur les VM de lab] ****...`
2. `TASK [Gathering Facts] ****...`
3. `TASK [filebeat : Importer la clé GPG Elastic] ****...`
4. `ok: [rh8103.localdomain]` (pas de `=>`, pas de JSON — cas de
   `Gathering Facts`)
5. `changed: [rh8103.localdomain] => {"changed": true}` (JSON minuscule)
6. `changed: [rh8103.localdomain] => {"changed": true, ... "status":
   {...énorme bloc systemd...}}` (JSON massif, sur une seule ligne)
7. `PLAY RECAP ****...`
8. `rh8103.localdomain         : ok=5    changed=4    unreachable=0
   ...` (ligne de résumé clé=valeur)

Scope retenu : 3 (`TASK`), 4/5/6 fusionnées (statut), et 8 (récap) —
soit trois patterns grok distincts. Les lignes 1, 2 et 7 (`PLAY [...]`,
`TASK [Gathering Facts]` en tant qu'en-tête, `PLAY RECAP ****...`)
restent hors scope, elles tomberont en `_grokparsefailure` — attention,
la ligne 2 `TASK [Gathering Facts]` matche bien le pattern de l'étape 2
(c'est une ligne `TASK` comme les autres), seule sa ligne de statut
associée (`ok: [rh8103.localdomain]`, sans JSON) est un cas particulier
à couvrir dans l'étape 3.

## Étape 2 — Pattern pour les lignes `TASK [...]`

Point de vigilance déjà rencontré une fois (note 04, groupe optionnel
raté) : `TASK` et `PLAY` partagent la même forme `MOT [texte] ****`,
donc un pattern trop permissif sur `TASK` risque de matcher aussi les
lignes `PLAY`/`PLAY RECAP` par erreur. À vérifier en testant
explicitement une ligne `PLAY [...]` contre le pattern une fois écrit
— pas juste supposer que l'ancrage `^TASK` suffit sans l'avoir observé.

## Étape 3 — Pattern pour les lignes de statut

Piège probable, à confirmer en pratique : le pattern `WORD` (utilisé
en note 04 pour le nom de process) ne matche pas un point (`.`) —
or l'hostname ici est `rh8103.localdomain`, pas juste `rh8103`. Un
pattern générique `WORD` pour capturer le host échouerait
silencieusement ou tronquerait au premier point. Comparer avec
`HOSTNAME` (pattern grok dédié) ou `NOTSPACE`/`DATA` avant de choisir.

Pour la partie JSON après `=>` (quand elle existe) : `GREEDYDATA` en
un seul champ brut, sans tenter de parser le JSON dans le pattern grok
lui-même — un vrai parsing JSON imbriqué se ferait avec le filtre
`json`, hors scope ici (déjà vu en survol en Palier 1, note 10, mais
pas appliqué à une sous-chaîne extraite d'un autre champ).

## Étape 4 — Pattern pour la ligne de récap

Format cible :
```
rh8103.localdomain         : ok=5    changed=4    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```
Une suite de paires `clé=valeur` séparées par des espaces variables,
après un hostname et `:`. Deux approches possibles, à choisir toi-même
en pratique plutôt qu'à trancher ici :

1. **Grok pur** — un champ nommé par paire (`ok`, `changed`,
   `unreachable`, `failed`, `skipped`, `rescued`, `ignored`), chacun en
   `%{NONNEGINT}`, avec `%{SPACE}` entre chaque pour absorber
   l'espacement irrégulier
2. **Grok minimal + filtre `kv`** — un grok qui isole juste le
   hostname, puis le filtre `kv` (pas encore vu, clé=valeur générique)
   sur le reste de la ligne — plus robuste si l'ordre ou le nombre de
   champs change un jour, mais introduit un nouveau filtre non prévu
   au programme du Palier 2

Même remarque qu'à l'étape 3 : ces champs sont déjà **numériques**
dans leur sens naturel (compteurs) — vérifier si `mutate.convert`
(note 24, déjà pratiqué) doit s'appliquer ici aussi, ou si un pattern
grok numérique dédié (`%{NONNEGINT}`) suffit à les stocker en tant que
nombres dès l'extraction.

## Étape 5 — Test et routage des échecs

Réutiliser le routage `_grokparsefailure` déjà en place (note 08,
consolidé note tp-fichier-complet) pour voir concrètement ce qui tombe
en échec : `PLAY`, `PLAY RECAP` (l'en-tête), et toute ligne dont le
format diffère de ce qui a été anticipé à l'étape 1.

## Ce qu'il faudra vérifier/clarifier en exécutant

- `WORD` vs `HOSTNAME` pour le champ host — à trancher par
  observation, pas par supposition (voir Étape 3)
- Le JSON massif de la task "Activer et démarrer le service Filebeat"
  contient des accolades/guillemets imbriqués sur une seule ligne
  physique — confirmer que `GREEDYDATA` s'en sort sans souci
  (attendu : oui, puisqu'aucun retour à la ligne réel à l'intérieur),
  mais à vérifier plutôt que supposer
- Grok pur vs grok + filtre `kv` pour la ligne de récap (Étape 4) — à
  décider en pratique, sachant que `kv` sort du programme prévu du
  Palier 2
- Les compteurs de la ligne de récap doivent-ils être convertis en
  entiers (`mutate.convert`, déjà pratiqué note 24) ou un pattern grok
  numérique dédié suffit-il directement à l'extraction

## Compétences pratiquées

- Écriture de plusieurs patterns grok indépendants pour plusieurs
  formats de ligne distincts dans le même fichier, sans chercher à les
  corréler prématurément
- Reconnaissance empirique des limites d'un pattern générique (`WORD`)
  face à une donnée réelle (hostname avec point)
- Extraction d'un bloc JSON en `GREEDYDATA` sans sur-ingénierie
  (pas de parsing JSON imbriqué à ce stade)
- Parsing d'une ligne clé=valeur à espacement irrégulier, avec un choix
  assumé entre grok pur et introduction du filtre `kv`
- Gestion d'une fixture de test versionnée dans le repo, pour un
  résultat non reproductible depuis la source (JSON systemd variable)

## Lien avec les notes existantes

`04-construction-premier-pattern-grok.md` (groupe optionnel raté,
`WORD` déjà limité une fois), `08-grok-conditionnel-kernel-gestionechec.md`
et `tp-fichier-complet-resultat.md` (routage `_grokparsefailure`),
`10-codecs-structuration-input-output.md` (codec/filtre `json`, pas
encore appliqué à un sous-champ), `24-mutate-en-profondeur.md`
(`convert`, pertinent pour les compteurs de la ligne de récap).
