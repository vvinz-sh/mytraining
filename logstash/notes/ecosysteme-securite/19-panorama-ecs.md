# Logstash — Panorama ECS (Elastic Common Schema)

Clôture le Palier 0 — dernier point de panorama théorique. On avait
déjà utilisé ECS sans le nommer plusieurs fois (`host.hostname`,
`event.original`, `event.created` en note 15, `[backup][size]`/
`[backup][unit]` inspirés de `SYSLOGPROG`) — cette note formalise ce
qu'on avait déjà pratiqué intuitivement.

## Le principe : normaliser des sources hétérogènes

ECS impose un **vocabulaire commun** pour des concepts qui reviennent
partout (une adresse IP source, un timestamp, un hostname) — plutôt
que chaque source de log (firewall, appli web, serveur Linux) invente
son propre nom (`src_ip` vs `client_ip` vs `remote_addr` pour la même
idée).

**Bénéfice concret construit ensemble** : avec un champ unique
`source.ip` respecté par toutes les sources normalisées, une seule
requête Kibana traverse **toutes** les sources d'un coup — sans avoir
à connaître ni répéter le nom propre à chaque type de log. C'est ce
qui rend une corrélation de sécurité possible (repérer la même IP
suspecte dans un firewall **et** une appli web simultanément).

## Field sets : des objets imbriqués, pas des champs à plat

ECS regroupe les champs liés en **field sets** (`host.*`, `event.*`,
`process.*`, `network.*`...) — des objets imbriqués dans Elasticsearch,
sauf le **Base field set**, seul groupe défini à la racine de l'event
(`@timestamp`, `message`, `tags`, `labels`, `ecs.version`).

## Trois niveaux de champs, pas deux

Distinction importante clarifiée en session (une confusion initiale
corrigée) :

- **Core** — champs officiels ECS, présents dans la plupart des
  events, base des recherches/dashboards standards
- **Extended** — champs officiels ECS aussi, mais spécifiques à des
  cas d'usage précis, moins systématiquement peuplés
- **Custom** — **hors du schéma ECS entièrement**, propre à un besoin
  métier non couvert. Nos propres `[backup][size]`/`[backup][unit]`
  sont dans cette troisième catégorie, pas "Extended" — confirmé par
  la doc : *"ECS is a permissive schema. If your events have
  additional data that cannot be mapped to ECS, you can simply add
  them to your events, using custom field names."*

## Piège découvert : un nom conforme ne suffit pas, l'unité doit l'être aussi

Question posée en creusant notre propre cas `backup.size` : ECS
prévoit bien un field set **`file`**, avec un champ `file.size` —
mais attendu **en bytes**, une unité normalisée. Notre pipeline
produit `45` et `GB` séparément, **sans conversion réelle** en octets.

**Conséquence** : renommer bêtement `backup.size` en `file.size`
n'aurait pas suffi — une vraie conformité ECS exige aussi de
**convertir** la valeur dans l'unité attendue, pas seulement d'adopter
le bon nom de champ. Une conformité de façade (bon nom, mauvaise
valeur) serait pire que pas de conformité du tout — elle laisserait
croire à un outil Kibana standard que la valeur est en bytes alors
qu'elle ne l'est pas.

## Champ officiel et champ custom coexistent, l'un ne remplace pas l'autre

Question tranchée : faut-il choisir entre `file.size` (ECS) et
`backup.size` (custom) ? Réponse : **les deux, en complément**,
servant deux publics différents :

- **`backup.*`** (custom) — lisible directement dans l'unité
  d'origine, pratique pour un contexte métier immédiat, sans calcul
  mental
- **`file.size`** (ECS, converti en bytes) — pour l'interopérabilité
  avec le reste de l'écosystème Elastic, exploitable par des
  dashboards Kibana standards qui s'attendent à cette unité précise

Le principe général : peupler les champs ECS officiels **là où le
concept générique existe réellement**, garder un namespace custom
pour tout ce qui est spécifique et non couvert par le schéma — pas un
choix binaire entre les deux approches.

## Résumé

1. ECS normalise le vocabulaire entre sources hétérogènes — le vrai
   bénéfice est de pouvoir chercher/corréler à travers plusieurs
   sources avec un seul nom de champ
2. Field sets = objets imbriqués (sauf Base field set, à la racine)
3. Trois niveaux, pas deux : Core (officiel, courant), Extended
   (officiel, spécifique), Custom (hors schéma, permis explicitement)
4. Un nom de champ conforme ne suffit pas — la valeur doit aussi
   respecter l'unité/format attendu par ECS (ex : bytes pour
   `file.size`)
5. Champs officiels et custom coexistent en complément, pas en
   remplacement l'un de l'autre

## Lien avec les notes existantes

`15-filtre-date-timestamp.md` (`event.created`/`event.original` déjà
utilisés sans les nommer ECS explicitement), `07-grok-conditionnel-regex-brute.md`
(`[backup][size]`/`[backup][unit]`, notre propre champ custom
maintenant identifié précisément comme tel), `04-construction-premier-pattern-grok.md`
(`SYSLOGPROG` officiel, source d'inspiration du regroupement imbriqué).

## Sources

- [Implementation patterns (Elastic Docs)](https://www.elastic.co/docs/reference/ecs/ecs-principles-implementation)
- [Design principles (Elastic Docs)](https://www.elastic.co/guide/en/ecs/master/ecs-principles-design.html)
- [ECS field reference (Elastic Docs)](https://www.elastic.co/docs/reference/ecs/ecs-field-reference)
- [File fields (Elastic Docs)](https://www.elastic.co/docs/reference/ecs/ecs-file)
- [Elastic Common Schema — Normalizing your data with ECS (Elastic)](https://www.elastic.co/elasticsearch/common-schema)
