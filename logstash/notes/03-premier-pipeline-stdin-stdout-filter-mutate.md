# Logstash — Premier pipeline : stdin/stdout et filtre mutate

Palier 1 (suite) — test pratique du concept input/filter/output posé
en note 02, avec un pipeline réellement exécuté sur la VM Rocky9.

## Pipeline testé

```
input {
  stdin {}
}

filter {
  mutate {
    add_field => { "environnement" => "lab" }
  }
}

output {
  stdout {}
}
```

## Commande de lancement

Volontairement **sans `sudo`** — Logstash lui-même avertit que tourner
en superutilisateur est déconseillé (risque amplifié par le filtre
`ruby`, capable d'exécuter du code arbitraire dans le pipeline — voir
note 01). Le dossier `path.data` par défaut appartenant à
l'utilisateur système `logstash`, un espace de travail dédié a été
créé pour l'utilisateur courant plutôt que d'élargir les permissions
du dossier d'installation partagé :

```
mkdir -p ~/logstash-lab/data
/usr/share/logstash/bin/logstash -f /home/vinz/premier-pipeline.conf --path.data /home/vinz/logstash-lab/data
```

## Résultat — sans filtre

Entrée : `test`

```
{
         "event" => { "original" => "test" },
      "@version" => "1",
    "@timestamp" => 2026-07-30T15:58:51.301571463Z,
          "host" => { "hostname" => "rocky.localdomain" },
       "message" => "test"
}
```

Confirme ce qui était anticipé en théorie : même sans `filter`,
l'`input` construit déjà un event structuré, pas juste le texte brut.

- **`message`** — texte brut
- **`event.original`** — copie conservée du message d'origine, même
  si un futur filtre modifie `message`
- **`@timestamp`** — heure de **réception** par Logstash, pas extraite
  du texte (le filtre `date`, au Palier 2, permettra d'utiliser un
  vrai timestamp contenu dans le log à la place)
- **`host.hostname`** — utile dès que plusieurs machines enverront des
  logs (pertinent quand `rh8103`/Filebeat entrera en jeu)
- **`@version`** — version du schéma d'event, pas du logiciel

## Résultat — avec filtre `mutate`

Entrée : `test`

```
{
          "message" => "test",
    "environnement" => "lab",
       "@timestamp" => 2026-07-30T16:12:27.730634478Z,
             "host" => { "hostname" => "rocky.localdomain" },
         "@version" => "1",
            "event" => { "original" => "test" }
}
```

Confirme le principe d'**accumulation** : `environnement` s'ajoute à
côté des champs existants, ne remplace rien. Cohérent avec le
comportement séquentiel des blocs `filter` déjà posé en théorie (note
02) — chaque étape enrichit l'event plutôt que de le reconstruire.

## Résumé

1. Un event Logstash est toujours structuré, même sans `filter` —
   l'`input` seul ajoute déjà `@timestamp`, `host`, `event.original`
2. Un `filter { mutate { add_field ... } }` enrichit par accumulation,
   jamais par remplacement implicite
3. Éviter `sudo` pour lancer Logstash manuellement — isoler un
   `path.data` dédié à l'utilisateur courant plutôt que d'élargir les
   permissions du dossier d'installation

## Lien avec les notes existantes

`01-panorama-alternatives-interfacage-securite.md` (risque du filtre
`ruby`, moindre privilège), `02-installation-ansible-architecture-input-filter-output.md`
(déploiement, architecture théorique input/filter/output).

## Sources

- [Introduction pratique à Logstash (Elastic, fr)](https://www.elastic.co/fr/blog/a-practical-introduction-to-logstash)
