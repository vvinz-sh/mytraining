# IA — Panorama de l'écosystème d'outils (mi-2026)

Dernier point de la vague 2 — section "Outils de l'écosystème" désormais
complète.

## Frameworks d'orchestration

- **LangChain** — le plus généraliste : chaînes d'appels LLM, mémoire,
  outils, agents. **LangGraph** (extension) gère l'orchestration d'agents
  avec état ; **LangSmith** pour l'observabilité. Large écosystème
  d'intégrations (700+).
- **LlamaIndex** — spécialisé sur la donnée : ingestion, indexation,
  récupération de documents pour du RAG. Plus abouti que LangChain
  spécifiquement sur les pipelines RAG (chunking, filtrage par
  métadonnées, reranking).
- **CrewAI** — orchestration **multi-agents** (plusieurs agents
  collaborant, chacun avec un rôle défini).

### Correspondance directe avec les concepts déjà vus

La distinction LangChain/LlamaIndex reflète exactement la différence
entre **orchestration d'agent** (LangChain — enchaîner des tool use en
autonomie, comme le TP agent Ansible avec `until`/`retries`) et **RAG**
(LlamaIndex — recherche/récupération de documents pertinents). En
pratique, beaucoup d'équipes combinent les deux : LlamaIndex pour la
couche recherche, LangChain/LangGraph pour la couche agent.

## Bases de données vectorielles

**Pinecone**, **Weaviate**, **Qdrant**, **Chroma**, **pgvector** —
implémentent à grande échelle l'étape "recherche par similarité" du
pipeline RAG déjà détaillé (comparer des embeddings, récupérer les plus
proches), avec de l'indexation optimisée pour rester rapide sur des
millions/milliards de vecteurs. `pgvector` se distingue en étant une
extension PostgreSQL classique plutôt qu'une base dédiée.

## Outils no-code/low-code avec IA

**n8n**, **Zapier** — automatisations (avec ou sans LLM) sans coder, via
interface visuelle. Utile pour prototyper rapidement, mais moins
flexible que du code pour des logiques complexes (même compromis vu avec
le TP agent Ansible : le code donne un contrôle plus fin sur une boucle
conditionnelle qu'un outil no-code).

## Assistants de code

**Claude Code**, **GitHub Copilot** — intégrés au flux de développement
(terminal, IDE), avec accès aux fichiers du projet. Exemple concret
d'agent : boucle lire → coder → tester → corriger, sans validation
humaine à chaque étape.

## Hermes — deux choses distinctes (Nous Research)

### Hermes, la famille de modèles (open-weight)

LLM open-weight (Hermes 3, Hermes 4...), basés sur des architectures
comme Llama, avec un post-entraînement visant une forte "steerability"
(moins de refus par défaut). Rentre dans le **panorama des LLM
open-weight** déjà vu (`14-panorama-llm-qlora.md`), à côté de Llama,
Mistral, Qwen — pertinent pour des contraintes de souveraineté/air-gap
(santé, conformité).

### Hermes Agent, le framework agentique

Agent autonome **auto-hébergé**, tournant comme un daemon persistant.
Points qui recoupent directement des concepts déjà vus :
- **Model-agnostic** (route vers n'importe quel LLM — Claude, GPT, Llama
  local via Ollama...) → écho du **routing multi-modèles** vu dans le
  panorama LLM.
- **Mémoire persistante entre sessions**, dans des fichiers externes qui
  survivent d'une session à l'autre → exactement le principe du
  **memory tool** vu dans la note sur la compaction
  (`24-fenetre-contexte-compaction.md`), construit ici comme produit
  complet.
- **Auto-génération de "skills" réutilisables** — convertit une tâche
  résolue en compétence réutilisable pour la prochaine fois similaire →
  apprentissage procédural écrit en texte, différent du fine-tuning (pas
  de ré-entraînement des poids).

Question de positionnement tranchée : le mécanisme "boucle autonome +
réajustement" d'un agent comme Hermes Agent se rapproche de
**LangGraph** (orchestration d'agent), pas de MCP. MCP ne serait qu'un
des outils que l'agent utiliserait en cours de route (ex : un serveur
MCP GitHub pour aller chercher un fichier) — MCP est le tuyau de
connexion, LangGraph/Hermes Agent est le cerveau qui décide quand et
comment l'utiliser en boucle.

## Panorama des serveurs MCP existants

Connecteurs officiels/communautaires pour la plupart des outils courants
: GitHub, Google Drive, Slack, bases de données (Postgres, SQLite),
gestion de projet (Jira, Linear, Asana), navigateurs web, système de
fichiers local. Principe déjà vu : un serveur MCP est écrit une fois et
devient utilisable par n'importe quel client compatible, plutôt qu'une
intégration ad-hoc par entreprise/outil.

## Aparté — auto-observation dans notre propre conversation

Question posée en fin de session : y a-t-il une orchestration
d'agent derrière les réponses de Claude dans cette conversation ?

Constat honnête, sans sur-interpréter :
- Ce qui est **visible** : du **tool use** clair (appels à `web_search`,
  création de fichiers, `bash`, outils de visualisation) — je décide
  d'appeler un outil, un système externe l'exécute, me renvoie un
  résultat.
- **Mini-boucle agentique locale** : à l'intérieur d'un seul tour de
  réponse, plusieurs outils peuvent s'enchaîner sans repasser par
  l'utilisateur — mais **entre chaque tour**, l'attente du message
  suivant de l'utilisateur casse la définition stricte d'un agent
  pleinement autonome (contrairement à Hermes Agent, qui tourne en fond
  sans attendre un humain).
- **Ce qui n'est pas connu avec certitude** : l'architecture interne
  exacte côté Anthropic (routing entre modèles, orchestration cachée) —
  reconnaître cette limite plutôt que d'inventer une réponse précise
  mais non fiable, écho direct du principe de sur-confiance vu dans
  `11-limites-hallucinations-surconfiance.md`.

## Vague 2 — complète ✅

Avec cette note, l'intégralité de la vague 2 (paramètres/fonctionnement
pratique, hardware, outils de l'écosystème) est désormais couverte.
