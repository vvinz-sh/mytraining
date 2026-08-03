# TP — Router les échecs de tâches Ansible (callback plugin) vers une sortie séparée (draft)

Statut : **design posé, pas encore exécuté**. Dernier TP à drafter du
Palier 4. Prolonge directement `tp-callback-ansible` (Palier 3) —
même pipeline d'entrée (TCP + `codec json`), cette fois avec un vrai
routage dessus plutôt qu'un `stdout` brut.

## Contexte — champs réels du callback (vérifiés en lisant le code source)

Plutôt que de deviner les noms de champs, lecture directe de
`plugins/callback/logstash.py` (ansible-collections/community.general).
Champs pertinents pour ce TP :

- **`status`** — chaîne parmi `"OK"`, `"FAILED"`, `"SKIPPED"`,
  `"UNREACHABLE"` (pas de booléen simple, une string à comparer)
- **`ansible_type`** — `"task"`, `"start"`, `"finish"`, `"setup"`,
  `"import"` — distingue un event de task d'un event de démarrage/fin
  de playbook
- **`ansible_task`**, **`ansible_host`**, **`ansible_play_name`** —
  contexte de la task concernée
- **`ansible_result`** — **chaîne JSON encodée** (pas un objet JSON
  imbriqué nativement), produite par `self._dump_results()` côté
  callback Python. Contient le détail complet du résultat Ansible
  (message d'erreur, module utilisé, etc.) — mais Logstash la reçoit
  comme une string à parser, pas comme une structure déjà exploitée
- **`ansible_changed`** — booléen distinct de `status` (`true`/`false`)

## Étape 1 — Router selon `status`

```
filter {
  if [status] == "FAILED" or [status] == "UNREACHABLE" {
    # branche échec
  } else if [status] == "OK" or [status] == "SKIPPED" {
    # branche normale
  }
}
```
Question à trancher, pas évidente d'emblée : `UNREACHABLE` (l'hôte
cible ne répond pas) fait-il partie des "échecs de tâche" à router
avec `FAILED`, ou est-ce une catégorie à part (un problème de
connectivité, pas un problème de task) méritant sa propre sortie
plutôt que d'être mélangé à `FAILED` ? Et que faire de `SKIPPED` —
avec `OK` dans la branche "normale", ou dans une troisième catégorie ?
Repense au principe déjà établi sur les sorties multiples (note 29) :
rien n'empêche plus de deux branches si les catégories sont
réellement différentes.

## Étape 2 — Exploiter `ansible_result` (JSON-dans-JSON, note 28)

Sur la branche échec, `ansible_result` contient le vrai détail de
l'erreur, mais **enfermé dans une string** — appliquer le filtre
`json` dessus, comme anticipé en note 28 pour un cas JSON-dans-JSON :
```
filter {
  json {
    source => "ansible_result"
    target => "[ansible_result_parsed]"
  }
}
```
Point de vigilance direct depuis la note 28 : `target` explicite ici
n'est pas optionnel par prudence — c'est quasiment nécessaire, vu que
le contenu exact de `ansible_result` (un résultat Ansible arbitraire)
pourrait très bien contenir des clés qui entrent en collision avec des
champs déjà présents (`host`, par exemple, déjà utilisé par le
callback lui-même en dehors de `ansible_result`).

Vérifier aussi, plutôt que présumer : sur un event `UNREACHABLE` (hôte
injoignable), `ansible_result` contient-il un JSON structuré
exploitable de la même façon que sur un `FAILED` (erreur de module),
ou une structure différente (pas de "module" exécuté, juste une
erreur de connexion) ?

## Étape 3 — Sorties séparées

```
output {
  if [status] == "FAILED" or [status] == "UNREACHABLE" {
    file { path => "/chemin/echecs_ansible.log" }
  } else {
    file { path => "/chemin/ok_ansible.log" }
  }
}
```
Cohérent avec le pattern déjà pratiqué sur les TP `ansible-playbook -v`
(`ok_logs`/`failed_logs`), mais cette fois sur un champ natif
(`status`) plutôt qu'un tag de parsing (`_grokparsefailure`) — aucun
grok nulle part dans ce TP, contrairement à tous les précédents sur
Ansible.

## Ce qu'il faudra vérifier/clarifier en exécutant

- `UNREACHABLE` rattaché à `FAILED`, ou catégorie séparée — décision
  à prendre en observant un vrai cas des deux plutôt qu'en théorie
- Sort de `SKIPPED` : avec `OK`, ou catégorie à part
- Structure réelle de `ansible_result` sur `UNREACHABLE` vs `FAILED`
  (module exécuté ou pas) — à vérifier, pas supposer identique
- Collision de champs potentielle entre `ansible_result_parsed` et le
  reste de l'event, à confirmer absente une fois `target` en place

## Compétences pratiquées

- Routage sur un champ de statut natif, sans aucun grok — contraste
  direct avec tous les TP Ansible précédents (recollage/parsing manuel)
- Application concrète du cas JSON-dans-JSON anticipé en note 28,
  sur une vraie donnée plutôt qu'un exemple jouet
- Décision de catégorisation (`UNREACHABLE` avec ou sans `FAILED`)
  fondée sur l'observation d'un vrai cas, pas une convention arbitraire

## Lien avec les notes existantes

`tp-callback-ansible-draft.md` (pipeline d'entrée réutilisé tel quel),
`28-codec-filtre-json-approfondi.md` (filtre `json`, `target`,
JSON-dans-JSON — appliqué ici en pratique), `29-sorties-multiples.md`
(routage vs duplication), `tp-parsing-ansible-verbose-resultat.md`
(contraste avec le routage `_grokparsefailure`, sans champ natif).
