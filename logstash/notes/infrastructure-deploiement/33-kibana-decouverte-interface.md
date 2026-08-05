# Kibana — découverte pratique de l'interface

Notes en vrac, accumulées au fil des premiers tests (note 31/32) —
pas une théorie posée à l'avance, des repères pratiques trouvés en
naviguant. À compléter au fil des prochaines sessions plutôt que
figé d'un coup.

## Se repérer dans le menu (☰, en haut à gauche)

Plusieurs sections cohabitent, faciles à confondre au premier abord :
- **Analytics → Discover** — explorer les events bruts (le point
  d'entrée le plus utile pour nous, voir des logs)
- **Stack Management → Index Management** — indices/data streams
  réels, sans le bruit d'"Enterprise Search" qu'on croise ailleurs
  dans l'UI
- **Stack Management → Data Views** — obligatoire avant de pouvoir
  utiliser Discover sur un nouvel index (pattern du type `logs-*`,
  champ de temps `@timestamp`)
- **"Elasticsearch" (section à part, en haut)** — orientée moteur de
  recherche (indices de contenu, web crawlers...), pas notre usage —
  facile de s'y perdre en cherchant juste "les index"
- **"Add integrations"** — catalogue Fleet/Elastic Agent (500+
  connecteurs), sans rapport avec un pipeline Logstash fait main —
  piège classique en cherchant "comment envoyer des données", puisque
  Kibana pousse cette voie par défaut sur ses écrans d'accueil

## KQL — l'essentiel pratique, au-delà de `champ:valeur`

- `and` / `or` / `not`, avec parenthèses pour grouper :
  `(process.name:sshd or process.name:sudo) and not host.hostname:rocky.localdomain`
- Comparaisons numériques directes, sans syntaxe spéciale :
  `response_code >= 400`
- Existence d'un champ (vrai si présent et non vide) : `process.pid:*`
  — utile pour repérer les events où un parsing a bien extrait quelque
  chose
- Wildcard en fin de mot : `process.name:ssh*`
- Phrase exacte entre guillemets : `message:"connection closed"` —
  sans les guillemets, KQL cherche les mots séparément, pas la phrase
  dans l'ordre

**Piège à garder en tête** (lien direct avec note 32, `text` vs
`keyword`) : `champ:valeur` ne se comporte pas pareil selon le type du
champ visé — correspondance quasi exacte sur un champ `keyword`,
recherche par mot sur un champ `text`. Confondre les deux donne des
résultats "qui matchent trop" ou "pas assez" sans comprendre pourquoi,
si on ignore lequel des deux on interroge.

## Dev Tools → Grok Debugger

Outil dédié pour itérer sur un pattern grok sans relancer Logstash à
chaque essai : coller une ligne de log brute + le pattern, il montre
en direct les champs extraits (ou l'échec). Change concrètement la
boucle de feedback comparé à ce qui a été fait sur le TP
`ansible-playbook -v` (Palier 2) — itérer en relançant tout le
pipeline à chaque correction de pattern.

Point non vérifié, à tester avant de s'y fier : les patterns
personnalisés (`patterns_dir`, `SYSLOGBASE_PERSO`) sont-ils reconnus
tels quels, ou faut-il les redéfinir manuellement dans un champ
"Custom Patterns" séparé de l'UI ?

## Résumé

1. Discover + Data Views (Stack Management) = le duo minimal pour
   explorer des logs — le reste de l'UI (section "Elasticsearch",
   "Add integrations") répond à d'autres besoins, pas le nôtre
2. KQL : `and`/`or`/`not`, comparaisons numériques, `champ:*`
   (existence), wildcard en fin de mot, guillemets pour phrase exacte
3. `champ:valeur` en KQL dépend du type du champ (`text` vs
   `keyword`) — même piège que celui déjà identifié en note 32
4. Grok Debugger (Dev Tools) accélère l'itération sur un pattern grok,
   sans repasser par un vrai pipeline Logstash à chaque essai — à
   vérifier si les patterns personnalisés y sont reconnus nativement

## Lien avec les notes existantes

`31-installation-elasticsearch-kibana.md` (premier accès à l'UI),
`32-archi-es-base.md` (`text`/`keyword`, base du piège KQL),
`04-construction-premier-pattern-grok.md`/
`08-grok-conditionnel-kernel-gestionechec.md` (pattern `SYSLOGBASE_PERSO`,
boucle de feedback comparée au Grok Debugger).
