# Logstash — Architecture des plugins : 4 types, gestion, provenance

Complète le Palier 1 — clarifie la hiérarchie conceptuelle derrière
tous les composants manipulés depuis le début du module.

## Plugin : la catégorie générale, 4 types

**Plugin** est le terme générique pour n'importe quel composant
enfichable dans Logstash. Il en existe **4 types**, chacun avec un
rôle distinct :

| Type | Rôle | Exemples déjà manipulés |
|---|---|---|
| `input` | Réception de la donnée brute | `stdin`, `file` (à venir) |
| `filter` | Enrichissement/transformation d'un event déjà construit | `grok`, `mutate` |
| `output` | Écriture de l'event vers une destination | `stdout`, `file` |
| `codec` | Structuration au moment de l'entrée/sortie brute | `json`, `rubydebug` |

`grok` et `mutate` sont donc des plugins de type **filter** ; `json`
et `rubydebug` des plugins de type **codec** (voir note 10) — une
distinction qui n'avait jamais été nommée explicitement jusqu'ici,
malgré leur usage constant depuis le Palier 1.

## Gestion des plugins : `logstash-plugin`

Un binaire séparé de `logstash` lui-même, dédié à la gestion des
plugins :
```
/usr/share/logstash/bin/logstash-plugin list
```

Permet aussi `install`/`update`/`remove` — ajouter ou retirer un
plugin sans réinstaller Logstash dans son ensemble.

## Provenance : RubyGems

Question posée : d'où `logstash-plugin install` télécharge-t-il un
nouveau plugin ? Piste explorée en premier lieu (`path.plugins` dans
`logstash.yml`) — fausse route, ce réglage concerne uniquement les
plugins **personnalisés déjà présents localement** sur le disque, pas
la source de téléchargement d'un nouveau plugin.

**Réponse** : **RubyGems**, le registre de paquets de l'écosystème
Ruby (équivalent de PyPI pour Python ou npm pour Node.js) — cohérent
avec le fait que Logstash tourne sur JRuby. Confirme et relie
concrètement un point de vigilance déjà noté en théorie en note 01
(*"les plugins tiers viennent de RubyGems — à surveiller comme toute
dépendance externe"*), sans qu'on ait alors identifié le mécanisme
d'installation précis qui s'y rattache.

## Résumé

1. "Plugin" est la catégorie générale ; 4 types existent : `input`,
   `filter`, `output`, `codec` — tous les composants manipulés depuis
   le début du module (`grok`, `stdin`, `json`...) sont des instances
   de l'un de ces 4 types
2. `logstash-plugin` (binaire séparé de `logstash`) gère l'installation
   des plugins indépendamment du reste de l'installation
3. Les plugins proviennent de RubyGems — la chaîne d'approvisionnement
   à surveiller identifiée en note 01 devient ici un mécanisme concret
   plutôt qu'une simple mention théorique

## Lien avec les notes existantes

`01-panorama-alternatives-interfacage-securite.md` (RubyGems comme
risque de chaîne d'approvisionnement, mentionné sans mécanisme précis
à l'époque), `10-codecs-structuration-input-output.md` (codec comme
4e type de plugin, distinct des filtres).

## Sources

- [Plugin Manager Reference (Elastic, 8.19)](https://www.elastic.co/guide/en/logstash/8.19/plugin-manager.html)
