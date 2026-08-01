# Logstash — Options CLI de confort (complément Palier 0)

Complète `01-panorama-alternatives-interfacage-securite.md` — options
en ligne de commande découvertes en cours de route, utiles au
quotidien plutôt que spécifiques à un palier de contenu précis.

## Rechargement automatique du pipeline

`--config.reload.automatic` (ou `-r`) : Logstash vérifie les
changements du `.conf` toutes les 3 secondes par défaut
(`--config.reload.interval <Ns>` pour ajuster). Quand un changement
est détecté, l'ancien pipeline est arrêté (inputs stoppés), un nouveau
est construit et validé, puis substitué à l'ancien — **sans redémarrer
la JVM**. C'est précisément le coût qu'on cherche à éviter (le
démarrage de la JVM est le vrai point lent, pas le pipeline
lui-même).

Limite: le plugin `logstash-input-stdin` est explicitement
marqué "non reloadable" dans son propre changelog — il maintient un
flux persistant (le clavier) qui ne peut pas être proprement démonté.

Limite : incompatible avec le flag `-e` (config passée en ligne de
commande plutôt que par fichier). Si Logstash tourne déjà sans ce
flag, un rechargement forcé reste possible via signal :
```bash
kill -SIGHUP <PID>
```

## Vérification de syntaxe sans exécution

`-t` / `--config.test_and_exit` : valide la syntaxe du `.conf` et
quitte immédiatement, sans démarrer un vrai pipeline. Point de
vigilance : **les patterns Grok ne sont pas vérifiés pour leur
correction** par ce flag — seule la structure globale (accolades,
syntaxe des blocs) est contrôlée, pas la logique interne d'un pattern.

## Test rapide sans fichier

`-e "CONFIGSTRING"` : passe directement une config en argument, sans
créer de fichier `.conf` — pratique pour un essai ponctuel très
rapide. Contrepartie : pas de rechargement automatique possible avec
ce mode.

## Niveau de verbosité

`--log.level` : `info` par défaut ; `debug`/`trace` pour creuser un
problème en profondeur, `warn`/`error` pour réduire le bruit.

## Debug de configuration — avec un vrai risque de sécurité

`--config.debug` (nécessite aussi `--log.level=debug`) : affiche la
configuration complète telle qu'interprétée par Logstash, utile pour
vérifier qu'un pattern a été compris comme prévu.

⚠️ **Avertissement officiel** : ce mode peut faire apparaître des mots
de passe en clair dans les logs si la config en contient (identifiants
de connexion à une base de données en sortie, par exemple) — à ne pas
laisser actif en dehors d'un contexte de debug ponctuel et maîtrisé,
cohérent avec la vigilance déjà posée sur la sécurité de l'outil
(note 01).

## Résumé

1. `--config.reload.automatic` évite de relancer toute la JVM à
   chaque modification de `.conf` — le vrai gain de confort recherché
2. `-t` vérifie la syntaxe mais pas la validité des patterns Grok —
   un fichier "valide" selon ce flag peut quand même échouer à
   l'exécution
3. `--config.debug` est puissant pour déboguer, mais expose
   potentiellement des secrets en clair dans les logs

## Sources

- [Running Logstash from the Command Line (Elastic, 8.19)](https://www.elastic.co/guide/en/logstash/8.19/running-logstash-command-line.html)
- [Reloading the Config File (Elastic, 8.19)](https://www.elastic.co/guide/en/logstash/8.19/reloading-config.html)
- [How to Auto-Reload Logstash Configuration (Better Stack)](https://betterstack.com/community/questions/how-to-auto-reload-logstash-configuration/)
