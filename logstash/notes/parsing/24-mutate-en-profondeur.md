# Logstash — Mutate en profondeur : convert, gsub, split, merge, et le plugin bytes

Clôture conceptuellement le Palier 2 — approfondissement de `mutate`
(au-delà du simple `add_field` de la note 03), avec un vrai calcul
en bytes prolongeant la théorie ECS de la note 19.

## Contexte : conversion d'unité prolongeant la note 19

Rappel de la note 19 (ECS) : un `file.size` ECS-compliant attend une
valeur en **bytes**, alors que notre pipeline produisait `backup.size`/
`backup.unit` séparément (ex : `45`/`GB`), sans conversion réelle.
Mise en pratique ici avec le plugin dédié **`logstash-filter-bytes`**
(officiel, mais **non bundlé par défaut** — comme `logstash-output-exec`,
note 23 — installation explicite requise) :

```
sudo -u logstash /usr/share/logstash/bin/logstash-plugin install logstash-filter-bytes
```

```
mutate {
  add_field => { "[backup][size_with_unit]" => "%{[backup][size]}%{[backup][unit]}" }
}
bytes {
  source => "[backup][size_with_unit]"
  target => "[backup][bytes]"
}
mutate {
  remove_field => [ "[backup][size_with_unit]" ]
}
```

**Résultat vérifié** : `45GB` → `48318382080` bytes — calcul confirmé
(`45 × 1024³`, en gibioctets/base 1024, pas en gigaoctets décimaux
base 1000 qui aurait donné `45 000 000 000`). Champ intermédiaire
(`size_with_unit`) nettoyé après usage, ne laisse aucune trace
inutile dans l'event final.

## `convert` : du texte vers un vrai type numérique

Constat de départ : `"size" => "45"` — entre guillemets, une chaîne
de caractères, pas un nombre. Problème identifié : Kibana (Palier 5)
ne pourrait ni trier ni moyenner correctement une valeur stockée
comme texte.

```
mutate {
  convert => { "[backup][size]" => "integer" }
}
```

**Résultat vérifié** : `"size" => 45` sans guillemets — confirmation
visuelle du changement de type réel, pas juste cosmétique.

## Découverte en chemin : GREEDYDATA capture bien le `\n`, malgré des sources anciennes contradictoires

En nettoyant `message_parse` d'un `\n` traînant (issu d'`echo` dans le
plugin `exec`, qui ajoute toujours un saut de ligne final sauf avec
`echo -n`), question soulevée : comment `%{GREEDYDATA:message_parse}`
(défini `.*`) a-t-il pu capturer ce `\n`, alors qu'un `.` en regex ne
matche normalement **pas** un saut de ligne sans le modificateur
`s`/DOTALL ?

Recherche menée : plusieurs fils communautaires anciens (2014-2016)
affirment le contraire (*"Make logstash GREEDYDATA accept newlines"*
— un patch dédié pour forcer ce comportement, suggérant qu'il
n'existait pas par défaut à l'époque). **Contradiction avec notre
propre observation empirique** sur Logstash 8.19 (moteur
Joni/Oniguruma) : le `\n` est bien capturé, sans aucun patch.

**Décision retenue** : faire confiance au test empirique plutôt qu'à
des sources datées et contradictoires entre elles — comportement
peut-être évolué entre versions, ou différence d'implémentation
Oniguruma vs PCRE historique. Comportement vérifié directement sur
notre propre instance, pas déduit d'une doc ambiguë.

**Nettoyage via `gsub`** :

```
mutate {
  gsub => [ "message_parse", "\n", "" ]
}
```

## `split` : d'une chaîne à un vrai tableau

Cas de test enrichi avec une ligne réaliste :
```
Jul 21 08:15:33 rh8102 backup-job[1234]: Writing archive... 45GB written - Including: /etc,/home,/var
```

