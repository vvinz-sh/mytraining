# IA — Usage pratique : appeler une API LLM depuis un script

## Appel de base (curl)

```bash
curl https://api.example.com/v1/messages \
  -H "x-api-key: $API_KEY" \
  -H "content-type: application/json" \
  -d '{
    "model": "un-modele",
    "max_tokens": 200,
    "messages": [
      {"role": "user", "content": "Résume ce texte en une phrase : ..."}
    ]
  }'
```

## Le paramètre `max_tokens` — ce qu'il fait vraiment

Il limite la taille de la réponse générée. Point important : si la
réponse aurait naturellement besoin de plus de tokens, elle n'est **pas**
refusée ni recommencée — elle est **tronquée brutalement**, potentiellement
en plein milieu d'une phrase, d'un mot, ou d'un JSON/code généré, sans que
le modèle "sache" qu'il va être coupé.

Les API exposent en général un champ (`stop_reason` ou équivalent) qui
indique si la réponse s'est terminée naturellement ou a été coupée par la
limite `max_tokens`. Bonne pratique : toujours vérifier ce champ avant de
traiter la réponse comme fiable, surtout si on parse du JSON ou du code
généré à partir de la sortie.

## Intégration dans un playbook Ansible — module `uri`

Pourquoi `uri` plutôt que `command`/`shell` + `curl` :
- `curl` retourne un code de sortie `0` même sur une erreur HTTP (404,
  500...) sauf avec `--fail` explicite → un playbook en `shell` penserait
  que tout s'est bien passé alors que l'API a rejeté la requête.
- Parsing JSON manuel nécessaire (`from_json`, jq...) avec `shell`, alors
  que `uri` + `body_format: json` + `return_content: yes` donne la réponse
  déjà parsée.
- Échappement de guillemets fragile et source d'injection en passant du
  JSON dans une commande shell, vs passer des dictionnaires Ansible/Jinja
  directement avec `uri`.
- `uri` gère nativement headers, timeout, retries, et expose le vrai code
  de statut HTTP dans une variable exploitable avec `failed_when`.

### Exemple de tâche

```yaml
- name: Générer un résumé de log via l'API LLM
  uri:
    url: https://api.example.com/v1/messages
    method: POST
    headers:
      x-api-key: "{{ llm_api_key }}"
      content-type: application/json
    body_format: json
    body:
      model: un-modele
      max_tokens: 300
      messages:
        - role: user
          content: "Résume ce log en 3 points : {{ log_content }}"
    status_code: 200
    return_content: yes
  register: llm_response

- name: Vérifier que la réponse n'a pas été tronquée
  fail:
    msg: "Réponse tronquée par max_tokens"
  when: llm_response.json.stop_reason == "max_tokens"
```

Ce pattern (appel + vérification du `stop_reason` + `fail` conditionnel)
permet d'échouer proprement le playbook plutôt que de continuer avec une
réponse potentiellement incomplète.

## À venir (module IA)

- [ ] RAG / fine-tuning — approfondissement (quand utiliser quoi)
- [ ] Limites et biais — hallucinations, sur-confiance, quand ne pas
      faire confiance au modèle
