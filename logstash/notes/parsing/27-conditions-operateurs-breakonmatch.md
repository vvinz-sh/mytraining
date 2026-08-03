# Logstash — Conditions avancées (`=~`, `in`, `!`) et `break_on_match`

Rassage en revue des 4 opérateurs conditionnels avancés du README, déjà partiellement
pratiqués sur le TP `ansible-playbook -v` (`=~`, `and`/`or`, `else
if`), et clarification du fonctionnement de `break_on_match`.

## `==` vs `=~` : deux opérations différentes, pas deux niveaux de tolérance

Deux tests different de nature :
- `==` : égalité de chaîne **littérale**, caractère pour caractère
- `=~` : **matching de regex** — le motif à droite est interprété
  comme une expression régulière, pas comme du texte à comparer

Conséquence concrète : `if [message] == "^TASK \["` ne matcherait
**jamais** une vraie ligne `TASK [Gathering Facts] ***`, puisque ça
chercherait le texte littéral `^TASK \[` (accent circonflexe et
antislash compris), qui n'existe dans aucun vrai log. Seul un message
qui vaudrait *exactement* la chaîne `^TASK \[` matcherait le `==`.

## `in` : test de sous-chaîne sur une string, pas seulement d'appartenance à un tableau

`in` fonctionne sur les tableaux (`"multiline" in [tags]`, usage le
plus courant), mais aussi sur les **chaînes simples** — dans ce cas,
test de sous-chaîne, comme `in` en Python sur une string :
`"TASK" in [message]` est `true` si "TASK" apparaît n'importe où
dans le message, même en plein milieu d'un mot (ex. hypothétique
`MULTITASKING`). D'où l'intérêt de `=~ "^TASK \["` (ancré en début de
ligne) dès que la **position** compte, pas seulement la présence —
`in` ne fait aucune distinction de position.

## `!` : négation d'expression, mais aussi test d'existence à part entière

Deux usages distincts à ne pas confondre :
- `!(expression)` : négation logique d'une expression complète —
  `!([message] =~ "^TASK \[")` équivaut logiquement à
  `[message] !~ "^TASK \["` (l'opérateur dédié). Logstash propose
  `!~`/`not in` pour la lisibilité, pas par nécessité — les deux
  formulations donnent le même résultat.
- `![champ]` (champ seul, sans comparaison) : teste l'**existence**
  du champ (absent ou "falsy"), pas l'inverse d'un booléen — `[tags]`
  n'est pas un booléen en soi, mais `![tags]` est vrai si le champ
  est absent ou vide.

## `break_on_match` : agit à l'intérieur d'un seul bloc `grok`, pas sur le pipeline

Confusion initiale : observer qu'un event continue son chemin dans le pipeline après un `grok` réussi (vers les
filtres suivants) n'a **rien à voir** avec `break_on_match`. Un grok
réussi ne "termine" jamais le traitement de l'event, avec ou sans
cette option — c'est le comportement normal de Logstash.

`break_on_match` agit à une échelle bien plus locale : uniquement
quand un **même bloc `grok`** contient plusieurs patterns candidats
dans son `match` (tableau). Par défaut (`true`), grok teste les
patterns dans l'**ordre d'écriture** et s'arrête au premier qui
matche — même si un pattern plus loin dans la liste aurait aussi
matché, potentiellement avec des champs différents ou plus précis.
Ce n'est jamais "le meilleur pattern gagne", c'est "le premier dans
l'ordre d'écriture gagne". `break_on_match => false` ferait tester
tous les patterns du tableau, quel que soit le résultat des
précédents.


## Lien avec les notes existantes

`tp-parsing-ansible-verbose-resultat.md` (usage pratique de `=~`,
`and`/`or`, `else if` sur le TP ansible-playbook -v — bug de
l'accumulation des tags entre blocs non protégés, distinct de
`break_on_match` mais dans la même famille de vigilance sur l'ordre
d'évaluation), `08-grok-conditionnel-kernel-gestionechec.md`
(premiers filtres conditionnels basiques, Palier 2).

## Sources

- [Accessing event data and fields — Conditionals (Logstash Reference 8.19, Elastic)](https://www.elastic.co/guide/en/logstash/8.19/event-dependent-configuration.html) — liste officielle des opérateurs (`==`/`!=`/`<`/`>`/`<=`/`>=`, `=~`/`!~`, `in`/`not in`, `!`), sémantique de `in` selon le type de champ (sous-chaîne vs appartenance stricte), comportement de `![champ]` (absent, faux, ou null)
- [Grok filter plugin — option `break_on_match` (Logstash Reference 8.19, Elastic)](https://www.elastic.co/guide/en/logstash/8.19/plugins-filters-grok.html) — confirme la valeur par défaut (`true`) et le comportement décrit ci-dessus
