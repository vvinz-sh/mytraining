# IA — Carte de consolidation : le pipeline complet d'un LLM

Note de synthèse, faite après un moment de "trop d'infos séparées" — pour
voir que toutes les briques vues jusqu'ici (tokens, embeddings, couches,
attention, activation, logits, softmax, temperature/top-p) ne sont pas
des notions isolées, mais un seul et même processus qui s'enchaîne.

## La carte complète, dans l'ordre réel d'exécution

```
1. Texte d'entrée
   → découpé en tokens

2. Chaque token devient un vecteur (embedding)
   → + une info de position (positional embedding)

3. Ces vecteurs traversent plusieurs couches, répétées N fois
   → chaque couche fait deux choses :
      a) ATTENTION : chaque mot regarde les autres mots pertinents (Q/K/V)
      b) ACTIVATION : une non-linéarité qui permet d'abstraire progressivement
   → résultat : une compréhension de plus en plus riche du texte

4. À la fin, la dernière couche produit un score (logit) pour CHAQUE
   mot possible du vocabulaire

5. Ces scores sont transformés en probabilités (softmax)
   → puis filtrés/ajustés (temperature, top-p/top-k)
   → puis un seul mot est tiré/choisi

6. Ce mot choisi est rajouté au texte, et TOUT recommence à l'étape 1
   pour deviner le mot suivant
```

## Nom de la boucle : génération autorégressive

**Autorégressif** (autoregressive) = "auto" (par lui-même) + "régressif"
(qui se base sur ses propres sorties précédentes). Chaque nouveau mot est
généré en se basant sur tous les mots précédents, **y compris ceux que le
modèle vient tout juste de produire lui-même**. C'est le terme
technique standard utilisé dans toute documentation sur les LLM pour
désigner ce cycle génération → réinjection → régénération.

## Schéma interactif

Version graphique cliquable de cette carte, générée en session :
`pipeline_llm_schema_complet` (sauvegardée dans `ia-concepts/notes/rsc/`
à côté de `pipeline_rag_embedding_generation`) — 5 blocs (texte →
tokens vectorisés → couches empilées → logits/probabilités → token
choisi, avec boucle autorégressive), chaque bloc cliquable pour
rouvrir l'explication détaillée correspondante.

## Renvoi vers les notes détaillées de chaque étape

- Tokens, ML de base : `01-domaine1...` (RHEL, sans lien direct), voir
  plutôt les notes IA de la vague 1 pour tokens/prompt
- Embeddings, RAG : `07-recap-agent-rag-hallucination.md`,
  `pipeline_rag_embedding_generation` (schéma visuel)
- Couches, activation, non-linéarité : `05-reseaux-neurones-couches.md`,
  `06-fonction-activation-non-linearite.md`
- Génération token par token, logits, softmax, temperature :
  `16-generation-token-logits-softmax-temperature.md`
- top_k / top_p : `18-top-k-top-p.md`
- Multimodalité (patches, positional embedding) :
  `19-multimodalite-patches-positional-embedding.md`
- Attention (Q/K/V, multi-head) :
  `20-mecanisme-attention-qkv-multihead.md`

## Point d'étape

Cette carte n'ajoute aucune notion nouvelle — elle sert uniquement de
repère pour se relocaliser dans l'ensemble, si un futur sujet ("pourquoi
X fonctionne comme ça") redevient confus. Revenir à ce schéma en premier
réflexe avant de rouvrir une note détaillée spécifique.
