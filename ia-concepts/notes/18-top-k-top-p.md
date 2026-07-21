# IA — Paramètres de génération : top_k et top_p

Suite de `16-generation-token-logits-softmax-temperature.md`. Même
famille de paramètres (agissent au moment du choix parmi les
probabilités), mais mécanismes différents de `temperature`.

## Rappel du contexte (même exemple)

"Le chat dort sur le ___" — après softmax :
- "canapé" → 70%
- "tapis" → 25%
- "toit" → 4%
- "réfrigérateur" → ~0,9%
- ... des milliers d'autres mots avec des probabilités minuscules

## `top_k` — nombre fixe de candidats

`top_k: 2` = ne garder que les **2 mots les plus probables**, ignorer
totalement tous les autres, même s'ils avaient une petite chance non
nulle. Ici : seuls "canapé" et "tapis" restent en lice, "toit" et
"réfrigérateur" sont exclus du tirage.

`top_k: 1` = un seul candidat possible, donc toujours choisi — même
résultat final que `temperature: 0` (déterminisme), mais par un
mécanisme différent :
- `temperature: 0` **écrase** les probabilités des autres tokens sans
  les retirer de la liste.
- `top_k: 1` **supprime physiquement** tous les autres tokens de la
  liste des candidats, avant même de regarder leurs probabilités.

Les deux paramètres se ressemblent à `k=1`, mais divergent dès qu'on
monte au-dessus de 1.

Point important : `top_k`/`top_p` sont, comme `temperature`, des
**paramètres d'inférence uniquement** — réglés à chaque appel API, sans
mémoire entre les appels, aucun lien avec l'entraînement ou les poids du
modèle.

## `top_p` — seuil de probabilité cumulée (nucleus sampling)

Au lieu d'un nombre fixe de candidats, `top_p` garde **juste assez de
mots pour atteindre un seuil de probabilité cumulée** (souvent 0.9 ou
0.95).

Exemple : avec `top_p: 0.95` sur notre distribution, "canapé" (70%) +
"tapis" (25%) = 95% pile → ces deux mots suffisent, le reste est exclu.

### Pourquoi top_p s'adapte, contrairement à top_k (fixe)

`top_p` **s'adapte automatiquement** à la forme de la distribution :
- Quand le modèle est **très confiant** (distribution très inégale, ex :
  70%/25%/4%...) → `top_p` garde naturellement **peu** d'options.
- Quand le modèle est **incertain** (distribution plus étalée, ex :
  30%/25%/20%/15%/8%...) → `top_p` garde **plus** d'options pour
  atteindre le même seuil de 95% (ici, il faudrait 5 mots).

`top_k` fixe, lui, garderait le même nombre de candidats peu importe si
le modèle était sûr ou hésitant — il ne s'ajuste jamais à la "forme" de
l'incertitude du modèle, contrairement à `top_p`.

## Pourquoi ne pas combiner `temperature` et `top_p`/`top_k` en même temps

Ordre des opérations dans le cycle de génération :
```
logits → temperature (modifie les probabilités elles-mêmes)
       → top_p / top_k (filtre les candidats à partir de ces probabilités déjà modifiées)
       → tirage au sort final
```

Problème si on ajuste les deux en même temps : ils agissent **en
cascade sur la même donnée**, et leurs effets s'entremêlent de façon
difficile à prévoir. Exemple : baisser `temperature` (resserre les
probabilités) **et** resserrer `top_p` (garde peu de candidats) cumule
deux mécanismes allant dans la **même direction** (moins de diversité) —
impossible de savoir ensuite lequel des deux réglages est responsable du
résultat, ni lequel ajuster si le résultat ne convient pas.

**Recommandation pratique** : choisir **un seul levier**, laisser l'autre
à sa valeur par défaut. `temperature` seule suffit dans l'immense
majorité des cas ; `top_p`/`top_k` restent des outils plus fins, réservés
à des cas avancés (recherche, contrôle très précis de la diversité) où
l'on sait précisément pourquoi ce contrôle supplémentaire est nécessaire.

## Récap de la famille de paramètres (temperature, top_k, top_p)

| Paramètre | Mécanisme | Effet |
|---|---|---|
| `temperature` | Modifie les probabilités elles-mêmes (avant filtrage) | Resserre ou étale la distribution |
| `top_k` | Filtre à un nombre **fixe** de candidats | Rigide, ignore la forme de la distribution |
| `top_p` | Filtre par seuil de probabilité **cumulée** | S'adapte à la confiance du modèle (peu de candidats si sûr, plus si incertain) |

Bonne pratique : ajuster un seul de ces trois paramètres à la fois.
