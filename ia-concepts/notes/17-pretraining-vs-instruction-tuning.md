# IA — Pré-entraînement vs fine-tuning d'instruction (pourquoi un LLM répond à une question)

Approfondissement transversal, né d'une question sur l'origine du texte
généré par un LLM.

## D'où vient "deviner le mot suivant" — la vraie tâche d'entraînement

Un LLM n'est jamais explicitement instruit "devine le mot suivant" dans
une conversation — c'est la tâche fondamentale sur laquelle il a été
entraîné, appliquée en continu à n'importe quel texte, y compris à toute
la conversation vue comme un seul long texte à continuer.

## Deux phases d'entraînement distinctes

**Phase 1 — Pré-entraînement** : le modèle lit d'énormes quantités de
texte brut d'internet (articles, forums, livres...) et apprend
uniquement à prédire le mot suivant, sans distinction de qualité. Dans ce
texte brut, le motif "Question : ... Réponse : ..." apparaît, mais
mélangé à des millions d'autres patterns (question suivie d'une autre
question, pas de réponse du tout, texte hors sujet...). Pas fiable à ce
stade seul pour produire des réponses systématiquement utiles.

**Phase 2 — Fine-tuning d'instruction (+ souvent RLHF)** : ré-entraînement
spécifique sur des milliers d'exemples soigneusement choisis, où le
motif "face à une question, produire une réponse utile et directe" est
délibérément **renforcé**, et les patterns non désirés (ignorer la
question, dévier, produire une autre question à la place) sont
**pénalisés**.

## Pourquoi la phase 2 est nécessaire (pas juste "plus de volume" en phase 1)

⚠️ Point clé, souvent mal compris : ce n'est pas une question de
"validation humaine en plus" au sens général — c'est une différence de
**nature du signal** appris.

Le pré-entraînement apprend uniquement ce qui est **statistiquement
fréquent** dans le texte brut — pas ce qui est **bon, utile ou
souhaitable**. Donner au modèle encore plus d'exemples Q/R tirés du même
internet brut non filtré lui ferait apprendre la distribution réelle des
réponses sur internet — qui inclut des réponses fausses, désagréables,
hors sujet ou de mauvaise qualité, mélangées aux bonnes (sur un forum
quelconque, toutes sortes de réponses coexistent sans distinction de
qualité).

La phase 2 n'ajoute pas "plus d'exemples du même genre" — elle ajoute un
type de signal **complètement absent** du pré-entraînement : un jugement
explicite de qualité ("cette réponse est bonne, celle-là est mauvaise"),
issu de vraies personnes évaluant les réponses. C'est cette distinction
**fréquence vs qualité** qui rend la deuxième phase indispensable, non
remplaçable par un simple ajout de volume à la phase 1.

## Résumé

```
Pré-entraînement (texte brut internet)
   → apprend la fréquence statistique des motifs de langage
   → "Q/R" est un motif parmi des millions d'autres, pas fiable seul

Fine-tuning d'instruction + RLHF (exemples évalués par des humains)
   → apprend un jugement de qualité absent du pré-entraînement
   → renforce spécifiquement "répondre utilement à une question"
   → rend ce comportement quasi systématique et fiable
```
