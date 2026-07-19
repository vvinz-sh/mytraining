# IA — Exercices d'approfondissement : agent vs tool use, MCP, RAG, embeddings

Suite de `01-terminologie-agents-mcp.md` — série de scénarios pour ancrer
les définitions par la pratique plutôt que par la théorie brute.

## Agent vs tool use — scénarios

**Claude Code qui corrige un bug** (lit le fichier → repère le bug → modifie
→ lance les tests → ajuste si échec → relance les tests → confirme une fois
au vert, sans validation humaine à chaque étape) → **agent**. Enchaînement
autonome de plusieurs étapes vers un objectif, avec réajustement en cours
de route.

**Chatbot météo** (une question → un appel API → une réponse, fin) →
**tool use simple**. Un seul aller-retour, aucun raisonnement multi-étapes.
Ce qui manquerait pour en faire un agent : par exemple, en déduire un
conseil vestimentaire, croiser avec l'agenda, etc. — plusieurs étapes
raisonnées à la suite.

## MCP — ce que ça apporte concrètement

Comparaison : (A) intégration codée sur-mesure entre un chatbot et Jira,
qui ne marche qu'avec ces deux systèmes précis ; (B) un serveur MCP Jira
déjà existant, utilisable par n'importe quel client compatible MCP sans
code sur-mesure.

Le gain de B n'est pas juste "plus flexible" en général : c'est la
**réutilisabilité**. Le serveur MCP est écrit une seule fois et devient
utilisable par n'importe quel LLM/outil compatible, sans réintégration à
chaque nouvelle combinaison client/service.

MCP ne décrit **pas une action** (contrairement au tool use, qui EST
l'action ponctuelle "appeler cet outil maintenant"). MCP décrit le
**protocole/l'infrastructure** qui rend cette action possible de façon
standardisée — analogie : HTTP n'est pas "visiter un site" (l'action),
c'est le protocole qui permet à n'importe quel navigateur de visiter
n'importe quel site sans négociation propriétaire.

## RAG vs contexte simple

Donner un PDF de 50 pages qui tient entièrement dans le contexte et poser
des questions dessus → **pas du RAG**. Le critère n'est pas "source
externe ou pas" (le PDF est externe) mais l'étape de **retrieval**
(recherche/sélection) : dans un vrai RAG, il y a une masse de documents
trop grande pour tenir dans le contexte, et un système sélectionne
seulement les passages pertinents avant de les injecter. Ici, tout le
contenu est déjà fourni intégralement — rien à "retrouver".

### Pipeline RAG complet

```
documents → embeddings (vectorisation, une fois, à l'indexation)
question   → embedding (vectorisation, à la volée)
                ↓
        recherche par similarité (comparaison des vecteurs, ex. cosinus)
                ↓
        les N documents les plus proches sont récupérés
                ↓
        injectés dans le contexte du LLM avec la question
```

Point de vocabulaire à ne pas confondre : **l'embedding** est la
représentation vectorielle (faite une fois) ; **la recherche par
similarité** est le calcul de distance fait *sur* ces embeddings pour
sélectionner les documents pertinents. L'embedding rend la comparaison
possible, il n'est pas la sélection elle-même.

## Embedding vs hash — l'analogie qui aide

- **Hash (MD5, SHA256...)** : effet avalanche — deux entrées presque
  identiques donnent des hash complètement différents. Sert à détecter un
  changement (identique / pas identique), pas à mesurer une ressemblance.
  Aucune notion de distance calculable entre deux hash.
- **Embedding** : deux textes de sens proche → vecteurs proches dans
  l'espace, même sans mots en commun ("Le chat dort sur le canapé" ≈ "Le
  félin fait la sieste sur le sofa"). Penser en **coordonnées GPS** plutôt
  qu'en hash : un vecteur place un texte à une position, et on calcule une
  **distance** entre deux positions, comme entre deux villes sur une
  carte (juste avec des centaines de dimensions au lieu de 2).

Un hash ne peut jamais servir à une recherche par similarité de sens : à
cause de l'effet avalanche, il n'existe aucun espace métrique où "proche"
et "loin" ont un sens pour des hash — même 99% d'identité en entrée donne
des hash à distance aléatoire.

## À venir

- [ ] Machine Learning vs programmation classique
- [ ] Réseaux de neurones — intuition (poids, activation, entraînement)
- [ ] Prompting — bonnes pratiques, few-shot, limites
- [ ] Usage pratique — appeler une API LLM depuis un script
