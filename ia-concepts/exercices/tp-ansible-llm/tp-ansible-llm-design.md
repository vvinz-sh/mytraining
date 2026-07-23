# TP — Interroger un LLM depuis un playbook Ansible : design complet

Statut : **prêt à démarrer**. Complète `tp-ansible-llm.md` (plan initial)
avec l'architecture, les prérequis techniques précis, et la structure de
projet.

## Architecture proposée

Deux rôles distincts, comme dans un vrai contexte pro :

```
[Control node]  --SSH-->  [Target node]
   Ansible                  génère/héberge les logs
   (ce qui exécute              (ex : une des VMs RHEL8
   le playbook, appelle          déjà montées pour RHCSA)
   l'API LLM)
```

- **Control node** : ta machine (laptop) ou une VM légère dédiée. C'est
  elle qui exécute `ansible-playbook`, lit le Vault, et fait l'appel HTTPS
  vers l'API.
- **Target node** : une VM RHEL 8 existante (réutilise une de tes VMs de
  labo RHCSA) qui contient un fichier de log d'exemple à résumer.

Ça permet de pratiquer un vrai scénario à deux machines plutôt qu'un
simple `localhost`, plus proche de ce que tu ferais en vrai.

## Prérequis matériels

Rien de lourd — aucune charge de calcul ne se fait localement (tout le
calcul du LLM est côté API, pas sur tes VMs) :

- **Control node** : 1 vCPU / 1 Go RAM suffit largement (juste
  Ansible + un appel HTTP).
- **Target node** : réutilise une VM RHCSA existante (2 vCPU / 2-4 Go RAM
  déjà en place), pas besoin de VM supplémentaire.

## Prérequis logiciels

**Système d'exploitation**
- Target node : RHEL 8 / Rocky / Alma 8 (déjà en place).
- Control node : n'importe quel Linux récent (y compris ton poste actuel)
  ou macOS — pas de contrainte RHEL ici.

**Ansible — version et point d'attention important**
RHEL 8 embarque Python 3.6 par défaut, trop ancien pour les versions
récentes d'Ansible (`ansible-core` ≥ 2.14 exige Python ≥ 3.9). Deux
options :
- Si le **control node** est ta machine perso (pas RHEL8), pas de souci,
  installe la dernière version normalement.
- Si tu veux exécuter Ansible **depuis** une VM RHEL8, installe Python 3.9+
  via AppStream (`dnf install python3.11`) et crée un environnement dédié
  plutôt que de dépendre du Python système.

Version recommandée : **ansible-core ≥ 2.15** (`pip install
ansible-core`), largement suffisant — le module `uri` est dans
`ansible.builtin`, aucune collection externe nécessaire.

**Vérifier la version installée**
```bash
ansible --version
python3 --version
```

**Paquets/modules Python**
- `requests` n'est pas nécessaire (le module `uri` gère lui-même les
  appels HTTP en interne).
- Aucune collection externe requise pour la version simple du TP (tout
  est dans `ansible.builtin` : `uri`, `slurp`, `copy`, `debug`, `fail`).

## Prérequis réseau

- **Control node** → accès sortant HTTPS (port 443) vers l'API
  (`api.anthropic.com` ou l'endpoint fourni par ta clé) — vérifie qu'aucun
  proxy/firewall interne ne bloque ça si le control node est une VM de
  labo isolée.
- **Control node** → **target node** : SSH classique (déjà en place pour
  tes VMs RHCSA).

## Sécurité — gestion de la clé API

```bash
ansible-vault create group_vars/all/vault.yml
```
Contenu :
```yaml
vault_llm_api_key: "ta-clé-ici"
```
Ne jamais committer `vault.yml` en clair dans `mytraining` — soit vault
chiffré, soit exclu via `.gitignore` si tu préfères ne pas versionner du
tout les secrets, même chiffrés.

## Structure de projet suggérée

```
tp-ansible-llm/
├── inventory.ini
├── group_vars/
│   └── all/
│       ├── vars.yml          (non sensible : URL API, modèle utilisé)
│       └── vault.yml         (chiffré : clé API)
├── playbook.yml
└── templates/
    └── resume.j2             (mise en forme du résumé final)
```

`inventory.ini` minimal :
```ini
[target]
rhel8-lab ansible_host=<IP de ta VM RHCSA>

[control]
localhost ansible_connection=local
```

## Étapes du playbook (reprises et affinées)

1. Sur le **target**, lire le fichier de log d'exemple (module `slurp`
   ou `fetch` pour le rapatrier sur le control node).
2. Sur le **control node**, appeler l'API via `uri` avec le contenu du
   log en `content` du message, clé API tirée du Vault.
3. Vérifier `status_code == 200` et `stop_reason != "max_tokens"`,
   `fail` sinon.
4. Rendre le résumé lisible via un template Jinja2 (`templates/resume.j2`)
   et l'écrire sur le control node avec `copy`/`template`.
5. (Optionnel, si le crédit API le permet) Boucler avec `loop` sur
   plusieurs fichiers de logs, avec un `delay`/`retries` pour respecter
   un éventuel rate-limit.

## Point d'attention avec ta clé actuelle (sans crédit)

Le premier test réel te renverra probablement une erreur de facturation
(status 400/402 selon l'API) plutôt qu'un vrai résumé — c'est attendu et
même utile : ça te permet de valider que l'étape 3 (vérification
`status_code`) fonctionne bien avant même d'avoir un compte crédité.
