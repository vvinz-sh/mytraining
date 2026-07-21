# mytraining

Repo de formation personnelle — notes, exercices et suivi de progression.

Vault Obsidian : ouvrir ce dossier directement comme vault (plugin **Obsidian Git** recommandé pour committer les notes automatiquement).

## Technos suivies

| Techno | Niveau visé | Format |
|---|---|---|
| RHEL 8 | Avancé — programme complet RHCSA (EX200) | notes/ + exercices/ |
| Ansible | Intermédiaire — rôles, Vault, structure de projet | notes/ + roles/ |
| Git | Débutant | notes/ |
| Logstash | Débutant | notes/ + pipelines/ |
| IA (concepts + pratique) | Débutant total → vague 2 en cours | notes/ + exercices/ |

## Suivi de progression — RHCSA (EX200)

- [x] 1. Comprendre et utiliser les outils essentiels
- [ ] 2. Créer des scripts shell simples
- [ ] 3. Faire fonctionner des systèmes (boot, systemd, processus)
- [ ] 4. Configurer le stockage local (partitions, LVM, swap)
- [ ] 5. Créer et configurer des systèmes de fichiers
- [ ] 6. Déployer, configurer et maintenir des systèmes
- [ ] 7. Gérer les réseaux de base
- [ ] 8. Gérer les utilisateurs et groupes
- [ ] 9. Gérer la sécurité (permissions, ACL, SELinux, firewalld)
- [ ] 10. Gérer les conteneurs (Podman)

## Suivi de progression — Git

- [x] Zone de staging (add / commit / diff / status)
- [ ] Branches : create, switch, merge
- [ ] Remotes : clone, push, pull, fetch
- [ ] Résolution de conflits
- [ ] Rebase vs merge
- [x] Purger un fichier de tout l'historique (`git filter-repo`) — module hors-série, `git/notes/03-purge-historique-filter-repo.md`

## Suivi de progression — Logstash

- [ ] Architecture (input / filter / output)
- [ ] Premier pipeline simple
- [ ] Filtres grok
- [ ] Sortie vers Elasticsearch

## Suivi de progression — Ansible

- [ ] Structure d'un rôle
- [ ] Inventaires et variables
- [ ] Ansible Vault
- [ ] Idempotence et handlers
- [ ] Tags et includes

## Suivi de progression — IA, vague 1 (base) — terminée ✅

- [x] Terminologie : LLM, tokens, prompt/system prompt, tool use, agents, MCP, RAG, embeddings, fine-tuning
- [x] Qu'est-ce que le Machine Learning (vs programmation classique)
- [x] Réseaux de neurones — intuition (poids, activation, entraînement)
- [x] Prompting — bonnes pratiques, few-shot, limites
- [x] Usage pratique — appeler une API LLM depuis un script (Python/bash)
- [x] RAG / fine-tuning — critères de décision (fréquence, nature, volume/coût)
- [x] Limites et biais — hallucinations, sur-confiance

TP réalisé avec succès : `ia-concepts/exercices/tp-ansible-llm-resultat.md`.

## Suivi de progression — IA, vague 2 (approfondissement)

**Paramètres et fonctionnement pratique**
- [x] Fenêtre de contexte en pratique (résumé progressif, compression, gestion d'historique long)
- [x] Paramètres de génération (`temperature`, `top_p`/`top_k`) — `ia-concepts/notes/16-...md`, `18-top-k-top-p.md`
- [x] Multimodalité (image/PDF au-delà du texte) — `ia-concepts/notes/19-multimodalite-patches-positional-embedding.md`
- [x] Guardrails et garde-fous en production
- [x] Coûts et facturation (tokens → €, input vs output)

**Hardware — pourquoi l'IA est si gourmande** — terminé ✅
- [x] Pourquoi l'entraînement/inférence dévore de la RAM/VRAM (taille des poids, précision numérique FP16/INT8, quantization)
- [x] Rôle du GPU vs CPU (parallélisme massif, multiplication de matrices)
- [x] CUDA vs Tensor Cores (logiciel vs matériel spécialisé)
- [x] Entraînement vs inférence (facteur ×4-6 : gradients, états d'optimiseur, activations)
- [x] Fine-tuning partiel — LoRA / QLoRA (rang intrinsèque faible, combinaison avec la quantization)
- [x] Panorama des LLM actuels (propriétaires vs open-weight, critères de choix, routing multi-modèles)

**Outils de l'écosystème**
- [ ] Frameworks d'orchestration (LangChain, LlamaIndex)
- [ ] Bases de données vectorielles (Pinecone, Chroma, Weaviate, pgvector)
- [ ] Outils no-code/low-code avec IA (n8n, Zapier)
- [ ] Assistants de code (Claude Code, Copilot)
- [ ] Serveurs MCP existants (panorama de ce qui existe déjà)

**TP en préparation**
- [ ] LLM local de bout en bout — Ollama (inférence) puis Unsloth/QLoRA (fine-tuning) sur RTX 3070 8 Go, WSL2 — design posé dans `ia-concepts/exercices/tp-llm-local-ollama-qlora-draft.md`, pas encore exécuté
- [ ] Agent Ansible avec boucle autonome (`until`/`retries`) — prolonge le TP 1 pour sentir en pratique agent vs tool use — design posé dans `ia-concepts/exercices/tp-ansible-agent-boucle-draft.md`, pas encore exécuté

## Suivi de progression — IA, hors programme (approfondissements ponctuels)

- [x] Deep learning vs Machine Learning (arbres de décision, forêts aléatoires) — `ia-concepts/notes/15-deep-learning-vs-ml-arbres-forets.md`
- [x] Pré-entraînement vs fine-tuning d'instruction (+ RLHF) — `ia-concepts/notes/17-pretraining-vs-instruction-tuning.md`
- [x] Mécanisme d'attention (Query/Key/Value, multi-head) — `ia-concepts/notes/20-mecanisme-attention-qkv-multihead.md`
- [x] Carte de consolidation du pipeline complet (tokens → embeddings → couches/attention → logits → softmax/temperature → génération) — `ia-concepts/notes/21-carte-consolidation-pipeline-llm.md`
- [x] Série de questions de consolidation (couches, activation, attention, RAG, diversité forêt/multi-head) — `ia-concepts/notes/22-serie-consolidation-couches-attention-rag.md`

## Ressources externes

Voir `ia-concepts/ressources-externes.md` — vidéos (3Blue1Brown, Karpathy) et livre (Géron) recommandés pour consolider les sujets les plus visuels (couches, activation, attention).
