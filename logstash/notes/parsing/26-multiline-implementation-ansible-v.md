# Logstash — Codec `multiline` : implémentation pratique (ansible-playbook -v)

Suite de la note 25 (fonctionnement conceptuel). Implémentation
effective sur `deployer_filebeat.log`, avec plusieurs détours
imprévus qui en disent plus long que le résultat final lui-même.

Travail en cours — le résultat complet (3 branches `if`/`else if`
adaptées au multiligne) n'est pas encore terminé, cette note fige ce
qui a été établi jusqu'ici.

## `auto_flush_interval` : flush périodique, pas un délai par ligne

Question posée avant d'ajouter l'option : est-ce que
`auto_flush_interval => 1` ralentit le traitement de 1 seconde par
ligne, ou par event ?

Réponse : ni l'un ni l'autre. C'est un
**timer périodique en arrière-plan** qui vérifie si un buffer est
resté inactif plus longtemps que l'intervalle configuré. Les lignes
qui matchent le pattern déclencheur continuent de flusher
immédiatement, sans latence — seul le tout dernier buffer (celui
sans ligne suivante pour le clore) attend le prochain passage du
timer, donc au maximum ~1s de latence, une seule fois, en toute fin
de traitement.

Test empirique sur plusieurs runs avec/sans l'option : durée totale
entre 20 et 25 secondes dans les deux cas, sans corrélation nette
avec la présence du timeout. Conclusion retenue avec la réserve
appropriée : sur seulement 7 events, l'écart de durée est
probablement dominé par d'autres facteurs (démarrage JVM, chargement
des plugins) — un test à plus grand volume serait plus tranchant
pour vraiment isoler l'effet du timeout.

## Résultat après correction : les 7 events attendus

Avec le pattern corrigé + `auto_flush_interval => 1` : 7 events en
sortie (les 5 déjà connus + `TASK [Activer et démarrer...]` avec son
JSON systemd de ~6900 caractères + `PLAY RECAP` fusionné avec sa
ligne de récap, flushé par le timeout faute de ligne suivante).
Confirmé par calcul programmatique (comptage des events, pas
lecture visuelle). Le premier event (`PLAY [...]`) reste toujours
sans tag `multiline` — cohérent avec le bug documenté en note 25
(les lignes vides continuent de disparaître silencieusement, même
une fois le pattern corrigé).

## Correction empirique sur `GREEDYDATA` face à un `\n`

Hypothèse de départ : `.`/`GREEDYDATA` ne
traverse pas un `\n` par défaut, donc un grok à une seule ligne
s'arrêterait avant la ligne de statut sur un message fusionné.

**Hypothèse fausse, corrigée par un test direct** : en nommant le
`GREEDYDATA` final (`reste`) sur le grok `TASK [...] \*%{GREEDYDATA}`
appliqué à un message fusionné sur 2 lignes, le contenu de `reste`
contenait bien la ligne `changed: [...] => {...}` en entier, `\n`
compris. `GREEDYDATA` traverse donc le saut de ligne sans problème —
il n'y a aucune ancre de fin (`$`) dans le pattern, donc rien ne
l'empêche de continuer jusqu'au bout du message, `\n` inclus.

Conséquence utile : rien n'empêche d'écrire **un seul grok** qui
capture nom de task et statut en même temps, en insérant un `\n`
littéral dans le pattern entre les deux parties :
```
%{WORD:[ansible][type]} \[%{DATA:[ansible][name]}\] \*+\n%{WORD:[ansible][state]}: \[%{HOSTNAME:[ansible][target]}\]%{GREEDYDATA}
```
Testé partiellement : ce pattern échoue proprement
(`_grokparsefailure`, sans autre effet de bord) sur `PLAY [...]`
(pas de ligne de statut derrière) et sur `PLAY RECAP` (structure
différente) — comportement attendu, pas gênant en soi, mais qui
oblige à revoir les conditions de routage.

## Redécoupage des branches nécessaire

Avant multiline : 3 familles de lignes, un pattern par famille,
`TASK` et `PLAY` regroupés dans la même condition (même en-tête
`MOT [texte] ***`). Après multiline, ce regroupement ne tient plus :
- `PLAY [...]` reste seul (pas de ligne de statut associée)
- `TASK [...]` est maintenant fusionné avec sa ligne de statut — le
  nouveau pattern à 2 lignes s'applique **seulement** à lui, pas à
  `PLAY`
- `PLAY RECAP` reste fusionné avec sa ligne de récap, structure
  toujours différente des deux autres

`TASK` et `PLAY`, qui partageaient une condition commune avant
multiline, doivent maintenant être **dégroupés** : la condition de
routage reste la même sur le principe (`^TASK \[` vs `^PLAY \[`
séparément), mais chacune applique un grok différent puisque leur
contenu a évolué différemment avec la fusion multiligne.

## Reste à faire

- Écrire et tester les 3 branches complètes (`PLAY` inchangé, `TASK`
  avec le pattern à 2 lignes, `PLAY RECAP` avec la condition resserrée
  sur l'en-tête et le grok d'extraction vérifié sur le message
  désormais multiligne)
- Vérifier si le grok d'extraction du récap (`%{HOSTNAME}%{SPACE}: ...`,
  sans ancrage `^`) continue de fonctionner correctement sur un
  message qui commence maintenant par la ligne `PLAY RECAP ****...`
  avant le hostname, ou s'il a besoin d'un `\n` littéral comme celui
  du grok `TASK`
- Repasser sur `tp-parsing-ansible-verbose-resultat.md` une fois le
  pipeline final stabilisé, pour noter l'évolution du scope (2 lignes
  fusionnées au lieu de 2 events séparés)

## Lien avec les notes existantes

`25-multiline-codec-concept.md` (fonctionnement du buffer, `negate`,
piège des lignes vides — confirmé de nouveau ici en pratique),
`tp-parsing-ansible-verbose-resultat.md` (grok `TASK`/`PLAY`
d'origine, à réviser).
