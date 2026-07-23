# IA — Suivi détaillé

Détail complet du module IA, extrait du README racine pour rester
lisible à mesure que le module grossit. Structure des notes organisée
en sous-dossiers thématiques (`notes/fondamentaux/`,
`notes/generation-parametres/`, `notes/rag-embeddings/`,
`notes/hardware/`, `notes/attention-architecture/`, `notes/securite/`,
`notes/ecosysteme/`) ; chaque TP a son propre dossier sous
`exercices/` (design + résultat + code).

## Vague 1 (base) — terminée ✅

- [x] Terminologie : LLM, tokens, prompt/system prompt, tool use, agents, MCP, RAG, embeddings, fine-tuning
- [x] Qu'est-ce que le Machine Learning (vs programmation classique)
- [x] Réseaux de neurones — intuition (poids, activation, entraînement)
- [x] Prompting — bonnes pratiques, few-shot, limites
- [x] Usage pratique — appeler une API LLM depuis un script (Python/bash)
- [x] RAG / fine-tuning — critères de décision (fréquence, nature, volume/coût)
- [x] Limites et biais — hallucinations, sur-confiance

TP réalisé avec succès : `exercices/tp-ansible-llm/tp-ansible-llm-resultat.md`.

## Vague 2 (approfondissement) — terminée ✅

**Paramètres et fonctionnement pratique**
- [x] Fenêtre de contexte en pratique (compaction, résumé progressif, memory tool) — `notes/generation-parametres/24-fenetre-contexte-compaction.md`
- [x] Paramètres de génération (`temperature`, `top_p`/`top_k`) — `notes/generation-parametres/16-...md`, `18-top-k-top-p.md`
- [x] Multimodalité (image/PDF au-delà du texte) — `notes/generation-parametres/19-multimodalite-patches-positional-embedding.md`
- [x] Guardrails et garde-fous en production (prompt injection, moindre privilège, filtrage de sortie, défense en profondeur) — `notes/securite/25-guardrails-prompt-injection-moindre-privilege.md`
- [x] Coûts et facturation (tokens → €, input vs output) — `notes/generation-parametres/26-couts-facturation-input-output.md`

