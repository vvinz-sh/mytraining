# IA — Logging structuré pour des appels LLM

Complète `33-monitoring-evaluation-drift-recall.md` et
`35-faithfulness-groundedness-llm-as-judge.md` — ici, la donnée brute à
capturer en amont de toute évaluation, pas l'évaluation elle-même.
Construite en reconstruisant, à partir des frictions concrètes du TP
LLM local (troncature silencieuse, confusion sur la config de
génération utilisée), ce qu'un log structuré aurait dû capturer dès le
départ.

## Texte libre vs structuré

Un log classique (syslog) est une phrase libre :
`Jul 21 09:47:45 rh8102 sshd[9981]: Accepted publickey...` — lisible
par un humain, mais coûteux à interroger en masse (il faut parser du
texte). Le logging structuré (généralement JSON) remplace la phrase
par des **champs nommés**, directement filtrables/agrégables par un
outil comme Logstash/Elasticsearch, sans parsing de texte libre.

## Les champs de base pour un appel LLM

Reconstruits à partir de frictions réelles rencontrées ce soir :

- **`tokens_entree`** — dépassement silencieux de `num_ctx` (Phase 1)
  et écart massif de comptage entre tokenizers GGUF/HF (bug 12, Phase
  3) auraient été visibles immédiatement avec ce champ tracé
- **`tokens_sortie`** — combiné à `max_tokens`/`max_new_tokens`, permet
  de repérer une troncature en comparant les deux valeurs
- **`temps_execution_s`** — la variance qu'on a observée (17s/it à
  123s/it, expliquée par le padding-free) aurait été immédiatement
  visible sur un graphique plutôt qu'à l'œil sur la console
- **`finish_reason`** — pourquoi la génération s'est arrêtée :
  - `stop` : le modèle a produit son token de fin naturellement
    (`eos_token_id`, ex. `<|im_end|>` = 151645 pour Qwen3)
  - `length` : coupé par la limite de tokens de sortie
  - `content_filter` : bloqué par un garde-fou de sécurité
  - `tool_calls` : arrêt pour invoquer un outil

⚠️ Ne pas confondre `finish_reason` (pourquoi le **modèle** a arrêté de
générer) avec un code d'erreur **transport** (ex : HTTP 499 rencontré
ce soir sur un timeout SSH bloquant) — deux couches différentes du
pipeline, à ne pas loguer dans le même champ.

## Diagnostic croisé — un exemple concret construit en session

Si `finish_reason: "length"` grimpe soudainement dans les logs (ex :
2% → 40% des appels), deux causes possibles, distinguables **sans
calcul complexe**, juste en croisant avec `tokens_entree` :

- **`tokens_entree` en hausse en même temps** → cohérent, les requêtes
  entrantes sont devenues plus lourdes (ex : utilisateurs qui collent
  des documents plus longs) — pas un problème de modèle
- **`tokens_entree` stable, mais `length` grimpe quand même** →
  suspect, pointe vers un changement de comportement du modèle
  lui-même (nouveau déploiement, dérive, fine-tuning qui l'a rendu
  plus verbeux) — le genre de signal qui aurait permis de repérer plus
  vite un souci comme celui rencontré en Phase 3

Un ratio calculé (tokens sortie / tokens entrée) n'apporte rien de
plus ici — les deux champs bruts, simplement posés côte à côte dans le
temps, suffisent à trancher.

## Champs stables vs champs de détail — la structure qui dure dans le temps

Piège identifié en session : si chaque paramètre de génération
(`do_sample`, `repetition_penalty`, `no_repeat_ngram_size`...) est logué
comme un champ de premier niveau, à plat, la structure du log **casse**
dès qu'un paramètre est ajouté ou retiré d'un run à l'autre — rendant
la comparaison entre logs anciens et récents fragile.

**Solution** : séparer clairement deux catégories de champs.

```json
{
  "model": "qwen3-4b-logs-lora-final",
  "tokens_entree": 3267,
  "tokens_sortie": 187,
  "temps_execution_s": 4.2,
  "finish_reason": "stop",
  "params_generation": {
    "do_sample": false,
    "repetition_penalty": 1.3
  }
}
```

- **Champs de premier niveau, à plat** (`tokens_entree`,
  `tokens_sortie`, `temps_execution_s`, `finish_reason`) : stables dans
  le temps, présents dans tous les cas — ce sur quoi on veut filtrer et
  agréger souvent (dashboards, alertes).
- **Sous-objet groupé** (`params_generation`) : nom du champ parent
  fixe, contenu variable — du contexte de détail utile pour
  investiguer un cas précis une fois qu'un filtre sur les champs plats
  y a déjà mené, pas structurant pour une vue d'ensemble.

## Résumé

1. Le logging structuré remplace la phrase libre par des champs
   nommés, directement interrogeables sans parsing de texte
2. 4 champs de base suffisent pour un appel LLM : tokens entrée/sortie,
   temps d'exécution, `finish_reason`
3. `finish_reason` (couche modèle) ≠ code d'erreur transport (couche
   réseau) — deux informations différentes, pas à mélanger
4. Croiser deux champs simples (`tokens_entree` + `finish_reason`)
   suffit souvent à distinguer deux causes d'un même symptôme, sans
   calcul complexe
5. Séparer champs stables à plat (premier niveau, pour filtrer/agréger)
   et champs de détail groupés (sous-objet, pour investiguer) —
   garantit une structure de log qui reste comparable dans le temps
   même quand le détail change

## Lien avec les notes existantes

`33-monitoring-evaluation-drift-recall.md`,
`35-faithfulness-groundedness-llm-as-judge.md` (l'évaluation qui
consomme ces logs), `tp-llm-local-phase1-resultat.md` (troncature
silencieuse, débriefée avec `OLLAMA_DEBUG=1`/`--verbose`),
`tp-llm-local-phase3-resultat.md` (confusion sur la config de
génération exacte utilisée, ayant motivé `params_generation`).
