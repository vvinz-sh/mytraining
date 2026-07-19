# IA — Session récap général (agent, RAG, hallucination, critère de sélection)

Séance de questions croisées sur l'ensemble du module IA vu jusqu'ici,
pour consolider avant de poursuivre.

## Piège 1 — Agent vs action ponctuelle qui s'arrête

Scénario : un outil qui, face à une alerte, va chercher automatiquement
les 5 incidents passés les plus similaires (RAG) avant de proposer un
diagnostic, **puis s'arrête et attend validation humaine**.

→ Ce n'est **pas** un agent, malgré l'automatisation impliquée. Le fait de
s'arrêter pour validation est un signal fort d'exclusion : un agent
enchaîne plusieurs étapes **en autonomie, sans validation humaine à
chaque pas**, en boucle jusqu'à l'objectif. Ici il y a une seule action
composite (retrouver + diagnostiquer), pas une boucle autonome.

→ C'était du **RAG** (recherche des tickets similaires) combiné à une
génération ponctuelle — mais pas un agent.

## Piège 2 — Embedding vs génération (étape C du pipeline RAG)

Rappel du pipeline avec un exemple à 4 propositions :
- Convertir chaque document en vecteur → **embedding**
- Comparer les vecteurs et garder les plus proches → **recherche par
  similarité**
- Générer un texte de diagnostic à partir des documents récupérés →
  **génération**, étape complètement différente, **pas de l'embedding**
  (aucun vecteur impliqué à ce stade, c'est le LLM qui produit du texte
  normal une fois les documents injectés dans son contexte)
- Trier par ordre alphabétique → rien à voir avec RAG (tri mécanique,
  aucune notion de sens)

## Piège 3 — Biais de dataset vs mauvais retrieval au runtime

Question : si le RAG récupère des documents peu pertinents (similarité de
surface seulement), quel est le risque pour le diagnostic généré ?

→ Ce n'est **pas** du biais de dataset. Le biais de dataset se fixe **à
l'entraînement** du modèle (poids mal réglés de façon permanente, comme le
chat blanc/noir). Ici le modèle n'est pas en cause — le problème est **à
l'exécution (runtime)**, dans l'étape de retrieval : documents peu
pertinents malgré une similarité de surface.

→ Risque concret : le LLM va quand même essayer de produire un diagnostic
cohérent à partir de mauvais matériau, et peut **forcer des connexions qui
n'existent pas** — un diagnostic qui sonne confiant et précis mais faux ou
trompeur. C'est un des mécanismes qui alimente l'**hallucination** : le
modèle ne dit pas "je ne sais pas", il génère quelque chose de plausible
à partir de ce qu'on lui a donné, même si c'est du bruit.

→ D'où l'importance, dans un vrai système RAG, de soigner la qualité du
retrieval (seuil de similarité minimum, rejet si rien n'est assez proche).

## Piège 4 — Le vrai critère RAG vs envoi direct dans le contexte

Scénario : résumer 200 comptes-rendus (~2000 mots chacun) pour en sortir
les causes racines **les plus fréquentes**. Le tout tient dans 1M tokens
de contexte.

Intuition de départ ("ça rentre dans la fenêtre donc pas besoin de RAG")
→ vraie mais **incomplète**. Le vrai critère décisif n'est pas seulement
"est-ce que ça rentre" mais **est-ce que la tâche a besoin de voir
l'exhaustivité, ou seulement d'un sous-ensemble pertinent**.

Ici, compter des **fréquences** exige de voir tous les 200 comptes-rendus
— sélectionner un sous-ensemble (même bien choisi via RAG) fausserait
mécaniquement les statistiques : on perdrait la notion de "combien de
fois" au profit de juste "quels types de cause existent".

→ Conclusion : envoi direct de tout le contenu dans le contexte ici,
précisément parce que la tâche a besoin d'exhaustivité et que ça rentre —
les deux conditions comptent, pas juste la taille.


![[fig1.png]]
## Points à retenir de cette session

1. "S'arrête et attend validation" ≠ agent, même avec de l'automatisation
   avancée dedans.
2. La génération de texte (étape finale du RAG) n'implique plus de
   vecteurs/embeddings.
3. Biais de dataset = problème d'entraînement (permanent) ; mauvais
   retrieval = problème d'exécution (ponctuel, par requête).
4. Critère RAG vs contexte complet = besoin d'exhaustivité de la tâche,
   pas seulement la taille qui rentre ou non dans la fenêtre.