**Hardware — pourquoi l'IA est si gourmande**
- [x] Pourquoi l'entraînement/inférence dévore de la RAM/VRAM (taille des poids, précision numérique FP16/INT8, quantization)
- [x] Rôle du GPU vs CPU (parallélisme massif, multiplication de matrices)
- [x] CUDA vs Tensor Cores (logiciel vs matériel spécialisé)
- [x] Entraînement vs inférence (facteur ×4-6 : gradients, états d'optimiseur, activations)
- [x] Fine-tuning partiel — LoRA / QLoRA (rang intrinsèque faible, combinaison avec la quantization)
- [x] Panorama des LLM actuels (propriétaires vs open-weight, critères de choix, routing multi-modèles)

Notes : `notes/hardware/12-...md`, `13-...md`, `14-panorama-llm-qlora.md`.

**Outils de l'écosystème**
- [x] Frameworks d'orchestration (LangChain/LangGraph, LlamaIndex, CrewAI) — `notes/ecosysteme/27-panorama-outils-ecosysteme-hermes-mcp.md`
- [x] Bases de données vectorielles (Pinecone, Chroma, Weaviate, Qdrant, pgvector)
- [x] Outils no-code/low-code avec IA (n8n, Zapier)
- [x] Assistants de code (Claude Code, Copilot)
- [x] Serveurs MCP existants (panorama) + aparté Hermes (modèle open-weight vs Hermes Agent, framework agentique)

**TP**
- [x] Agent Ansible avec boucle autonome (`include_tasks`/`loop`) — **réalisé avec succès** ✅ — `exercices/tp-ansible-agent/`
- [x] Visualiser des embeddings de mots (gensim/GloVe, PCA, matplotlib) — **réalisé avec succès** ✅ — `exercices/tp-visualisation-embeddings/`
- [x] RAG sur son propre repo + serveur MCP maison — **réalisé avec succès** ✅ — `exercices/tp-rag-mcp/`
- [ ] LLM local de bout en bout — Ollama (inférence) puis Unsloth/QLoRA (fine-tuning) sur RTX 3070 8 Go, WSL2 — design posé dans `exercices/tp-llm-local/`, pas encore exécuté
- [ ] Sécuriser le serveur RAG/MCP (guardrail pattern + guardrail sémantique) — design posé dans `exercices/tp-securite/`, pas encore exécuté

## Vague 3 (MLOps/Ops) — en préparation 🚧

Identifiée via un radar de comparaison avec un référentiel junior
MLOps (~2 ans d'XP) — ces catégories étaient jusqu'ici des angles
morts complets du module.

### 1. Déploiement & serving

- [ ] Conteneuriser un modèle (Docker) — packager un serving simple
- [ ] Frameworks de serving dédiés (vLLM, TGI, Triton) vs un serveur classique (Flask/FastAPI)
- [ ] Scaling horizontal et load balancing pour une API de modèle
- [ ] Autoscaling selon la charge (Kubernetes HPA ou équivalent cloud)
- [ ] Latence/throughput : batching de requêtes, streaming de réponses

### 2. Monitoring & évaluation

- [ ] Logging structuré des requêtes/réponses d'un LLM en prod
- [ ] Métriques RAG concrètes (recall@k, faithfulness/groundedness, latence de recherche)
- [ ] Détection de drift (données, comportement du modèle dans le temps)
- [ ] Traçabilité/observabilité (LangSmith ou équivalent) — suivre une requête à travers tout le pipeline
- [ ] Alerting sur dégradation de qualité ou de performance

### 3. CI/CD & pipelines MLOps

- [ ] Registre de modèles (model registry) — versionner un modèle comme un artefact
- [ ] Tracking d'expériences (MLflow, W&B) — comparer plusieurs runs/fine-tunings
- [ ] Pipeline de réentraînement automatisé (déclenché par drift ou planning)
- [ ] Tests automatisés spécifiques au ML (régression sur les sorties, pas juste tests de code classique)
- [ ] Déploiement progressif (canary, blue-green) appliqué à un modèle

### 4. Gouvernance & conformité

- [ ] RGPD appliqué à l'IA (données personnelles dans les prompts/logs)
- [ ] AI Act européen — grandes lignes, catégories de risque
- [ ] Documentation type "model card" / "system card"
- [ ] Audit trail — tracer qui a demandé quoi, quelle version de modèle a répondu
- [ ] Biais et équité (fairness) — angle gouvernance, pas ML pur

### 5. Ingénierie de données pour le ML

- [ ] Pipelines d'ingestion et de nettoyage de données (entraînement ou RAG)
- [ ] Versioning de données (DVC ou équivalent) — pourquoi une donnée doit être versionnée comme du code
- [ ] Feature stores — concept, à quoi ça sert
- [ ] Qualité et validation de données (détection d'anomalies, schémas)
- [ ] Cycle de vie de la donnée (rétention, suppression, lien avec RGPD)

## Hors programme (approfondissements ponctuels)

- [x] Deep learning vs Machine Learning (arbres de décision, forêts aléatoires) — `notes/fondamentaux/15-deep-learning-vs-ml-arbres-forets.md`
- [x] Pré-entraînement vs fine-tuning d'instruction (+ RLHF, biais structurel) — `notes/fondamentaux/17-pretraining-vs-instruction-tuning.md`
- [x] Mécanisme d'attention (Query/Key/Value, multi-head) — `notes/attention-architecture/20-mecanisme-attention-qkv-multihead.md`
- [x] Carte de consolidation du pipeline complet — `notes/attention-architecture/21-carte-consolidation-pipeline-llm.md`
- [x] Série de questions de consolidation — `notes/attention-architecture/22-serie-consolidation-couches-attention-rag.md`
- [x] Visualisation des embeddings dans l'espace, arithmétique vectorielle, hypothèse distributionnelle — `notes/rag-embeddings/23-visualisation-embeddings-hypothese-distributionnelle.md`
- [x] Bases de données vectorielles en profondeur (ANN/HNSW, angle sysadmin) — `notes/rag-embeddings/30-bases-vectorielles-ann-hnsw-sysadmin.md`
- [x] Chunking en profondeur (chevauchement, taille adaptative, chunking sémantique) — `notes/rag-embeddings/31-chunking-chevauchement-taille-adaptative.md`

## Ressources externes

Voir `ressources-externes.md` — vidéos (3Blue1Brown, Karpathy) et livre
(Géron) recommandés pour consolider les sujets les plus visuels
(couches, activation, attention).
