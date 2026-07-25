# IA — Vague 3 (MLOps/Ops) : Tests automatisés spécifiques au ML

Session théorique partie d'un constat simple : un test classique
`assert résultat == valeur_attendue` ne fonctionne pas sur un système
basé sur des embeddings/LLM, à cause du double niveau d'incertitude
(approximation ANN côté récupération, génération probabiliste côté LLM).

## Type 1 — Assertions à seuil/statistiques, pas d'égalité stricte

Rappel du recall@k (`monitoring/33-...md`) : au lieu de vérifier une
égalité stricte, on vérifie un **seuil de tolérance** — "le recall@3
doit être ≥ 80%", pas "doit être exactement 100%".

## Type 2 — Régression continue, pas un test écrit une fois pour toutes

Un test de code classique reste vrai indéfiniment une fois écrit — la
fonction ne se dégrade jamais sans qu'on touche au code. Un test ML
doit être **rejoué en continu** (CI/CD, intervalle régulier, à chaque
déploiement), précisément parce que le comportement peut se dégrader
sans qu'aucune ligne de code ne change — le drift
(`monitoring/33-...md`).

## Type 3 — Tests adversariaux aux frontières, pas au "chemin heureux"

Écho direct de la calibration du guardrail sémantique
(`exercices/tp-securite/tp-securite-rag-mcp-guardrails-resultat.md`) :
le faux positif rencontré était **sémantiquement très proche** de la
vraie attaque — c'est justement cette proximité qui faisait confondre
les deux à un seuil naïf.

Un test de code classique vérifie des cas bien séparés (entrée valide
vs clairement invalide). Un test adversarial en ML doit spécifiquement
chercher les cas **à la frontière**, ceux qui ressemblent le plus à ce
qu'on veut détecter sans en être — c'est précisément là que les
systèmes probabilistes se trompent le plus souvent, pas sur des cas
évidents et éloignés.

## Type 4 — Non-régression sémantique + vérification factuelle ciblée

Scénario : modifier légèrement le prompt de génération de
`search_notes`, vérifier que ça n'a rien cassé, sans exiger une réponse
identique au mot près (impossible avec un LLM).

⚠️ Piège à éviter : tester uniquement par similarité sémantique globale
reproduirait le piège de la faithfulness (`monitoring/35-...md`) —
"Paris est la capitale de la France" vs "Lyon est la capitale de la
France" ont une similarité élevée malgré un fait faux. D'où la
combinaison de deux vérifications :
1. Similarité sémantique globale (structure/sujet cohérents)
2. **Vérification factuelle ciblée** — extraire les faits clés attendus
   et vérifier spécifiquement leur présence

Nuance sur quand utiliser quoi : pour un fait simple et binaire (une
date, une capitale), une vérification factuelle directe (comparaison à
une valeur de référence) suffit. Le **LLM-as-judge** devient utile
quand le "fait attendu" n'est pas une simple valeur à comparer, mais un
jugement nuancé ("le raisonnement est-il cohérent", "l'idée de X est-elle
bien capturée") — des critères qu'une simple égalité ou extraction ne
peut pas trancher mécaniquement.

## RAGAS — framework de référence pour ne pas réinventer la roue

Implémenter LLM-as-judge from scratch demande un travail conséquent
(prompts d'évaluation, gestion des cas limites, parsing, calibration).
**RAGAS** (Retrieval Augmented Generation Assessment) s'est imposé comme
référence open source pour l'évaluation RAG, avec 4 métriques
principales :
- **Faithfulness** — chaque affirmation est-elle inférable du contexte ?
- **Answer Relevancy** — la réponse adresse-t-elle la question posée ?
- **Context Precision** — proportion de documents récupérés réellement
  utiles
- **Context Recall** — les informations nécessaires ont-elles été
  récupérées ? (proche du recall@k déjà vu)

Autres frameworks du même écosystème : **DeepEval** (interface
pytest-like, orienté CI/CD), **TruLens** (tracing + évaluation
combinés), **LangSmith** (intégré à l'écosystème LangChain, déjà cité
dans `ecosysteme/27-...md`).

## Limites du LLM-as-judge — au-delà du paradoxe déjà identifié

En plus du paradoxe déjà vu (le juge est aussi un LLM faillible,
`monitoring/35-...md`), quatre limites concrètes supplémentaires :
- **Biais du modèle juge** — préférences stylistiques, favorise certains
  types de réponses
- **Coût à l'échelle** — évaluer des milliers d'exemples avec un modèle
  premium représente un vrai budget
- **Circularité potentielle** — utiliser le même modèle pour générer
  et évaluer peut masquer certains problèmes (le juge et le généré
  partagent les mêmes angles morts)
- **Variabilité** — contrairement aux métriques déterministes, les
  scores peuvent légèrement varier entre exécutions (écho direct de
  `generation-parametres/16-...md` — même à `temperature: 0`, pas de
  garantie absolue de reproductibilité bit à bit)

Bonne pratique recommandée : calibrer le juge contre un petit ensemble
évalué manuellement avant de lui faire confiance à grande échelle — et
documenter/versionner les prompts d'évaluation au même titre que le
code, un score n'ayant de sens que si l'on sait précisément comment il
a été calculé.

## Résumé — 4 types de tests ML

| Type | Remplace/complète | Principe |
|---|---|---|
| Seuil statistique | Égalité stricte | Tolérance mesurable (recall@k ≥ X%) |
| Régression continue | Test unique figé | Rejoué en boucle pour détecter le drift |
| Adversarial aux frontières | Test du chemin heureux | Cible les cas limites, pas les cas évidents |
| Non-régression sémantique + factuel/judge | Comparaison mot à mot | Similarité globale + vérification ciblée selon la nature du fait |

## Ressource externe

[LLM-as-a-Judge : définitions et exemples (Blent.ai)](https://blent.ai/blog/a/llm-as-a-judge)
— bon complément pratique : détaille le flux d'évaluation (préparation
du contexte → prompt d'évaluation → verdict → extraction du score),
des exemples de prompts d'évaluation concrets, et un tableau comparatif
métriques lexicales (BLEU/ROUGE) vs évaluation humaine vs LLM-as-judge.
