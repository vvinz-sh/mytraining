# TP — Parser une sortie `ansible-playbook -v` avec un pattern grok sur mesure : résultat

Complète `tp-parsing-ansible-verbose-draft.md`. Dernier TP du Palier 2
(Parsing), sur le fichier réel `deployer_filebeat.log` (rôle
d'installation de Filebeat sur `rh8103.localdomain`, aucune task en
échec).

## Pipeline final

Voir `./tp-parse-ansible-v.conf`. Structure en `if`/`else if`/`else
if`/`else`, un bloc par famille de ligne :
1. Drop des lignes vides (`[message] == ""`)
2. `TASK [...]`/`PLAY [...]` → `ansible.type`, `ansible.name`
3. Lignes de statut (`^[a-z]+: `) → `ansible.state`, `ansible.target`
4. Ligne de récap (`ok=...changed=...`) → grok minimal (hostname) +
   `kv` → 7 compteurs + `mutate.convert` en `integer`
5. Tout le reste (`PLAY RECAP ****...` en-tête) → drop

## Constat du test baseline (avant tout grok)

Premier test avec un filtre vide, juste pour valider input/output.
Deux découvertes réelles, intégrées ensuite au design :

- **L'ordre de sortie n'est pas garanti** : la ligne `PLAY [...]`,
  première ligne du fichier source, ressortait en position 11 sur 20
  dans le fichier de sortie — Logstash ne garantit pas l'ordre
  d'écriture dès qu'il traite les events avec plusieurs workers en
  parallèle. Sans incidence ici puisque le scope du TP exclut déjà
  toute corrélation entre lignes (pas de multiline).
- **Les lignes vides produisent des events avec `message: ""`** — non
  anticipé dans la liste initiale des familles de lignes, traité par
  un `drop` en tout début de filtre pour ne pas gonfler artificiellement
  le compteur d'échecs.

## Bug découvert : les tags s'accumulent entre blocs sans condition

Première version du filtre : les trois premiers grok étaient chacun
dans leur `if` propre (pas de `else if`), et le grok de la ligne récap
tournait *sans aucune condition*, donc sur toutes les lignes arrivant
jusque-là — y compris celles déjà traitées avec succès par un grok
précédent.

**Constat empirique** : une ligne `TASK [...]` qui avait déjà réussi
son premier grok (champs `ansible.type`/`name` bien remplis) héritait
quand même du tag `_grokparsefailure` en traversant ensuite le grok
récap, qui ne la reconnaissait pas. Les tags s'ajoutent tout au long
du filtre, ils ne sont jamais remis à zéro entre deux blocs `grok` —
et l'`output`, qui ne regarde que la présence du tag, faisait passer
des lignes correctement parsées dans le fichier des échecs.

**Correction retenue** : chaîne `if`/`else if`/`else if`/`else`
complète, chaque ligne ne traverse plus qu'un seul bloc.

## Erreurs de copier-coller sur le pattern grok pur (ligne récap)

Plusieurs itérations avant que le pattern à 7 champs (`ok`, `changed`,
`unreachable`, `failed`, `skipped`, `rescued`, `ignored`) matche : clé
littérale oubliée devant un `%{NONNEGINT}` après des copier-coller trop
rapides, le format du grok pur n'aidant pas, voir plus loin kv.

Point noté au passage : un `%{SPACE}` surnuméraire entre `failed=` et le chiffre
n'a jamais fait échouer le match — `%{SPACE}` est défini comme `\s*`
(zéro ou plus), donc un `%{SPACE}` de trop matche simplement zéro
caractère, sans casser le pattern.

## Grok pur vs grok + `kv` : le contraste recherché

Les deux versions ont été écrites et testées côte à côte sur la ligne
de récap :

- **Grok pur** : un `%{NONNEGINT}` nommé par compteur, 7 fois — long à
  écrire, source d'erreurs de copier-coller (voir ci-dessus), et à
  réécrire entièrement si Ansible ajoutait un jour un 8ᵉ compteur.
  Types (`integer`) obtenus via `mutate.convert` explicite sur les 7
  champs.
- **Grok minimal + `kv`** : un grok isole juste le hostname (`grok`
  sur `%{HOSTNAME}` puis `:`), stocke le reste dans un champ
  temporaire (`recap_line`), et `kv` (`field_split => "\s+"`,
  `value_split => "="`, `target => "[ansible]"`) découpe les paires
  sans connaître leurs noms à l'avance — un futur 8ᵉ compteur serait
  capturé automatiquement, sans toucher au pipeline. Champ temporaire
  supprimé ensuite via `mutate.remove_field`.

**Point important, découvert en pratique et pas anticipé dans le
draft** : `kv` ne convertit jamais les types automatiquement. Les 7
compteurs ressortent en string (`"4"`, `"5"`...) exactement comme avec
le grok pur — la concision de `kv` porte uniquement sur l'écriture du
pattern, pas sur le typage. Le `mutate.convert` reste nécessaire dans
les deux approches.

**Bilan retenu** : `kv` donne une gestion plus fiable et sans
réécriture des structures clé/valeur (robuste à un changement du
nombre ou de l'ordre des champs), au prix d'une étape de préparation
(isoler le hostname en amont) que le grok pur n'a pas besoin de faire
séparément.

## Résultat final

12 events en sortie sur les 20 lignes du fichier source (20 - 7 lignes
vides - 1 ligne `PLAY RECAP` = 12) : **0 tag `_grokparsefailure`**.
Répartition : 6 events `ansible.type`/`name` (TASK + PLAY), 5 events
`ansible.state`/`target` (statuts), 1 event récap avec les 7
compteurs. Vérifié par calcul indépendant (`grep -cE "^$"` +
`wc -l`), pas seulement par lecture du fichier de sortie.

## Compétences pratiquées

- Écriture de plusieurs patterns grok indépendants pour plusieurs
  formats de ligne distincts dans le même fichier
- Diagnostic empirique de l'accumulation des tags entre blocs de
  filtre non protégés par une condition exclusive
- Comparaison pratique grok pur vs grok + `kv` sur une même ligne
  clé=valeur, avec un résultat contre-intuitif (`kv` ne type pas les
  champs, contrairement à une attente naturelle de "solution plus
  moderne")
- Vérification d'un résultat de pipeline par un calcul indépendant
  (comptage de lignes) plutôt que par simple relecture visuelle

## Lien avec les notes existantes

`04-construction-premier-pattern-grok.md` (`WORD` limité par un point,
groupe optionnel), `08-grok-conditionnel-kernel-gestionechec.md` et
`tp-fichier-complet-resultat.md` (routage `_grokparsefailure`,
cascade de filtres après un grok raté — même famille de bug retrouvée
ici sous une autre forme), `24-mutate-en-profondeur.md` (`convert`,
utilisé dans les deux versions de la ligne récap).