Extraction du texte via Grok, avec un choix de pattern justifié
(prolonge la leçon `DATA`/`GREEDYDATA` de la note 05) :
```
match => { "message_parse" => "%{DATA} Including: %{GREEDYDATA:[backup][directories]}" }
```
`DATA` pour "sauter" le texte avant `Including:` (une seule
occurrence dans la ligne, donc `DATA` s'arrête dès la première —
et seule — correspondance possible, comportement plus prévisible que
`GREEDYDATA` qui reculerait depuis la fin). `GREEDYDATA` conservé
pour la capture finale, rien après elle jusqu'à la fin de ligne, donc
aucun risque de backtrack malvenu.

```
mutate {
  split => { "[backup][directories]" => "," }
}
```

**Résultat** : `"/etc,/home,/var"` (chaîne) devient
`["/etc", "/home", "/var"]` (tableau) — chaque élément individuellement
exploitable (compter, filtrer un dossier précis dans Kibana).

## `merge` : pourquoi pas juste `%{...}` sur deux tableaux

Tentative initiale (naïve, volontairement testée pour voir l'échec) :
combiner deux tableaux (`directories` et un nouveau `excluded`) via
`add_field` + interpolation `%{...}` :
```
mutate {
  add_field => { "[backup][all_dirs]" => "%{[backup][directories]}%{[backup][excluded]}" }
}
```

**Résultat révélateur de bug** : `"/etc,/home,/var/sys,/dev"` — le
dernier élément de `directories` (`/var`) et le premier de `excluded`
(`/sys`) se **collent sans séparateur**, donnant l'illusion trompeuse
d'un seul chemin `/var/sys`. La virgule Ruby n'apparaît qu'**à
l'intérieur** de chaque tableau lors de sa représentation textuelle,
jamais **entre** deux champs distincts interpolés côte à côte.

**Solution propre, `merge`** :
```
mutate {
  merge => { "[backup][directories]" => "[backup][excluded]" }
}
```

**Résultat vérifié** : `directories` contient directement les 5
éléments distincts (`/etc`, `/home`, `/var`, `/sys`, `/dev`) — aucun
collage, chaque chemin individuellement préservé.

## Résumé

1. Le plugin `bytes` (non bundlé) convertit une taille lisible
   (`45GB`) en valeur numérique réelle — met en pratique la
   coexistence champ custom/champ ECS-compliant théorisée en note 19
2. `convert` change le **type** réel d'un champ, pas juste son
   apparence — visible à la disparition des guillemets en sortie
3. Un comportement observé empiriquement (GREEDYDATA capturant `\n`)
   peut contredire des sources communautaires anciennes — faire
   confiance au test direct plutôt qu'à une doc datée et ambiguë
4. `split` transforme une chaîne délimitée en tableau exploitable
   élément par élément
5. `merge` combine deux tableaux en préservant chaque élément
   distinctement — `%{...}` sur des tableaux entiers colle les
   représentations textuelles sans séparateur entre les champs,
   créant des valeurs trompeuses

## Lien avec les notes existantes

`19-panorama-ecs.md` (théorie `file.size` en bytes, mise en pratique
ici), `05-grok-filtre-conditionnel-greedydata-data.md` (leçon
`DATA`/`GREEDYDATA` réappliquée pour `Including:`), `23-plugin-exec.md`
(`echo` et son `\n` final, origine du bug nettoyé via `gsub`),
`03-premier-pipeline-stdin-stdout-filter-mutate.md` (premier usage
de `mutate`, `add_field` seul).

## Sources

- [logstash-filter-bytes (GitHub, officiel)](https://github.com/logstash-plugins/logstash-filter-bytes)
- [Bytes filter plugin (Elastic Docs)](https://www.elastic.co/guide/en/logstash/current/plugins-filters-bytes.html)
- [Mutate filter plugin (Elastic Docs)](https://www.elastic.co/guide/en/logstash/current/plugins-filters-mutate.html)
- [GREEDYDATA and newlines (Elastic Discuss, 2016)](https://discuss.elastic.co/t/greedydata-and-newlines/45268)
