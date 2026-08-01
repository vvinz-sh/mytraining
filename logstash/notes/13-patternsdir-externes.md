# Logstash — patterns_dir : externaliser des patterns Grok personnalisés

Clôture le Palier 1 — dernier trou identifié, prolonge directement
la note 11 (architecture des plugins) et la note 04 (pattern de base
`SYSLOGBASE` maison, jusqu'ici codé en dur).

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
   nommage à connaître
3. Un nom personnalisé doit éviter toute collision avec un pattern
   officiel déjà défini (`SYSLOGBASE_PERSO` plutôt que `SYSLOGBASE`)
4. Valider une config via un pipeline systemd (`stdin` + EOF immédiat)
   ne prouve que la validité syntaxique, pas le comportement réel du
   pattern — la vérification fonctionnelle nécessite un vrai test
   interactif en avant-plan

## Lien avec les notes existantes

`04-construction-premier-pattern-grok.md` (pattern `SYSLOGBASE` maison
d'origine, ici externalisé), `08-grok-conditionnel-kernel-gestionechec.md`
(ligne de test réutilisée), `11-architecture-plugins.md` (patterns
comme brique de l'écosystème plugin), `12-pipelines-config.md` (bug 4
`stdin`/systemd, réutilisé ici pour expliquer le faux positif de
validation).
