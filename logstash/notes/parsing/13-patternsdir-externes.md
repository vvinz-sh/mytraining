# Logstash — patterns_dir : externaliser des patterns Grok personnalisés

Clôture le Palier 1 — dernier trou identifié, prolonge directement
la note 11 (architecture des plugins) et la note 04 (pattern de base
`SYSLOGBASE` maison, jusqu'ici codé en dur).

Enrichie en Palier 3 (renforcement théorique) avec 3 points non
couverts à l'origine : dossiers multiples, composabilité entre
patterns personnalisés, nuance sur le rechargement à chaud.

## Pourquoi externaliser un pattern

Chaque pattern écrit depuis le Palier 2 était resté codé directement
dans le `.conf` (`SYSLOGBASE` maison, patterns `java-app`/
`backup-job`/`kernel`). Sur un pipeline qui grossit, ça nuit à la
maintenabilité — un même pattern potentiellement dupliqué entre
plusieurs `.conf`, ou difficile à faire évoluer proprement.

## Fichier de patterns personnalisé

Même syntaxe que le fichier officiel `grok-patterns` déjà lu plusieurs
fois (`NOM_DU_PATTERN definition_regex`), dans un fichier texte séparé
sans extension particulière :

`/etc/logstash/patterns/mes_patterns` :
```
SYSLOGBASE_PERSO %{SYSLOGTIMESTAMP:timestamp} %{HOSTNAME:hostname} %{PROG:processus}(?:\[%{POSINT}\])?: %{GREEDYDATA:message_parse}
```

Nom volontairement distinct de `SYSLOGBASE` officiel (`_PERSO`) pour
éviter toute collision avec le nom déjà défini dans les patterns
prédéfinis de Logstash.

## Paramètre `patterns_dir` : un dossier, pas un fichier

Piège de nommage repéré avant de se tromper : `patterns_dir` ("dir"
pour directory) attend le chemin vers le **dossier** contenant le
fichier de patterns, pas le fichier lui-même directement.

```
filter {
  grok {
    patterns_dir => "/etc/logstash/patterns/"
    match => { "message" => "%{SYSLOGBASE_PERSO}" }
  }
  if [processus] == "kernel" {
    grok {
      match => { "message_parse" => "%{DATA:[fs][format]} %{LOGLEVEL:[fs][level]}: %{GREEDYDATA:details}" }
    }
  }
}
```

`patterns_dir` accepte aussi un **tableau de plusieurs dossiers**,
pas seulement un chemin unique :
```
patterns_dir => ["/etc/logstash/patterns", "/etc/logstash/patterns-equipe-x"]
```
Utile pour organiser des patterns par module/équipe plutôt que dans
un seul dossier fourre-tout — tous les dossiers listés sont scannés
au chargement du pipeline, sans priorité particulière entre eux.

## Composabilité : un pattern personnalisé peut en référencer un autre

`%{SYSLOGBASE_PERSO}` (ci-dessus) n'est pas un bloc monolithique —
c'est déjà, en soi, une composition de patterns officiels imbriqués
(`%{SYSLOGTIMESTAMP}`, qui compose lui-même d'autres patterns de plus
bas niveau, etc.). Le même principe fonctionne pour un pattern
personnalisé qui en référence un **autre** pattern personnalisé du
même fichier — pas seulement des patterns officiels. Confirmé en
pratique lors de l'exercice de la note : `SYSLOGBASE_PERSO` appelle
`SYSLOGTIMESTAMP`, qui appelle lui-même d'autres patterns de base —
la composition se fait exactement comme avec les patterns officiels,
sans distinction de statut "personnalisé" vs "officiel" au moment de
la résolution.

## Rechargement : plus subtil qu'un simple "redémarrage nécessaire"

Hypothèse de départ : modifier le fichier de patterns une fois
Logstash démarré nécessiterait un redémarrage du pipeline. Confirmé
par la doc officielle, mais avec une nuance importante : Logstash **ne
surveille pas** le fichier de patterns lui-même, seulement le(s)
fichier(s) `.conf`. Avec `config.reload.automatic` activé :
- Modifier **seulement** le fichier de patterns → **rien ne se
  passe**, le changement n'est jamais détecté, même avec le
  rechargement automatique actif
- Modifier le `.conf` (même un changement trivial, un commentaire par
  exemple) → déclenche un rechargement complet du pipeline, qui **relit
  aussi** le fichier de patterns au passage — donc les deux fichiers
  se retrouvent synchronisés, mais uniquement parce que le `.conf` a
  bougé, pas le fichier de patterns en lui-même

Sans `config.reload.automatic`, un signal `SIGHUP` ou un redémarrage
manuel du process a le même effet (recréation du pipeline, patterns
relus). Le renseignement pratique à retenir : après une modification
du fichier de patterns, forcer une prise en compte en touchant aussi
le `.conf` (ou en envoyant un `SIGHUP`), plutôt que de supposer que
`config.reload.automatic` seul suffira.

## Piège méthodologique évité : valider via un pipeline systemd n'a rien prouvé

Premier test lancé via `pipelines.yml`/systemd : le pipeline démarre
sans erreur de parsing (confirme que `patterns_dir` est trouvé et
`SYSLOGBASE_PERSO` syntaxiquement compris), mais se termine
immédiatement — exactement le bug 4 déjà documenté en note 12
(`stdin` sous systemd = `/dev/null` = EOF immédiat). **Aucune ligne
réelle n'a traversé le pipeline** — ce test valide la config, pas le
comportement du pattern.

**Vérification correcte** : relancer manuellement en avant-plan
(`-f`), là où `stdin` reste un vrai flux clavier interactif.

## Résultat validé

Sur la ligne `kernel` déjà utilisée en note 08 :
```
Jul 21 08:22:10 rh8102 kernel: EXT4-fs warning: /var running low on free space (2% remaining)
```

Résultat identique à la version avec pattern codé en dur : `timestamp`,
`hostname`, `processus`, `fs.format`, `fs.level`, `details` tous
correctement extraits via `%{SYSLOGBASE_PERSO}` externalisé — aucune
régression, gain de maintenabilité confirmé sans perte de
fonctionnalité.

## Résumé

1. Un pattern personnalisé s'externalise dans un fichier texte séparé,
   même syntaxe que les patterns officiels (`NOM definition`)
2. `patterns_dir` attend un **dossier**, pas un fichier — piège de
   nommage à connaître ; accepte aussi un tableau de plusieurs
   dossiers
3. Un nom personnalisé doit éviter toute collision avec un pattern
   officiel déjà défini (`SYSLOGBASE_PERSO` plutôt que `SYSLOGBASE`)
4. Un pattern personnalisé peut en référencer un autre pattern
   personnalisé du même fichier — composabilité identique aux
   patterns officiels, sans distinction de statut
5. Valider une config via un pipeline systemd (`stdin` + EOF immédiat)
   ne prouve que la validité syntaxique, pas le comportement réel du
   pattern — la vérification fonctionnelle nécessite un vrai test
   interactif en avant-plan
6. Modifier le fichier de patterns seul ne déclenche **jamais** de
   rechargement, même avec `config.reload.automatic` actif — Logstash
   ne surveille que le(s) fichier(s) `.conf`. Forcer la prise en
   compte via une modification du `.conf` (même triviale) ou un
   `SIGHUP`/redémarrage

## Lien avec les notes existantes

`04-construction-premier-pattern-grok.md` (pattern `SYSLOGBASE` maison
d'origine, ici externalisé), `08-grok-conditionnel-kernel-gestionechec.md`
(ligne de test réutilisée), `11-architecture-plugins.md` (patterns
comme brique de l'écosystème plugin), `12-pipelines-config.md` (bug 4
`stdin`/systemd, réutilisé ici pour expliquer le faux positif de
validation).

## Sources

- [Reloading the Config File (Logstash Reference 8.19, Elastic)](https://www.elastic.co/guide/en/logstash/8.19/reloading-config.html) — confirme que les fichiers de patterns Grok ne sont relus que lorsqu'un changement du fichier `.conf` déclenche lui-même un rechargement (ou redémarrage du pipeline), pas sur une modification directe du fichier de patterns
