# TP — Interroger un LLM depuis Ansible : réalisé avec succès ✅

Complète `tp-ansible-llm.md` et `tp-ansible-llm-design.md`. Le TP a été
mené à bien de bout en bout.

## Environnement final utilisé

- Control node : WSL (Ubuntu), Ansible core 2.21, Python 3.12, venv `.py3`
- Target node : VM RHEL 8 (`rh8102`), réseau host-only, Python 3.11
  installé via AppStream pour compatibilité avec Ansible récent
- Fichier de log de test : `/var/log/messages-short` (extrait volontaire
  plutôt que le fichier complet, pour limiter les tokens envoyés)

## Bugs rencontrés et corrigés en cours de route

1. **`SyntaxError: from __future__ import annotations`** sur la target —
   Python 3.6 par défaut sur RHEL8 trop ancien pour les modules Ansible
   récents. Corrigé en installant `python3.11` via `dnf` et en pointant
   `ansible_python_interpreter` dessus dans l'inventaire.
2. **Appel API exécuté sur le mauvais host** — la tâche `uri` était dans
   le même play que la lecture du log (`hosts: target`), donc tentée
   depuis la VM host-only sans accès internet. Corrigé en séparant en
   deux plays distincts (`hosts: target` puis `hosts: localhost`), avec
   `hostvars['rh8102']['log_content']` pour transmettre la donnée entre
   les deux plays (plus simple qu'`add_host`, Ansible garde nativement en
   mémoire les `set_fact` de tous les hosts pendant l'exécution).
3. **Header `anthropic-version` manquant** — nécessaire en plus de
   `x-api-key`, sinon requête rejetée même avec une clé valide.
4. **`max_tokens: " {{ llm_max_tokens }}"`** — espace avant l'accolade
   transformait la valeur en chaîne `" 300"` au lieu d'un entier.
5. **Erreur 400 "credit balance too low"** — pas un bug technique : la
   clé API créée n'avait pas de crédit. A permis de valider que la
   vérification `status_code: 200` de la tâche `uri` fonctionnait
   correctement (échec propre du playbook plutôt qu'une erreur silencieuse).
   Résolu en créditant le compte sur la Console.

## Playbook final (structure)

```yaml
---
- name: Récupérer le log depuis la target
  hosts: target
  tasks:
    - name: Lire le contenu du fichier de log
      slurp:
        src: /var/log/messages-short
      register: log_raw
    - name: Décoder le contenu en base64 -> texte
      set_fact:
        log_content: "{{ log_raw.content | b64decode }}"

- name: Appeler l'API LLM depuis le control node
  hosts: localhost
  tasks:
    - name: Générer un résumé de log via l'API LLM
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
          max_tokens: "{{ llm_max_tokens }}"
          messages:
            - role: user
              content: "Résume ce log en 3 points : {{ hostvars['rh8102']['log_content'] }}"
        status_code: 200
        return_content: yes
      register: llm_response
      no_log: true
    - name: Vérifier que la réponse n'a pas été tronquée
      fail:
        msg: "Réponse tronquée par max_tokens"
      when: llm_response.json.stop_reason == "max_tokens"
    - name: Afficher le résumé généré
      debug:
        msg: "{{ llm_response.json.content[0].text }}"
```

## Résultat obtenu (exécution réelle)

Playbook exécuté avec succès (`ok=3` sur les deux hosts, `failed=0`), le
LLM a correctement résumé le contenu réel du log en 3 points cohérents
(activité Ansible, renouvellements DHCP, services système démarrés) — la
tâche de vérification `stop_reason` est passée en `skipping`, ce qui est
le comportement attendu en cas de succès (pas de troncature).

## Compétences pratiquées

- Module `uri` (POST, headers, `body_format: json`, `status_code`,
  `return_content`)
- Ansible Vault (création, chiffrement, exécution avec `--ask-vault-pass`)
- Partage de variables entre hosts via `hostvars`
- Architecture multi-host dans un même playbook (control node vs target,
  et pourquoi ça compte en environnement réseau restreint/host-only)
- Debug méthodique d'erreurs Ansible (lecture des messages d'erreur
  Python, erreurs HTTP, erreurs de typage YAML/Jinja)
