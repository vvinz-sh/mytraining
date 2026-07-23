# IA — Modèles Claude (tokens, context window, effort) + exercices récap

## Gamme de modèles (compromis intelligence / vitesse / coût)

Fable 5 = le plus capable, Opus 4.8 = raisonnement difficile, Sonnet =
équilibre quotidien, Haiku 4.5 = le plus rapide/économique. Plus un modèle
est "haut de gamme", plus il coûte cher et raisonne profondément ; les
modèles plus légers sont plus rapides et moins chers.

| Modèle | Fenêtre de contexte | Sortie max | Repère tarif |
|---|---|---|---|
| Haiku 4.5 | 200k tokens | plus limité | le moins cher |
| Sonnet 5 | 1M tokens | 128k tokens | équilibre |
| Opus 4.8 | 1M tokens | 128k tokens | premium |
| Fable 5 | 1M tokens | 128k tokens | le plus cher |

## Le paramètre "effort" — deux leviers indépendants

- **Changer de modèle** = changer la capacité brute du modèle (un cerveau
  différent, un plafond d'intelligence différent).
- **Changer l'effort** (Opus/Sonnet récents) = garder le même modèle mais
  lui laisser plus ou moins de "temps de réflexion interne" (tokens de
  raisonnement) avant de répondre.

⚠️ Correction importante : augmenter l'effort ne coûte pas juste plus de
**temps**, ça coûte aussi plus **cher** — un effort plus élevé génère
davantage de tokens de raisonnement interne, et ces tokens sont facturés
comme les autres. Effort élevé = plus lent **et** plus cher, jamais l'un
sans l'autre.

Ce sont deux axes indépendants : on peut combiner (ex. Opus effort bas vs
Sonnet effort max) — pas un seul curseur linéaire "meilleur → moins bon".

## Sur l'entraînement (point resté volontairement flou)

Anthropic ne publie pas le détail exact de l'entraînement de chaque
modèle. Règle générale seulement : un modèle plus capable est associé à
plus de paramètres, plus de données d'entraînement, plus de calcul — mais
le **mécanisme** d'apprentissage lui-même reste à voir dans le prochain
module (ML vs programmation classique).

## Exercices récapitulatifs

**1. Effort vs modèle** — Tâche de tri automatique d'emails (simple,
répétitif, gros volume) → **Haiku effort bas**. Tolérance d'erreur élevée,
pas besoin de raisonnement profond, volume élevé = priorité vitesse/coût.

**2. Context window dépassé** — Document de 500k tokens sur un modèle à
200k tokens de fenêtre. Le modèle ne sait **jamais** découper lui-même un
contexte trop long automatiquement. Deux issues possibles :
   - Rejet pur et simple de la requête (erreur).
   - Découpage géré par l'application *autour* du modèle (chunking, ou
     RAG pour ne sélectionner que les passages pertinents) — un choix fait
     par le développeur, pas un comportement automatique du système.
   (Passer à un modèle à 1M tokens est une solution stratégique valable
   dans ce cas précis, mais c'est un choix humain en amont, pas quelque
   chose qui se déclenche tout seul.)

**3. Classification automatisation / tool use / agent / RAG**
   - Cron qui purge les logs >30 jours chaque nuit → **automatisation
     classique** (règle fixe, zéro raisonnement).
   - Recherche des 5 tickets Jira les plus pertinents parmi 50 000 avant
     de répondre → **RAG** (retrieval par similarité avant réponse).
   - Système qui consulte les logs → diagnostique → ouvre un ticket →
     notifie → vérifie → clôture si résolu tout seul → **agent**
     (enchaînement autonome multi-étapes avec boucle de vérification).

## À venir

- [ ] Machine Learning vs programmation classique
- [ ] Réseaux de neurones — intuition (poids, activation, entraînement)
- [ ] Prompting — bonnes pratiques, few-shot, limites
- [ ] Usage pratique — appeler une API LLM depuis un script
