# TP — Transformer le TP Ansible+LLM en vrai agent (boucle autonome)

Statut : **design complet, prêt à coder**. Les deux points d'ingénierie
identifiés (parsing JSON fiable, réajustement de stratégie par
tentative) sont maintenant résolus dans ce document (prefill + `loop`
manuel). Prolonge `tp-ansible-llm-resultat.md` (TP 1, réussi) en ajoutant
une vraie autonomie multi-étapes — pour sentir en pratique la différence
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

## Mécanisme Ansible : `loop` manuel + `when` (plutôt qu'`until` strict)

Décision de conception prise après réflexion (voir section suivante) :
**`until`/`retries` seul ne suffit pas** ici, parce qu'il relance la
même tâche telle quelle, sans exposer de numéro de tentative
réutilisable pour faire varier la stratégie. On utilise donc un `loop`
manuel sur la liste des fenêtres de log, avec un `when` qui saute les
itérations suivantes dès que le diagnostic est jugé suffisant :

```yaml
vars:
  log_windows:
    - "tail -n 20 /var/log/messages-short"
    - "tail -n 100 /var/log/messages"
    - "tail -n 500 /var/log/messages"
  diagnostic_suffisant: false

tasks:
  - name: Boucle d'analyse avec fenêtre de log croissante
    block:
      - name: Extraire la fenêtre de log de cette tentative
        shell: "{{ item }}"
        register: log_extrait
        delegate_to: rh8102

      - name: Interroger le LLM avec sortie JSON forcée (prefill)
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
                  Voici un extrait de log : {{ log_extrait.stdout }}
                  Réponds STRICTEMENT en JSON avec deux clés :
                  "diagnostic_suffisant" (true/false) et "analyse" (texte).
              - role: assistant
                content: "{"
          status_code: 200
          return_content: yes
        register: llm_response

      - name: Parser la réponse et mettre à jour le statut
        set_fact:
          diagnostic_suffisant: "{{ ('{' + llm_response.json.content[0].text) | from_json | json_query('diagnostic_suffisant') }}"
          derniere_analyse: "{{ ('{' + llm_response.json.content[0].text) | from_json | json_query('analyse') }}"
    loop: "{{ log_windows }}"
    when: not (diagnostic_suffisant | bool)
```

Point clé pédagogique : le `when: not (diagnostic_suffisant | bool)`
fait exactement le travail de la boucle autonome — dès que le diagnostic
est jugé suffisant lors d'une itération, les itérations suivantes de la
liste sont **sautées** automatiquement, sans avoir à casser la boucle
manuellement. Compromis assumé : moins "pur" sémantiquement qu'un vrai
`until`, mais donne un accès direct à `item` (la fenêtre de log de cette
tentative précise) — impossible à faire proprement avec `until` seul.

## ✅ Parsing JSON fiabilisé par prefill (résolu)

Point qui restait ouvert dans une version précédente de ce design,
résolu grâce à la technique du **prefill** découverte en session : ajouter
un message `assistant` pré-rempli commençant par `{` force le modèle à
continuer directement en JSON, sans jamais pouvoir insérer une phrase
d'introduction avant. Note dans le YAML ci-dessus : comme le prefill
`{` n'est pas inclus dans le texte renvoyé par l'API, il faut le
**rajouter manuellement** avant de parser (`'{' + llm_response.json.content[0].text`),
sinon le JSON serait incomplet (il manquerait l'accolade ouvrante).

## ✅ Comment réajuster à chaque tentative (résolu)

Le `loop` sur `log_windows` (voir ci-dessus) résout directement ce qui
était identifié comme "le vrai enjeu à concevoir" — chaque itération
utilise une fenêtre de log différente (`item`), de plus en plus large,
au lieu de systématiquement répéter la même requête.

## Critère d'arrêt à définir clairement

- **Succès** : `diagnostic_suffisant: true` → le playbook affiche
  l'analyse finale et s'arrête normalement.
- **Échec après épuisement des tentatives** : après 3 tentatives sans
  succès, le playbook doit `fail` proprement avec un message clair
  ("diagnostic impossible après 3 tentatives, log probablement trop
  pauvre en information"), plutôt que de continuer silencieusement avec
  un résultat non fiable.

## Points restants à vérifier en codant (mineurs, pas structurels)

- Vérifier le comportement exact de `json_query` sur la structure
  imbriquée retournée (peut nécessiter un ajustement de syntaxe selon la
  version d'Ansible/jinja installée).
- Décider si le nombre de tentatives (3, via la longueur de
  `log_windows`) et les tailles de fenêtre de log sont fixes ou
  paramétrables via `group_vars`.
- Vérifier que `delegate_to: rh8102` fonctionne bien à l'intérieur d'un
  `block` en boucle (devrait être le cas, mais à confirmer à l'exécution).

## Compétences visées

- Boucles conditionnelles Ansible (`until`, `retries`, `delay`)
- Distinction concrète agent vs tool use, vécue plutôt que théorique
- Parsing de sortie structurée (JSON) générée par un LLM, avec gestion
  de la fiabilité de ce format
- Design d'un critère d'arrêt explicite (succès vs échec propre)
