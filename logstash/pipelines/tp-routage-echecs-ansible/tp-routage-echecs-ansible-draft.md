# TP — Dupliquer les erreurs Ansible vers un fichier lisible (draft)

Statut : **design posé, pas encore exécuté**. Prolonge
`tp-callback-ansible` : tout part vers Elasticsearch comme
aujourd'hui, et en plus les erreurs sont **dupliquées** (note 29)
vers un fichier dédié — pas juste la ligne JSON brute, mais un
message reconstruit lisible par un humain (façon ligne syslog),
construit à partir des champs extraits de `ansible_result` via le
filtre `json`.

Pipeline-to-pipeline envisagé puis écarté : un seul traitement léger
en aval, pas besoin d'isoler quoi que ce soit pour ce scope.

## Contexte — champs réels du callback

- **`status`** — `"OK"`, `"FAILED"`, `"SKIPPED"`, `"UNREACHABLE"`
- **`ansible_result`** — chaîne JSON encodée (`self._dump_results()`),
  détail complet du résultat Ansible, reçue par Logstash comme une
  string à parser

## Étape 1 — Parser `ansible_result` avec le filtre `json`

```
filter {
  if [status] == "FAILED" or [status] == "UNREACHABLE" {
    json {
      source => "ansible_result"
      target => "[ansible_result_parsed]"
    }
  }
}
```
`target` explicite : évite toute collision entre les clés du JSON
parsé (contenu arbitraire d'un résultat Ansible) et les champs déjà
présents sur l'event (`host`, notamment).

## Étape 2 — Vérifier la structure obtenue selon le type de résultat

Sur un `FAILED` (erreur de module, `msg` explicite) vs un
`UNREACHABLE` (hôte injoignable, aucun module exécuté) — la structure
de `ansible_result_parsed` est-elle comparable, ou fondamentalement
différente (pas de clé `module`/`invocation` sur un `UNREACHABLE`) ?
À observer avant l'étape suivante, pas à supposer uniforme.

## Étape 3 — Reconstruire un message lisible pour le fichier d'erreurs

Objectif : le fichier dédié ne doit pas contenir le blob JSON brut,
mais une ligne construite façon syslog, lisible sans outil — par
exemple :
```
mutate {
  add_field => {
    "message_erreur" => "%{[ansible_host]} - %{[ansible_task]} - %{[ansible_result_parsed][msg]}"
  }
}
```
Champ exact à utiliser dépend de ce que l'Étape 2 a révélé (le nom de
la clé contenant le message d'erreur peut différer entre `FAILED` et
`UNREACHABLE`) — à ajuster une fois la vraie structure observée,
prévoir éventuellement deux constructions différentes selon le cas.

## Étape 4 — Sortie dupliquée

```
output {
  elasticsearch { ... }  # toujours, document inchangé (pas de _parsed dessus)

  if [status] == "FAILED" or [status] == "UNREACHABLE" {
    file {
      path => "/chemin/erreurs_ansible.log"
      codec => line { format => "%{message_erreur}" }
    }
  }
}
```

## Ce qu'il faudra vérifier/clarifier en exécutant

- Structure de `ansible_result_parsed` sur `FAILED` vs `UNREACHABLE`
- Nom de clé du message d'erreur selon le cas — un seul `mutate`
  suffit, ou faut-il deux constructions distinctes
- Confirmer que les documents ES restent inchangés (pas de
  `ansible_result_parsed` dessus), seul le fichier dupliqué en
  bénéficie

## Compétences pratiquées

- Duplication en sortie (note 29), jamais pratiquée jusqu'ici
- Filtre `json` sur un cas JSON-dans-JSON (note 28), avec un vrai
  objectif de lisibilité humaine en sortie, pas juste un exercice
  isolé
- Reconstruction d'un message lisible à partir de champs structurés
  (`mutate`/`sprintf`)

## Lien avec les notes existantes

`tp-callback-ansible-resultat.md` (pipeline d'entrée réutilisé tel
quel), `28-codec-filtre-json-approfondi.md` (filtre `json`,
`target`), `29-sorties-multiples.md` (duplication vs routage).
