# Logstash — Codec vs filtre `json` : approfondissement (Palier 3)

Complète la note 10 (Palier 1, premier contact avec `codec => json`) en
distinguant le codec du **filtre** `json` 

## Codec vs filtre : où chacun agit, sur quelle portée

- **Codec `json`** : paramètre d'`input`/`output`, agit sur **toute la
  ligne d'entrée** — celle-ci doit être du JSON de bout en bout.
  N'aurait jamais pu fonctionner directement sur
  `deployer_filebeat.log` : chaque ligne mélange du texte libre et,
  parfois, un fragment JSON en fin de ligne seulement — pas du JSON
  de bout en bout.
- **Filtre `json`** (`filter { json { source => "champ" } }`) : agit
  sur un **champ précis, déjà existant** dans un event déjà construit
  par autre chose (grok, par exemple), et parse seulement son contenu
  comme du JSON. C'est l'outil qui aurait permis d'exploiter le blob
  systemd (`{"changed": true, ..., "status": {...}}`) du TP ansible,
  resté volontairement en `GREEDYDATA` sans nom — il aurait fallu
  d'abord nommer ce fragment dans un champ temporaire (même principe
  que l'isolement de `recap_line` avant `kv`), puis lui appliquer
  `json { source => "ce_champ" }`.

## `target` : même logique que `kv`, disponible sur les deux (codec ET filtre)

Sans `target` précisé, les clés extraites atterrissent **à la racine
de l'event** (top-level) — que ce soit avec le codec ou le filtre.
Risque concret, dans la continuité directe du bug `kv`/`ansible.target`
déjà rencontré : une clé JSON nommée `host`, `tags`, ou `@timestamp`
**écrase silencieusement** le champ de même nom déjà présent dans
l'event. D'où l'intérêt de toujours préciser `target` explicitement,
même quand ce n'est pas obligatoire.

Le warning vu dans les logs d'exécution du TP ansible
(`jsonlines - ECS compatibility is enabled but 'target' option was
not specified`) illustre exactement ce principe — mais attention,
**pas dans notre config à nous** : ce warning venait d'un plugin
`jsonlines` interne à l'API de monitoring de Logstash (port 9600,
déjà croisé au Palier 0), pas d'un choix qu'on avait fait. Le
principe qu'il signale (ECS activé + `target` non précisé = warning)
reste identique pour le filtre `json` qu'on configurerait nous-mêmes.

## Structure imbriquée préservée telle quelle (codec, en entrée)

Un objet JSON imbriqué (`{"host": {"name": "x"}}`) ou un tableau
(`{"tags": ["a", "b"]}`) ne sont pas aplatis par le codec — ils
deviennent directement des champs imbriqués/tableaux dans l'event,
sans transformation ni perte de structure. Appliqué au cas du blob
systemd : si cette ligne avait été du JSON pur en entrée (pas
mélangée à du texte `changed: [...] =>`), le codec aurait
automatiquement produit `ansible.status.ActiveState`,
`ansible.status.CPUAccounting`, etc. — sans écrire le moindre pattern
grok.

Autre comportement du codec (entrée) à connaître : un **tableau JSON
à la racine** génère **plusieurs events**, un par élément — un objet
JSON simple, lui, ne génère toujours qu'un seul event.

## Gestion d'échec : rien ne casse, tout est tagué

Codec et filtre partagent le même principe défensif :
- **Filtre** : contenu du champ source non-JSON valide → event
  laissé intact, tag `_jsonparsefailure` ajouté (configurable via
  `tag_on_failure`), rien de destructeur
- **Codec** : payload non-JSON valide en entrée → *fallback* en texte
  brut stocké dans `message`, même tag `_jsonparsefailure`

Nuance supplémentaire côté filtre : `skip_on_invalid_json => true`
permet de ne **rien** tagger du tout sur un échec — utile si le champ
source contient parfois du JSON, parfois du texte simple, sans que ce
soit une vraie anomalie à signaler à chaque fois.

## JSON imbriqué dans du JSON : le filtre ne descend pas récursivement seul

Si une valeur JSON est elle-même une chaîne contenant du JSON
(JSON-dans-JSON), le filtre `json` ne le détecte pas automatiquement
en un seul passage — il faut le rejouer une seconde fois, avec
`source` pointant cette fois vers le champ nouvellement créé par le
premier passage.

## Résumé

1. Codec = toute la ligne d'entrée/sortie doit être du JSON ; filtre
   = un champ précis d'un event déjà construit
2. `target` existe sur les deux, même logique que `kv` — sans lui,
   risque d'écraser silencieusement un champ existant à la racine
3. Le codec préserve la structure imbriquée du JSON telle quelle
   (objets/tableaux), sans passer par grok
4. Un tableau JSON à la racine (codec, entrée) génère un event par
   élément, pas un seul event global
5. Échec géré sans casse des deux côtés (`_jsonparsefailure`,
   `tag_on_failure`), avec `skip_on_invalid_json` en option côté
   filtre pour les champs mixtes JSON/texte
6. JSON imbriqué dans du JSON nécessite de rejouer le filtre une
   deuxième fois, pas de récursion automatique

## Lien avec les notes existantes

`10-codecs-structuration-input-output.md` (premier contact avec
`codec => json`, distinction codec/filtre posée en théorie),
`tp-parsing-ansible-verbose-resultat.md` et
`26-multiline-implementation-ansible-v.md` (blob JSON systemd laissé
en `GREEDYDATA` sans nom, bug `kv`/`target` — même famille de
vigilance sur l'écrasement de champs).

## Sources

- [JSON filter plugin (Logstash Reference 8.19, Elastic)](https://www.elastic.co/guide/en/logstash/8.19/plugins-filters-json.html) — comportement de `target`, `tag_on_failure`, `skip_on_invalid_json`, gestion du `@timestamp`
- [JSON codec plugin (Logstash Reference 8.19, Elastic)](https://www.elastic.co/guide/en/logstash/8.19/plugins-codecs-json.html) — comportement de `target`, tableau JSON → plusieurs events, fallback sur échec
- [logstash-filter-json source (GitHub)](https://github.com/logstash-plugins/logstash-filter-json/blob/main/lib/logstash/filters/json.rb)
