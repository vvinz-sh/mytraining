# Logstash — Sorties multiples : duplication vs routage

Premier des 2 points théoriques du Palier 4 (renforcement avant
d'attaquer les TP pratiques). Déjà pratiqué sans le nommer sur les
TP ansible (`ok_logs`/`failed_logs`) — cette note nomme et complète
ce qu'on faisait déjà, plus un usage jamais utilisé jusqu'ici
(duplication sans condition).

## Deux usages distincts sous le même terme

"Sorties multiples" recouvre en réalité deux mécanismes différents,
faciles à confondre au premier abord :

**1. Duplication** — plusieurs plugins dans un même bloc `output`,
**sans condition** :
```
output {
  stdout {}
  file { path => "/chemin/archive.log" }
}
```
Chaque plugin reçoit **chaque event**, indépendamment des autres —
pas de logique "le premier qui correspond gagne" comme
`break_on_match` sur grok (note 27). Littéralement tout le monde
reçoit tout. Cas d'usage typique : envoyer le même event vers
`elasticsearch` **et** `file` en parallèle (indexation + archivage
brut), pas pour trier quoi que ce soit.

**2. Routage** — avec `if`/`else if`, comme pratiqué sur les TP
ansible (`if "_grokparsefailure" in [tags] { file {...} } else {
file {...} }`). Un event ne part que dans **une seule** branche,
exclusive.

Les deux se combinent dans un même bloc sans problème : un
`stdout {}` sans condition (debug systématique) à côté d'un
`if`/`else` conditionnel (routage réel) — rien n'oblige à choisir
l'un des deux mécanismes pour tout le bloc `output`.

## Détail de performance : un pool de workers par plugin

Chaque plugin de sortie tourne avec son **propre pool de workers**,
indépendamment des autres. Conséquence concrète : un plugin lent
(`email`, attente SMTP ; `http`, latence réseau) ne bloque pas un
plugin rapide (`file`) à côté, même si les deux reçoivent le même
event simultanément en mode duplication.

## Panorama des plugins output (les familles principales)

La doc officielle en liste une soixantaine, l'essentiel se regroupe
en quelques familles :

- **Stockage/recherche** : `elasticsearch` (de loin le plus utilisé,
  la destination "native" du produit), `s3`, `csv`, `file`
- **Bus de messages / files d'attente** : `kafka`, `rabbitmq`,
  `redis`, `sqs` — utile pour découpler Logstash d'un système en aval
  trop lent ou instable
- **Génériques** : `http`, `tcp`, `udp`, `exec` (lance une commande),
  `pipe` (vers le stdin d'un autre programme)
- **Alerting/notification** : `email`, `pagerduty`, `nagios`
- **Debug/dev** : `stdout`, `file` — ceux utilisés depuis le tout
  début du module
- **Chaînage Logstash → Logstash** : le plugin `logstash` (output)
  vers un autre `logstash` (input) — pertinent si un jour le
  traitement se segmente en plusieurs instances
- **`sink`** — plugin qui **jette** l'event volontairement, sans rien
  écrire nulle part ; utile pour tester une branche de routage sans
  polluer un vrai fichier de sortie

## Résumé

1. "Sorties multiples" = deux mécanismes distincts : duplication
   (sans condition, tout le monde reçoit tout) et routage (avec
   `if`/`else if`, exclusif)
2. Déjà pratiqué en routage sur les TP ansible sans le nommer —
   nouveau ici : la duplication, jamais utilisée jusqu'à présent
3. Les deux mécanismes se combinent librement dans un même bloc
   `output`
4. Chaque plugin de sortie a son propre pool de workers — un plugin
   lent ne ralentit pas les autres

## Lien avec les notes existantes

`tp-parsing-ansible-verbose-resultat.md` (routage `ok_logs`/
`failed_logs`, premier usage pratique sans le nommer),
`27-conditions-operateurs-breakonmatch.md` (`break_on_match` — "le
premier qui matche gagne", contraste avec la duplication où tout le
monde reçoit tout).

## Sources

- [Output plugins (Logstash Reference 8.19, Elastic)](https://www.elastic.co/guide/en/logstash/8.19/output-plugins.html) — liste complète des plugins de sortie disponibles
