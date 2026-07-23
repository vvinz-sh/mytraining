# TP — Agent Ansible avec boucle autonome : réalisé avec succès ✅

Complète `tp-ansible-agent-boucle-draft.md`. Le TP a été mené à bien de
bout en bout, avec plusieurs vrais bugs rencontrés et corrigés en cours
de route — tous liés à des concepts déjà vus en théorie, maintenant
observés en conditions réelles.

## Scénario d'incident simulé

Log généré sur `rh8102` (`/var/log/messages-incident`, 520 lignes),
structuré pour matcher précisément 3 fenêtres d'analyse :
- `tail -n 20` : bruit générique seul (postfix/cron), aucune cause
  identifiable — **ambigu**
- `tail -n 100` : révèle le symptôme (httpd "No space left on device")
  — **partiellement suffisant**
- `tail -n 500` : révèle la cause racine (kernel EXT4 "No space left",
  backup-job qui sature le disque) — **cause racine claire**

Script de génération testé et validé avant utilisation (voir
`generate-incident-log.sh`).

## Bugs rencontrés et corrigés

### 1. `loop` non supporté directement sur un `block`

Erreur découverte par vérification (pas supposée) : Ansible ne supporte
pas `loop` directement sur un `block` — limitation connue, pas
implémentée nativement.

**Correction** : séparer la logique dans un fichier de tâches externe
(`analyser_fenetre.yml`), inclus via `include_tasks` (qui, lui, supporte
bien `loop`) depuis le playbook principal.

### 2. Assistant message prefill obsolète sur les modèles récents

Erreur API : `"This model does not support assistant message prefill.
The conversation must end with a user message."`

**Explication** : le prefill (technique enseignée en théorie plus tôt,
valable sur d'anciens modèles) a été **retiré comme fonctionnalité** sur
les modèles Claude récents (Sonnet 4.6, Opus 4.8, Fable 5) — un
changement cassant (breaking change) côté API.

**Correction, meilleure que l'ancienne solution** : les **Structured
Outputs** natifs (`output_config.format`), qui garantissent
mathématiquement (via décodage contraint pendant l'inférence, pas
juste une consigne dans le prompt) que la sortie respecte un schéma
JSON fourni :

```yaml
output_config:
  format:
    type: json_schema
    schema:
      type: object
      properties:
        diagnostic_suffisant: { type: boolean }
        analyse: { type: string }
      required: [diagnostic_suffisant, analyse]
      additionalProperties: false
```

Plus besoin de réinjecter manuellement un `{` avant de parser (comme
c'était nécessaire avec le prefill) — la sortie est directement du JSON
valide et complet.

Leçon retenue : même une technique bien vérifiée en théorie peut
devenir obsolète — l'esprit critique et la vérification (plutôt que
d'appliquer une recette apprise sans la questionner) restent essentiels,
API en constante évolution ou pas.

### 3. Troncature par `max_tokens` — illustration live d'un concept déjà vu

Sur la 2e tentative (`tail -100`), le diagnostic était plus long
(3 problèmes distincts identifiés) et a dépassé `max_tokens: 400` —
réponse coupée en plein milieu d'une phrase, JSON invalide
("Unterminated string").

**Correction** : `max_tokens` porté à 1024, consigne "2-3 phrases
maximum" ajoutée au prompt, et surtout une vérification `stop_reason`
**ajoutée avant le parsing** (qu'on avait omise dans le premier jet du
playbook) :

```yaml
- name: Vérifier que la réponse n'a pas été tronquée par max_tokens
  fail:
    msg: "Réponse tronquée (stop_reason={{ llm_response.json.stop_reason }})"
  when: llm_response.json.stop_reason == "max_tokens"
```

Bon exemple concret de pourquoi cette vérification, vue en théorie dans
le TP 1, n'est pas optionnelle — elle a directement expliqué un bug réel
rencontré ici, plutôt que de planter avec une erreur `from_json`
cryptique sans cause apparente.

## Résultat final obtenu

Après 3 tentatives (progression automatique `-20` → `-100` → `-500`,
sans validation humaine entre elles), le diagnostic final :

> La cause racine est un remplissage complet du système de fichiers
> /var : le job de backup a écrit 62 Go dans /var/backups sans
> nettoyage préalable, saturant la partition. Cette saturation a
> provoqué en cascade : un emballement de cron, l'échec du démarrage
> d'Apache, et des erreurs Postfix. L'archive incomplète laissée sur
> disque aggrave le problème.

Le modèle a reconstruit toute la **chaîne causale** (pas juste répété
les lignes de log), y compris un détail (l'archive incomplète qui
aggrave le problème) qui demandait de relier deux informations
distinctes du log.

## Ce que ce TP a démontré concrètement

- **Agent vs tool use** : boucle autonome réelle, progression
  automatique entre 3 stratégies (fenêtres de log croissantes), sans
  validation humaine — contrairement au TP 1 qui n'était qu'une seule
  action (tool use).
- **`max_tokens`/`stop_reason`** : la troncature n'est pas qu'un concept
  théorique — elle s'est produite réellement et a cassé le parsing,
  confirmant l'importance de la vérification systématique.
- **Structured Outputs > prefill** : la bonne pratique évolue avec l'API
  elle-même ; vérifier la doc à jour reste indispensable, même sur une
  technique qu'on croit maîtriser.
- **`include_tasks` > `block` pour boucler** : limitation Ansible
  concrète découverte en pratique, pas dans la documentation lue à
  l'avance.

## Compétences pratiquées

- `include_tasks` + `loop` (contournement de la limitation `block`)
- Structured Outputs de l'API Claude (`output_config.format`)
- Vérification `stop_reason` en contexte réel de bug
- Conception et génération d'un scénario de log réaliste et testé
- Debug méthodique d'un playbook Ansible multi-fichiers
