# IA — Terminologie : LLM, tokens, tool use, agents, MCP, RAG

Statut : **terminologie de base acquise**. À creuser ensuite : ML vs prog
classique, intuition réseaux de neurones, prompting.

## Les briques de base

- **LLM (Large Language Model)** — le modèle de base. Prend du texte en
  entrée, prédit la suite token par token. Stateless : ne se souvient de
  rien entre deux appels sauf ce qu'on lui redonne à chaque fois.
- **Token** — unité de base manipulée par le modèle. Ni un mot entier ni
  une lettre : souvent un morceau de mot. Le **context window** est la
  limite de tokens visibles en une fois (prompt + historique + réponse) —
  analogue à une limite de RAM allouée à un process : au-delà, l'ancien
  contenu est coupé/oublié.
- **Prompt / System prompt** — le prompt est la requête utilisateur ; le
  system prompt est une couche de config injectée en amont par celui qui
  déploie le modèle (comportement, contraintes) — comparable à un fichier
  de conf chargé avant que le service ne traite les requêtes.

## Tool use, agents, MCP — la hiérarchie

```
MCP        → le protocole de connexion (le "tuyau" standardisé vers des
             outils/données externes : GitHub, Drive, Slack...)
Tool use   → une action ponctuelle via un outil, décidée par le LLM puis
             exécutée par l'orchestrateur autour de lui (le LLM ne
             l'exécute jamais lui-même)
Agent      → plusieurs tool use enchaînés en autonomie vers un objectif,
             avec réévaluation à chaque étape (boucle : réfléchir → agir →
             observer → réajuster), sans validation humaine à chaque pas
```

Exemple concret : aller chercher un fichier sur Google Drive suite à une
question = **tool use, via MCP**. Pas un agent : une seule action, décidée
et exécutée dans le fil normal de l'échange, pas de boucle autonome
multi-étapes.

Ça deviendrait un agent si : chercher le fichier → l'analyser → en déduire
qu'il faut un autre document → aller le chercher → croiser les deux →
générer un rapport, le tout enchaîné sans validation intermédiaire.

## Distinction avec l'automatisation classique

Un thermostat programmable (règle fixe : si heure = X alors température =
Y) n'est **ni** du tool use **ni** un agent — c'est de l'automatisation à
base de règles fixes, sans raisonnement. Il exécute un plan figé sans
jamais évaluer une situation nouvelle.

| Type | Décision | Exemple |
|---|---|---|
| Automatisation classique | Règle fixe, zéro raisonnement | Thermostat programmé |
| Tool use | LLM raisonne pour choisir *une* action | Aller chercher un fichier sur demande |
| Agent | LLM raisonne en boucle, *plusieurs* actions vers un but | Recherche → analyse → recherche complémentaire → rapport |

## RAG, embeddings, fine-tuning (aperçu, à approfondir)

- **RAG (Retrieval-Augmented Generation)** — recherche de documents
  pertinents dans une base externe (via similarité sur des embeddings) et
  injection dans le contexte au moment de la requête, plutôt que tout
  faire tenir dans le prompt ou ré-entraîner le modèle.
- **Embeddings** — représentation d'un texte en vecteur numérique ; des
  textes proches en sens ont des vecteurs proches (recherche sémantique,
  pas juste mot-clé).
- **Fine-tuning** — ré-entraîner (partiellement) un modèle sur des données
  spécifiques. Différence clé avec le RAG : le fine-tuning modifie le
  modèle (lourd, coûteux) ; le RAG laisse le modèle intact et lui donne
  juste du contexte à la demande (léger, flexible).

## À venir

- [ ] Machine Learning vs programmation classique
- [ ] Réseaux de neurones — intuition (poids, activation, entraînement)
- [ ] Prompting — bonnes pratiques, few-shot, limites
- [ ] Usage pratique — appeler une API LLM depuis un script
- [ ] Limites et biais — hallucinations, sur-confiance
