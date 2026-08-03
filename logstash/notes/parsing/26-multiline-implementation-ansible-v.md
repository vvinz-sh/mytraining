# Logstash — Codec `multiline` : implémentation pratique (ansible-playbook -v)

Suite de la note 25 (fonctionnement conceptuel). Implémentation
effective sur `deployer_filebeat.log`, avec plusieurs détours
imprévus qui en disent plus long que le résultat final lui-même.

Implémentation terminée : les 3 branches sont écrites et testées
(voir `tp-parsing-ansible-verbose-resultat.md`, section "Extension
hors scope initial : recollage via `multiline`"), pipeline final
dans `multiline-ansible-v.conf`.

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

## Redécoupage des branches

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
multiline, ont donc été **dégroupés** : la condition de routage reste
la même sur le principe (`^TASK \[` vs `^PLAY \[` séparément), mais
chacune applique un grok différent puisque leur contenu a évolué
différemment avec la fusion multiligne.

## Bug `kv`/`target` : `kv` remplace le hash visé au lieu d'y fusionner

Une fois les 3 branches écrites et testées, `ansible.target`
disparaissait spécifiquement sur l'event récap (jamais sur les
`TASK`) — sans aucun tag `_grokparsefailure`, donc sans signal
d'erreur visible. Cause isolée en renommant temporairement le champ
hostname sous `ansible2` (le grok fonctionnait très bien, la
disparition venait d'ailleurs) : le filtre `kv`, configuré avec
`target => "[ansible]"`, **remplace entièrement** le hash `[ansible]`
déjà peuplé par le grok précédent (qui y avait mis `target`), au lieu
de fusionner ses 7 compteurs dedans — comportement documenté et
signalé à plusieurs reprises côté `logstash-filter-kv` au fil de ses
versions.

Deux corrections possibles :
1. Rejouer le grok du hostname *après* `kv` — fonctionne, mais
   duplique le pattern
2. Faire pointer `kv` vers un sous-chemin dédié
   (`target => "[ansible][counters]"`) qui n'entre jamais en
   collision avec `target` — retenue comme solution finale, un seul
   grok, mais les compteurs vivent désormais sous `ansible.counters.*`
   plutôt que directement sous `ansible.*`

## Lien avec les notes existantes

`25-multiline-codec-concept.md` (fonctionnement du buffer, `negate`,
piège des lignes vides — confirmé de nouveau ici en pratique),
`tp-parsing-ansible-verbose-resultat.md` (grok `TASK`/`PLAY`
d'origine, révisé — voir section extension multiline).
