# Logstash — Codec `multiline` : fonctionnement conceptuel (buffer, `negate`, `what`)

Ouverture du Palier 3, amorcée directement depuis le TP de parsing
`ansible-playbook -v` (Palier 2) : le nom de la task et son statut
vivent sur deux lignes séparées, un cas d'usage naturel pour
`multiline`. Session purement conceptuelle — pattern raisonné et
tracé à la main, **pas encore implémenté ni testé** sur le fichier
réel. L'implémentation (config complète, test sur
`deployer_filebeat.log`) fera l'objet d'une session séparée.

## Premier point : `multiline` n'est pas un filtre, c'est un codec

Question de départ : `multiline` doit-il se configurer dans le bloc
`filter` (comme `grok`, `mutate`, déjà manipulés au Palier 2), ou
ailleurs ?

Raisonnement suivi : un pipeline Logstash traite les events avec
plusieurs workers en parallèle une fois qu'ils sont dans le `filter`
— constaté empiriquement lors du TP `ansible-playbook -v` (ordre de
sortie non garanti, `PLAY [...]` ressorti en position 11 sur 20).
Recoller deux lignes *consécutives* du fichier source n'a de sens que
si l'ordre séquentiel est encore garanti à ce moment-là — donc
**avant** la parallélisation, pas après.

**Conclusion** : `multiline` est un **codec**, configuré sur
l'`input` (`codec => multiline { ... }`), pas un filtre. Cohérent avec
la distinction déjà posée en note 10 (Palier 1) — un codec structure
les données en entrée/sortie, un filtre transforme des events déjà
individualisés.

## Fonctionnement interne : un buffer, pas un simple "regarde en arrière"

Le codec traite les lignes une par une, **dans l'ordre du fichier**,
et maintient un buffer interne qui accumule les lignes d'un même
event en cours de construction. Pour chaque nouvelle ligne, une seule
question : *cette ligne continue-t-elle le buffer courant, ou faut-il
d'abord flush (émettre) le buffer comme event terminé, puis démarrer
un nouveau buffer avec cette ligne ?*

- Ligne qui "continue" → ajoutée au buffer courant
- Ligne qui "démarre un nouveau groupe" → flush du buffer courant tel
  quel comme event complet, puis nouveau buffer initialisé avec cette
  ligne

`what => "previous"` désigne donc littéralement **le buffer pas
encore flush**, pas un event déjà émis en sortie — distinction qui
n'était pas évidente au premier abord.

## Deux façons d'écrire la même règle — et leurs conséquences différentes

Cas d'étude : recoller `TASK [...]`/`PLAY [...]` avec la ligne de
statut qui suit (`ok:`/`changed:`), en gardant en tête que le fichier
contient aussi des lignes vides et une ligne de récap
(`ok=5 changed=4 ...`), ni `TASK`/`PLAY` ni statut.

**Option A — décrire la ligne à rattacher** :
```
pattern => "^(ok|changed|failed|unreachable|skipped): "
what => "previous"
```
Une ligne qui matche rejoint le buffer. Une ligne qui ne matche pas
déclenche un flush + nouveau départ.

**Option B — décrire la frontière (l'en-tête)** :
```
pattern => "^(TASK|PLAY) \["
negate => true
what => "previous"
```
Une ligne qui matche `TASK`/`PLAY` (donc, avec `negate`, la condition
s'inverse) déclenche un flush + nouveau départ. Toute ligne qui ne
matche **pas** ce pattern rejoint le buffer courant.

Les deux options donnent le même résultat sur le cas nominal
(`TASK`+statut). Elles divergent sur les lignes vides et la ligne de
récap — aucune des deux ne matche `TASK`/`PLAY`, ni `ok:`/`changed:`.

## Le piège tracé à la main : l'Option A génère des events parasites

Traçage ligne par ligne de la séquence `TASK` → `changed:` → (ligne
vide) → `TASK` suivant, avec l'**Option A** :

1. `TASK [...]` — ne matche pas `^(ok|changed|...)`  → flush (buffer
   vide au départ) + nouveau buffer = `[TASK]`
2. `changed: [...]` — matche → buffer = `[TASK, changed]`
3. *(ligne vide)* — ne matche pas → **flush** de `[TASK, changed]`
   comme event complet, **puis** nouveau buffer démarré avec la ligne
   vide elle-même dedans = `[""]`
4. `TASK [...]` suivant — ne matche pas non plus → **flush** de `[""]`
   comme son propre event, contenant uniquement une ligne vide

Résultat : en plus des events `TASK`+statut correctement recollés,
apparition d'un **event parasite par ligne vide** — un event dont le
contenu est juste une chaîne vide, qui n'existait pas avant
l'introduction de `multiline` (avant, chaque ligne vide restait un
event séparé normal et sans conséquence sur les autres ; avec
l'Option A, elle en flush un autre puis devient elle-même un
mini-event dégénéré).

Même traçage avec l'**Option B** (`negate` sur `TASK`/`PLAY`) : la
ligne vide ne matche pas `^(TASK|PLAY) \[` → avec `negate`, elle
**rejoint le buffer courant** au lieu de le flusher. Elle ne devient
jamais un event isolé, et ne déclenche pas de flush prématuré.

## Leçon retenue

Avec `multiline`, la question à se poser n'est jamais *"quel pattern
décrit la ligne que je veux rattacher"*, mais **"quel pattern décrit
fidèlement la frontière entre deux events"**. Une règle qui semble
correcte sur le cas nominal peut se comporter différemment sur des
lignes qu'on n'avait pas en tête au moment de l'écrire (ici, les
lignes vides) — décrire la frontière (l'en-tête, avec `negate`) s'est
montré structurellement plus robuste à ce genre d'angle mort que
décrire le contenu à rattacher.

## Reste à traiter dans une session d'implémentation

- Écrire la config `codec => multiline` complète (`pattern`, `negate`,
  `what`) sur l'`input` du pipeline `ansible-playbook -v`
- Cas de la toute première ligne du fichier (`PLAY [...]`) : pas de
  buffer précédent à flusher, comportement à vérifier plutôt que
  supposer
- Reste à voir en pratique : comment le résultat recollé se présente
  côté `message`/`event.original` (plusieurs lignes physiques
  concaténées avec quel séparateur par défaut ?)
- Deuxième terrain prévu au programme (README, Palier 3) : stack
  traces Java éclatées sur plusieurs lignes — cas canonique basé sur
  l'absence de timestamp en début de ligne plutôt que sur une
  structure `TASK`/statut

## Lien avec les notes existantes

`10-codecs-structuration-input-output.md` (distinction codec/filtre,
posée au Palier 1, confirmée en pratique ici), `08-grok-conditionnel-
kernel-gestionechec.md` et `tp-parsing-ansible-verbose-resultat.md`
(ordre de sortie non garanti, tags qui s'accumulent — même vigilance
face à des lignes non anticipées au moment de concevoir une règle).
