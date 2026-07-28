# Mémo — combler l'axe Écosystème (idées de TP, non détaillées)

Contexte : axe resté au niveau panorama pur
(`ecosysteme/27-panorama-outils-ecosysteme-hermes-mcp.md`), alors que
tout le reste du repo a été construit "from scratch" (Chroma +
sentence-transformers à la main, boucle d'agent codée en Ansible,
serveur MCP custom) plutôt qu'avec les frameworks dédiés qu'on a juste
nommés en théorie.

## Déjà couvert (correction faite en session)

- **Serveurs MCP communautaires** — en fait déjà pratiqué : serveur
  officiel `mcp-server-git` utilisé en complément du serveur custom
  `git-push-perso` (qui comble juste le push, absent de l'officiel).

## Items à couvrir, avec une idée de TP par item

| Item | Ce qui manque | Idée de TP |
|---|---|---|
| LlamaIndex | Jamais utilisé, alors que c'est l'équivalent outillé du TP RAG/MCP fait à la main | Réimplémenter `tp-rag-mcp` avec LlamaIndex plutôt que Chroma+sentence-transformers manuels — comparer les lignes de code, ce que le framework abstrait |
| LangChain/LangGraph | Jamais utilisé, alors que le TP agent Ansible fait déjà "à la main" ce que LangGraph orchestre nativement | Reprendre la boucle du TP agent avec LangGraph plutôt que `include_tasks`/`loop` Ansible — comparer les deux approches d'orchestration |
| CrewAI | Jamais touché — aucun TP avec un vrai multi-agent (rôles distincts qui collaborent) | Petit multi-agent : un agent "chercheur" (interroge `search_notes`) + un agent "rédacteur" (synthétise) |
| No-code (n8n) | Jamais essayé | Reproduire une version simplifiée du pipeline monitoring (golden dataset + alerte) via n8n plutôt qu'un script Python — mesurer l'effort relatif |
| Assistants de code (Claude Code) | À vérifier si déjà pratiqué au quotidien sans le documenter comme exercice | Si oui, juste à noter comme acquis plutôt qu'à designer |

## Principe retenu pour ce genre de session

Pas de nouvelle théorie ici — le format qui ferait le plus progresser
cet axe est de reprendre un TP **déjà réussi** et de le refaire avec
l'outil dédié, exactement le format qui a fait grimper Hardware et
Sécurité dans le radar (exécution réelle, pas design supplémentaire).
