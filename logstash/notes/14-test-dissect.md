# Logstash — Dissect en pratique, un premier cas réel

Complète la théorie posée en note 04/12 (dissect écarté pour le
préfixe syslog générique, à cause du PID optionnel) — clôt le point
en attente depuis le début du Palier 2, avec un vrai cas d'usage où
`dissect` convient.

## Choix du cas de test : `cron`, pas le préfixe syslog générique

Rappel du critère théorique : `dissect` convient à un contenu
**structurellement régulier**, sans champ optionnel qui varierait
d'une ligne à l'autre — contrairement au préfixe syslog (PID absent
sur `kernel`). Parmi les types déjà traités, `cron` s'est confirmé
comme le meilleur candidat pour un premier test : structure fixe,
aucune variation observée.

```
Jul 21 08:30:1 rh8102 cron[2001]: (root) CMD (run-parts /etc/cron.hourly)
```

## Syntaxe `%{+champ}` : fusionner plusieurs captures dans un seul champ

Piège identifié avant même d'écrire le pattern : le timestamp
(`Jul 21 08:30:1`) contient deux espaces internes. Un découpage naïf
sur chaque espace fragmenterait le timestamp en trois champs séparés.

Trouvé dans un exemple officiel quasi identique à notre cas :
```
%{ts} %{+ts} %{+ts} %{src} %{} %{prog}[%{pid}]: %{msg}
```

Le préfixe `+` (`%{+ts}`) indique à `dissect` d'**ajouter** cette
capture au champ déjà commencé du même nom, plutôt que d'en créer un
nouveau — les trois occurrences fusionnent en un seul champ contenant
"mois jour heure". `%{}` (vide) capture une portion de texte sans lui
donner de nom, pour l'ignorer délibérément — absent de notre propre
pattern, car aucune donnée superflue n'existe à cet endroit dans nos
lignes.

## Pattern final et test

```
filter {
  dissect {
    mapping => { "message" => "%{timestamp} %{+timestamp} %{+timestamp} %{hostname} %{prog}[%{pid}]: %{msg}" }
  }
}
```

Résultat sur la ligne `cron` : `timestamp`, `hostname`, `prog`, `pid`,
`msg` tous correctement extraits — sans une seule ligne de regex.

## Confirmation de la limite déjà anticipée en théorie

Question posée avant de conclure : que se passerait-il si ce même
pattern était appliqué à une ligne `kernel` (sans PID) ? Réponse
construite sans même avoir besoin de tester : `dissect` n'a pas
d'équivalent au groupe optionnel `(?:...)?` de Grok — la ligne
échouerait net, l'irrégularité (PID absent) n'étant pas gérable par
un découpage à position fixe.

Confirmé par la doc officielle : *"Dissect works well when data is
reliably repeated"*, et le hybride reste la bonne approche pour un
fichier hétérogène : *"You can use both Dissect and Grok for a hybrid
use case when a section of the line is reliably repeated, but the
entire line is not."*

## Piste ouverte : mesurer objectivement dissect vs grok

Question posée : comment vérifier concrètement le gain de performance
annoncé (jusqu'à 5x, note 04), plutôt que de se fier à une statistique
générique ? Découverte : l'API de monitoring intégrée (port 9600, déjà
visible dans les logs de démarrage depuis le Palier 1) expose des
statistiques par plugin, dont `duration_in_millis` :

```bash
curl -s 'http://localhost:9600/_node/stats/pipelines?filter_path=pipelines.main.plugins.filters&pretty'
```

Un test réel sur un seul event a donné `duration_in_millis: 72` pour 1
event traité — chiffre non significatif isolément (inclut le
démarrage à froid du pipeline, pas seulement le temps de traitement).
Une vraie comparaison chiffrée nécessiterait plusieurs centaines de
répétitions de la même ligne, et une mesure équivalente sur un
pipeline `grok` pour comparer objectivement. **Reporté** : l'API de
monitoring mérite sa propre note dédiée, probablement au Palier 4
(observabilité d'un pipeline en fonctionnement), plutôt qu'une
mention noyée ici.

## Résumé

1. `dissect` convient aux structures **régulières sans variation** —
   confirmé en pratique sur `cron`, écarté à raison pour le préfixe
   syslog générique (PID optionnel)
2. `%{+champ}` fusionne plusieurs captures consécutives dans un seul
   champ nommé, `%{}` ignore une portion de texte sans la nommer
3. L'API de monitoring (port 9600, `_node/stats/pipelines`) expose
   `duration_in_millis` par plugin — outil à creuser plus tard pour
   des comparaisons de performance objectives, pas juste des
   statistiques génériques trouvées en ligne

## Lien avec les notes existantes

`04-construction-premier-pattern-grok.md` (dissect écarté en théorie
pour le préfixe syslog), `08-grok-conditionnel-kernel-gestionechec.md`
(cas `kernel`, PID optionnel, référence de la limite confirmée ici).

## Sources

- [Dissect filter plugin (Elastic, 8.19)](https://www.elastic.co/docs/reference/logstash/plugins/plugins-filters-dissect)
- [Node Stats API (Elastic, 8.19)](https://www.elastic.co/guide/en/logstash/8.19/node-stats-api.html)
- [Monitoring Logstash Filters (Elastic Blog)](https://www.elastic.co/blog/monitoring-logstash-filters)
