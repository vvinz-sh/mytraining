# TP — Callback plugin `community.general.logstash` : Ansible → Logstash en direct (draft)

Statut : **design posé, pas encore exécuté**. Dernier des 3 TP
pratiques du Palier 3, alternative "propre" au recollage `multiline`
fait sur `ansible-playbook -v` — ici, les events du playbook arrivent
**déjà structurés en JSON**, directement en TCP, sans passer par un
fichier texte à reparser après coup.

## Contexte

Nœud de contrôle : WSL (là où tourne `ansible-playbook`). Flux réseau
validé : WSL → Rocky (Logstash). Le rôle Filebeat existant
(`deployer_filebeat.log`) ne sera **pas** réutilisé ici — un nouveau
rôle, plus simple, sera écrit exprès pour produire un mélange de
statuts (`ok`, `changed`, `failed`, `skipped`), chose que le rôle
Filebeat ne permettait pas (aucune task en échec dans son run).

Pas de comparaison explicite avec le TP `multiline` en préambule —
le rapprochement (JSON structuré nativement vs recollage +
grok manuel a posteriori) se fera de lui-même en conclusion, sans
l'annoncer dès le départ.

## Étape 1 — Écrire un rôle qui produit les 4 statuts délibérément

Question à trancher avant d'écrire quoi que ce soit : quelle cible
pour ce rôle (`localhost` sur WSL, Rocky, ou RH8103) ? Le choix influe
sur les modules disponibles et sur ce qui est réaliste à faire échouer
sans casser un service existant sur une VM du lab.

Pistes pour forcer chaque statut sans dépendre du hasard :
- **`ok`** — une task idempotente rejouée une deuxième fois (elle
  était `changed` au premier run, `ok` ensuite), ou `changed_when: false`
  sur une commande qui s'exécute réellement
- **`changed`** — n'importe quelle task standard qui modifie l'état
  du système (paquet, fichier, service)
- **`failed`** — une commande qui échoue franchement (`command: /bin/false`),
  ou une condition `failed_when` déclenchée volontairement
- **`skipped`** — une task avec `when:` évalué à faux

## Étape 2 — Installer et configurer le callback côté WSL

`python-logstash` doit être installé sur le nœud de contrôle (WSL),
pas sur la cible du playbook. Configuration via `ansible.cfg`,
section `[callback_logstash]` (`server`, `port`, `type`, `pre_command`
optionnel) — ou variables d'environnement équivalentes
(`LOGSTASH_SERVER`, `LOGSTASH_PORT`...).

Point à vérifier plutôt que supposer : le nom du réglage qui active le
callback a changé selon les versions d'Ansible
(`callback_whitelist` dans les versions plus anciennes,
`callbacks_enabled` dans les plus récentes) — à confirmer sur la
version installée sur le WSL avant d'écrire la config, pas après.

## Étape 3 — Configurer l'input `tcp` + `codec json` côté Logstash (Rocky)

```
input {
  tcp {
    port => 5000
    codec => json
  }
}
```
Port à choisir en cohérence avec ce qui est libre sur Rocky (5000 par
défaut dans les exemples de la doc, à confirmer qu'il n'est pas déjà
pris par un autre pipeline du lab). Filtre : a priori **vide** au
départ — l'intérêt du test est justement de voir ce qui arrive tel
quel avant d'ajouter quoi que ce soit dessus.

Point à observer, pas à anticiper : les exemples officiels du plugin
ajoutent des champs sous `[@metadata][...]` (`beat`, `type`) côté
input. `@metadata` est un espace de champs qu'on n'a jamais croisé
jusqu'ici dans le module — à voir en pratique ce qu'il a de
particulier par rapport à un champ normal de l'event (repense à ce
qu'on a appris sur `target`/écrasement de champs : est-ce que
`@metadata` a été pensé justement pour éviter ce genre de collision ?).

## Étape 4 — Lancer le rôle et observer la sortie brute

Sortie Logstash en `stdout`/`file`, sans filtre. Comparer, sur les 4
types d'events reçus (`ok`/`changed`/`failed`/`skipped`), la structure
JSON obtenue nativement à ce qu'il aurait fallu écrire à la main en
grok pour arriver au même résultat sur `ansible-playbook -v`.

## Ce qu'il faudra vérifier/clarifier en exécutant

- Nom exact du réglage d'activation du callback selon la version
  d'Ansible installée sur le WSL (`callback_whitelist` vs
  `callbacks_enabled`)
- Port TCP réellement libre sur Rocky pour ce nouvel input
- Ce que contient concrètement `[@metadata][...]`, et si ces champs
  apparaissent dans la sortie `stdout`/`file` par défaut ou sont
  traités différemment des champs normaux
- Cible du nouveau rôle (localhost WSL, Rocky, ou RH8103) — à
  trancher avant d'écrire les tasks
- Est-ce que le callback envoie **un event par task**, ou un seul
  event de synthèse en fin de playbook (`playbook_on_stats`) en plus
  des events par task — à observer plutôt que supposer, ça conditionne
  ce qu'il y a à traiter côté Logstash

## Compétences pratiquées

- Configuration d'un flux JSON structuré nativement en TCP, sans
  fichier ni grok intermédiaire
- Découverte du concept `@metadata` (nouveau, jamais croisé jusqu'ici)
- Comparaison implicite entre ingestion JSON native et reconstruction
  manuelle (grok + multiline) d'une structure équivalente

## Lien avec les notes existantes

`28-codec-filtre-json-approndi.md` (codec `json`, `target`,
structure imbriquée préservée — directement applicable ici),
`tp-parsing-ansible-verbose-resultat.md` et
`26-multiline-implementation-ansible-v.md` (l'approche manuelle à
laquelle ce TP sert d'alternative, sans le dire explicitement au
départ).
