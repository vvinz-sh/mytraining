# Logstash — Palier 2 : construction d'un pattern Grok (SYSLOGBASE fait main)

Palier 2 du module Logstash — premier pattern Grok construit
manuellement, brique par brique, pour parser le préfixe fixe d'un log
syslog hétérogène (`tp-ansible-agent`, log disque plein).

## Dissect vs Grok : pourquoi Grok était nécessaire ici

Hypothèse initiale : `dissect` (séparateurs fixes, plus léger) pour
tout le fichier. Invalidée en observant la vraie hétérogénéité des
lignes du log :

```
Jul 21 08:23:04 rh8102 systemd[1]: backup-job.service: Failed with result 'exit-code'.
Jul 21 08:25:00 rh8102 kernel: EXT4-fs error: /var: filesystem full
Jul 21 08:30:1 rh8102 cron[2001]: (root) CMD (run-parts /etc/cron.hourly)
```

`kernel` n'a **pas de PID** entre crochets, contrairement à `systemd`
et `cron` — `dissect`, qui attend une position fixe pour chaque
séparateur, échoue net sur ce genre de variation ; `grok`, via une
regex, peut exprimer l'optionnalité. Confirmé par la doc officielle
(`SYSLOGPROG`, dans `logstash-patterns-core`) qui gère exactement ce
même cas.

Chiffres trouvés en parallèle : remplacer un filtre grok par dissect
sur des logs structurés peut améliorer la vitesse de traitement
jusqu'à 5x — un gain réel mais qui ne concernerait ici que la petite
partie fixe du préfixe. Décision : grok seul pour ce premier
exercice (pas de besoin de perf en lab), combo dissect+grok à
envisager plus tard si un vrai besoin de débit se présente.

## Construction du pattern, étape par étape

Départ : les briques identifiées séparément (`SYSLOGTIMESTAMP`,
`HOSTNAME`, `WORD`, `POSINT`, `GREEDYDATA`).

**Erreurs successives corrigées en cours de construction** :
1. Nom de processus codé en dur (`systemd[1]`) au lieu d'un pattern
   générique (`WORD`)
2. Parenthèse ouvrante manquante pour le groupe optionnel (`?:` seul
   au lieu de `(?:...)?`)
3. Crochets littéraux non échappés (`[`/`]` ont un sens spécial en
   regex — il faut `\[`/`\]` pour les matcher tels quels)
4. Patterns Grok utilisés sans les `%{}` (`WORD` au lieu de `%{WORD}`)
5. **Portée du groupe optionnel trop large** : `(?:%{WORD}\[%{POSINT}\])?`
   englobait le nom du processus lui-même — sur une ligne sans PID
   (`kernel`), tout le groupe (donc aussi le nom du processus)
   devenait absent, et `kernel` se retrouvait avalé par
   `GREEDYDATA` au lieu d'être capturé. Corrigé en sortant `%{WORD:processus}`
   du groupe optionnel : seul `(?:\[%{POSINT}\])?` (les crochets et
   le PID) reste conditionnel.

## Pattern final

```
%{SYSLOGTIMESTAMP:timestamp} %{HOSTNAME:hostname} %{WORD:processus}(?:\[%{POSINT}\])?: %{GREEDYDATA:message_parse}
```

## Conflit de nommage découvert au test

Premier essai avec `%{GREEDYDATA:message}` (au lieu de `message_parse`) :
le champ `message` existait déjà (créé par l'`input`, avant même le
filtre Grok). Écrire une nouvelle valeur dans un champ déjà existant
ne l'écrase pas silencieusement — Logstash **transforme le champ en
tableau** pour conserver les deux valeurs (`[0]` = ancien message
brut, `[1]` = nouvelle capture).

Deux corrections possibles envisagées :
- Nettoyer le tableau après coup (retirer l'index 0) — nécessiterait
  le filtre `ruby` (aucune action `mutate` native ne permet de
  manipuler un élément précis d'un tableau) — écarté : `event.original`
  conserve déjà le message brut intact, donc cette info serait
  dupliquée pour un coût de sécurité inutile (filtre `ruby` = surface
  d'exécution de code, voir note 01)
- **Renommer la capture Grok** (`message_parse` plutôt que `message`)
  — action native triviale, retenue

**Principe retenu** : éviter un conflit en amont plutôt que le nettoyer
après coup avec un outil plus lourd/risqué que celui qui l'a causé.

## Résultat final validé

Sur les deux lignes de test (avec et sans PID) :

```
{
        "hostname" => "rh8102",
       "processus" => "systemd",
       "timestamp" => "Jul 21 08:23:04",
   "message_parse" => "backup-job.service: Failed with result 'exit-code'.",
           "event" => { "original" => "Jul 21 08:23:04 rh8102 systemd[1]: backup-job.service: Failed with result 'exit-code'." },
         "message" => "Jul 21 08:23:04 rh8102 systemd[1]: backup-job.service: Failed with result 'exit-code'."
}
{
        "hostname" => "rh8102",
       "processus" => "kernel",
       "timestamp" => "Jul 21 08:25:00",
   "message_parse" => "EXT4-fs error: /var: filesystem full",
           "event" => { "original" => "Jul 21 08:25:00 rh8102 kernel: EXT4-fs error: /var: filesystem full" },
         "message" => "Jul 21 08:25:00 rh8102 kernel: EXT4-fs error: /var: filesystem full"
}
```

`processus`, `timestamp`, `hostname` corrects dans les deux cas ;
PID optionnel bien géré ; plus de conflit de type sur `message`.

## Résumé

1. `dissect` échoue net sur une structure qui varie (PID optionnel) —
   `grok` gère l'optionnalité via `(?:...)?`
2. La portée d'un groupe optionnel compte : englober trop large peut
   faire disparaître une capture censée être toujours présente
3. Un nom de champ Grok identique à un champ déjà existant transforme
   silencieusement ce champ en tableau plutôt que d'écraser —
   toujours vérifier les noms de champs déjà posés par l'`input`
4. Préférer éviter un conflit en amont (renommer) plutôt que le
   nettoyer après coup avec un outil plus lourd (filtre `ruby`)

## Lien avec les notes existantes

`01-panorama-alternatives-interfacage-securite.md` (dissect vs grok en
théorie, risque du filtre `ruby`), `03-premier-pipeline-stdin-stdout-filter-mutate.md`
(event structuré dès l'`input`, champ `message` déjà existant).

## Sources

- [Introduction pratique à Logstash (Elastic, fr)](https://www.elastic.co/fr/blog/a-practical-introduction-to-logstash)
- [logstash-patterns-core — grok-patterns (ECS v1)](https://github.com/logstash-plugins/logstash-patterns-core/blob/main/patterns/ecs-v1/grok-patterns)
- [Do you grok Grok? (Elastic Blog)](https://www.elastic.co/blog/do-you-grok-grok)
- [Introducing Logstash Dissect (Elastic Blog)](https://www.elastic.co/blog/logstash-dude-wheres-my-chainsaw-i-need-to-dissect-my-logs)
- [Logstash Performance Tuning (Hyperflex)](https://www.hyperflex.co/solution-and-best-practices/logstash-performance-tuning-solving-the-mystery-of-event-delays)
