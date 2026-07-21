# TP — Transformer le TP Ansible+LLM en vrai agent (boucle autonome)

Statut : **design posé, pas encore exécuté**. Prolonge
`tp-ansible-llm-resultat.md` (TP 1, réussi) en ajoutant une vraie
autonomie multi-étapes — pour sentir en pratique la différence
agent/tool use vue en théorie.

## Rappel du problème avec le TP 1 (tool use, pas agent)

Le TP 1 faisait : lire un log → appeler l'API → afficher le résumé. Une
seule action, aucune boucle, aucune décision autonome sur "quoi faire
ensuite" — exactement du **tool use**, pas un agent (même si l'appel API
en lui-même impliquait du raisonnement du LLM).

## Objectif du TP 2 : introduire une vraie boucle autonome

Scénario : le playbook analyse un extrait de log, mais si le LLM juge
l'extrait **insuffisant** pour poser un diagnostic fiable (ex : pas
assez de contexte, log trop court), il doit **automatiquement** relancer
une recherche avec une fenêtre de log plus large — sans validation
humaine entre les tentatives — jusqu'à obtenir un diagnostic jugé
suffisant, ou atteindre un nombre maximal de tentatives.

Ça reproduit exactement le principe de l'agent vu en théorie :
réfléchir → agir → observer le résultat → réajuster → recommencer,
jusqu'à l'objectif ou une limite.

## Mécanisme Ansible : `until` / `retries` / `delay`

Ansible a un mécanisme natif de boucle conditionnelle sur une tâche,
parfaitement adapté ici — pas besoin de logique externe complexe :

```yaml
- name: Interroger le LLM jusqu'à diagnostic suffisant
  uri:
    url: "{{ llm_api_url }}"
    method: POST
    headers:
      x-api-key: "{{ llm_api_key }}"
      anthropic-version: "2023-06-01"
      content-type: application/json
    body_format: json
    body:
      model: "{{ llm_model }}"
      max_tokens: 400
      messages:
        - role: user
          content: >
            Voici un extrait de log : {{ log_content }}
            Réponds STRICTEMENT en JSON avec deux clés :
            "diagnostic_suffisant" (true/false) et "analyse" (texte).
            Mets "diagnostic_suffisant" à false si l'extrait est trop
            court ou ambigu pour conclure avec certitude.
    status_code: 200
    return_content: yes
  register: llm_response
  until: (llm_response.json.content[0].text | from_json).diagnostic_suffisant
  retries: 3
  delay: 2
```

Point clé pédagogique : `until` réévalue la condition après **chaque**
tentative, et Ansible **relance automatiquement** la tâche tant que la
condition n'est pas remplie (ou jusqu'à épuisement de `retries`) — c'est
la boucle autonome elle-même, fournie nativement par Ansible, sans avoir
à coder une boucle manuelle.

## Le vrai enjeu à concevoir : comment "réajuster" à chaque tentative

Une boucle qui repose exactement les mêmes données à chaque tentative
ne serait qu'une **répétition**, pas un agent — l'agent doit
**réajuster sa stratégie** entre les tentatives (comme le ticket support
qui change de mots-clés de recherche).

Idée à développer : faire varier la fenêtre de log envoyée à chaque
tentative, en fonction du numéro de tentative. Par exemple avec une
liste de commandes de plus en plus larges :

```yaml
vars:
  log_windows:
    - "tail -n 20 /var/log/messages-short"
    - "tail -n 100 /var/log/messages"
    - "tail -n 500 /var/log/messages"
```

Piste à explorer pendant l'implémentation : Ansible ne permet pas
nativement d'incrémenter une variable d'index à chaque `retry` d'un
`until` — il faudra probablement une astuce (ex : une tâche `shell`
englobante avec un compteur, ou une structure `block`/`rescue` en
boucle manuelle avec `loop` plutôt qu'`until` strict). Point à
clarifier concrètement en codant, pas encore résolu dans ce design.

## Critère d'arrêt à définir clairement

- **Succès** : `diagnostic_suffisant: true` → le playbook affiche
  l'analyse finale et s'arrête normalement.
- **Échec après épuisement des tentatives** : après 3 tentatives sans
  succès, le playbook doit `fail` proprement avec un message clair
  ("diagnostic impossible après 3 tentatives, log probablement trop
  pauvre en information"), plutôt que de continuer silencieusement avec
  un résultat non fiable.

## Ce qu'il faudra clarifier en le codant (pas encore résolu ici)

- Le mécanisme exact pour faire varier la source de log à chaque
  tentative dans une boucle `until` (Ansible n'expose pas nativement le
  numéro de tentative en cours dans une variable facilement réutilisable
  — à vérifier/tester).
- Le format de sortie structuré (JSON strict) demandé au LLM doit être
  fiabilisé — un LLM peut parfois ajouter du texte autour du JSON malgré
  la consigne ; prévoir un parsing tolérant ou une validation
  supplémentaire.
- Décider si le nombre de tentatives (3) et les tailles de fenêtre de
  log sont fixes ou paramétrables.

## Compétences visées

- Boucles conditionnelles Ansible (`until`, `retries`, `delay`)
- Distinction concrète agent vs tool use, vécue plutôt que théorique
- Parsing de sortie structurée (JSON) générée par un LLM, avec gestion
  de la fiabilité de ce format
- Design d'un critère d'arrêt explicite (succès vs échec propre)
