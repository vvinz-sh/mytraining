# IA — Mécanique de génération : logits, softmax, temperature

Premier point de la vague 2 (paramètres de génération).

## Étape 1 — Un score par mot possible (logits)

Le modèle ne "choisit" pas un mot directement. La couche de sortie
produit un **score brut (logit)** pour **chaque token possible** du
vocabulaire (souvent 50 000 à 100 000+ tokens) — à chaque étape de
génération, des dizaines de milliers de scores calculés d'un coup.

Exemple pour compléter "Le chat dort sur le ___" (scores inventés) :
- "canapé" → 9
- "tapis" → 7
- "toit" → 3
- "réfrigérateur" → -2

## Étape 2 — Softmax : transformer les scores en probabilités

Le **softmax** convertit ces logits bruts (potentiellement négatifs,
sans somme fixe) en une vraie distribution de probabilités (tous
positifs, somme = 100%) :
- "canapé" → 70%
- "tapis" → 25%
- "toit" → 4%
- "réfrigérateur" → ~0%

Le score le plus haut devient la probabilité la plus forte, mais aucun
token n'est totalement éliminé — chacun garde une chance non nulle.

## Étape 3 — `temperature` : comment on choisit parmi ces probabilités

La `temperature` divise les logits **avant** le softmax :
- **Proche de 0** → amplifie les écarts entre logits → après softmax, le
  token le plus probable écrase presque totalement les autres → choix
  quasi déterministe (toujours "canapé" dans l'exemple).
- **Élevée (>1)** → aplatit les écarts → probabilités plus proches les
  unes des autres → tirage au sort pondéré, plus de chance qu'un token
  "moins évident" (ex : "tapis") soit choisi.

Analogie : une roue de loterie où chaque mot occupe une portion de la
roue proportionnelle à sa probabilité. `temperature: 0` = toujours le
plus gros morceau. `temperature` élevée = vrai tirage au sort pondéré,
avec un mélange de résultats sur plusieurs essais.

## Étape 4 — Génération autorégressive (un mot à la fois)

Une fois un token choisi, il est **ajouté** à la suite du texte, et tout
le processus (calcul des logits → softmax → choix selon la temperature)
**recommence depuis le début** pour le token suivant, en tenant compte
du nouveau token ajouté.

Point clé : le mot choisi (même si issu d'un tirage au sort à
`temperature` élevée, donc pas forcément le plus probable) fait
**définitivement partie du contexte** pour la suite. Le modèle ne peut
jamais "revenir en arrière" ou effacer un choix passé — chaque nouveau
mot dépend de tout ce qui précède, y compris ses propres choix
antérieurs, même si un choix s'avère être une mauvaise idée quelques
mots plus tard.

## Plage de valeurs — dépend du fournisseur

- **Anthropic (API Claude)** : `temperature` va de **0 à 1**, maximum
  plus restreint que d'autres fournisseurs. Impossible de dépasser 1.
- **OpenAI et Gemini**, à titre de comparaison : plage de **0 à 2** — ne
  pas réutiliser machinalement une valeur comme `1.5` en changeant pour
  l'API Claude, elle serait rejetée.

### ⚠️ `temperature: 0` n'est pas un déterminisme garanti à 100%

Même à `temperature: 0`, la réponse n'est **pas garantie identique au bit
près** d'une exécution à l'autre. Anthropic le précise dans sa propre
documentation : à cause de subtilités d'arithmétique en virgule flottante
sur GPU et du traitement par lots des requêtes, deux exécutions à
`temperature: 0` peuvent très rarement diverger légèrement.

`temperature: 0` donne une **quasi-déterminisme** (identique l'immense
majorité du temps), pas une garantie cryptographique absolue — à garder
en tête pour tout pipeline qui supposerait une reproductibilité parfaite
bit à bit.

## `temperature` en pratique — paramètre d'inférence, pas d'entraînement

C'est un paramètre qu'on règle **à chaque appel de l'API**, exactement
comme `max_tokens` vu dans le TP Ansible :

```json
{
  "model": "...",
  "max_tokens": 300,
  "temperature": 0,
  "messages": [...]
}
```

**Combien de fois on le définit** : à chaque requête, sans mémoire entre
deux appels. Rien n'empêche de faire un appel avec `temperature: 0` puis,
juste après, un autre appel avec `temperature: 1` pour une tâche
différente, avec le même modèle. Sans valeur précisée, l'API applique une
valeur par défaut (souvent autour de 1 selon les fournisseurs) — ne pas
préciser `temperature` ne veut donc pas dire "déterministe strict".

**Quand vouloir 0 vs 1, avec des exemples concrets** :
- `temperature: 0` → réponse la plus prévisible/reproductible : générer
  du code, extraire des données structurées d'un log (le TP Ansible),
  répondre à une question factuelle précise, classer un ticket dans une
  catégorie fixe.
- `temperature: 1` (ou plus) → variété/créativité recherchée :
  brainstorming d'idées, écriture créative, générer plusieurs variantes
  d'un même message à tester.

### ⚠️ Clarification importante — la temperature ne change jamais le type de tâche

La `temperature` ne fait que **choisir différemment parmi les mots
plausibles à chaque étape** — elle ne transforme jamais la nature de ce
qui est demandé. Un prompt "résume ce log en 3 points" avec
`temperature: 1` continuera à produire un résumé en 3 points (parce que
c'est ce que le contexte rend le plus probable à chaque étape) — la
variation se limite au choix des mots ou à l'ordre de présentation, pas à
un changement de sujet ou de format complètement hors contexte (ex : pas
de risque de "poème" à la place d'un résumé technique, quelle que soit la
temperature).

Analogie : la temperature est le niveau de hasard **dans les limites de
ce que le contexte rend plausible** — elle élargit ou réduit le champ des
choix parmi des options déjà cohérentes avec la demande, elle n'ouvre
jamais la porte à des choix complètement hors sujet.

### Exercice pratique à tester (à faire plus tard)

Relancer le playbook Ansible du TP (`tp-ansible-llm`) plusieurs fois avec
`temperature: 0`, puis plusieurs fois avec `temperature: 1`, et comparer
si les résumés varient (mots différents, ordre des points) ou restent
identiques d'une exécution à l'autre.

## Récap du cycle complet

```
Texte jusqu'ici
   → logits (un score par token du vocabulaire)
   → softmax (scores → probabilités, somme = 100%)
   → choix selon temperature (déterministe ou tirage pondéré)
   → un token ajouté au texte
   → on recommence pour le token suivant
```

C'est le mécanisme fondamental de génération de n'importe quel LLM,
appliqué en continu, y compris pour générer cette note elle-même.
