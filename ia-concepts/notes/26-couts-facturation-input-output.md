# IA — Coûts et facturation : pourquoi l'output coûte plus cher que l'input

Dernier point de la section "paramètres et fonctionnement pratique" de
la vague 2 — section maintenant complète.

## Le constat de base

Sur l'API Claude, les tokens **input** (envoyés) et **output** (générés)
n'ont pas le même prix — l'output coûte généralement plusieurs fois plus
cher que l'input, à quantité égale de tokens (ordre de grandeur : ~5x
plus cher pour Sonnet, à titre d'exemple).

## Pourquoi — écho direct avec la génération autorégressive

**Tokens d'entrée** : le modèle traite **tout le prompt en un seul
passage parallèle** — toutes les couches (attention comprise) sont
calculées une seule fois sur l'ensemble du texte d'entrée, même sur
10 000 tokens. Lourd, mais fait **une seule fois**.

**Tokens de sortie** : rappel de la génération autorégressive (voir
`16-generation-token-logits-softmax-temperature.md`) — chaque nouveau
token nécessite de **repasser à travers tout le modèle** (toutes les
couches, toute l'attention sur le contexte accumulé), puis ce token est
ajouté et **tout recommence** pour le token suivant. Générer 100 tokens
de sortie = **100 passages complets** à travers tout le modèle, chacun
un peu plus coûteux que le précédent (le contexte s'accumule), pas un
calcul fait une fois pour 100 tokens comme pour l'entrée.

C'est cette **redondance de passages complets** pour chaque token de
sortie qui explique le tarif plus élevé — pas simplement "un calcul de
probabilité en plus" (qui existe mais n'est pas le point coûteux).

## Ce qui détermine le coût réel d'une tâche : le produit volume × tarif

Le coût total dépend du **produit** volume × tarif pour chaque
catégorie, pas juste du tarif unitaire.

### Cas 1 — beaucoup à lire, peu à écrire (résumé de document)

Document de 50 000 tokens en entrée → résumé de 200 tokens en sortie.
Même avec un ratio de prix de ~1 pour 5, un volume 250 fois plus grand
(50 000 vs 200) fait que l'**input domine largement** le coût total,
malgré son tarif plus bas.

### Cas 2 — peu à lire, beaucoup à écrire (génération de code/contenu long)

Exemple : "crée-moi un site web complet" — quelques dizaines de tokens
en entrée, potentiellement des milliers de tokens en sortie (tout le
code généré). Ici, c'est l'**output qui domine** le coût total, malgré
son tarif plus élevé, parce que le volume généré est énorme comparé à
l'entrée minuscule.

## Résumé pratique

Le coût réel d'une tâche n'est jamais déterminé par le tarif unitaire
seul — il faut regarder **quel côté (input ou output) a le plus gros
volume** pour ce type de tâche précis :
- Beaucoup à lire, peu à écrire → coût dominé par l'input
- Peu à lire, beaucoup à écrire → coût dominé par l'output

## Section "paramètres et fonctionnement pratique" — vague 2 complète ✅

Avec cette note, les 5 points de cette section sont désormais tous
couverts : fenêtre de contexte (compaction), paramètres de génération
(temperature/top_p/top_k), multimodalité, guardrails, coûts/facturation.

## À venir (vague 2)

- [ ] Outils de l'écosystème (LangChain, bases vectorielles, no-code, MCP...)
