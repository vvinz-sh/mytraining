# TP — LLM local de bout en bout : inférence (Ollama) puis QLoRA (draft)

Statut : **design posé, pas encore exécuté**. Suite logique du module
hardware (quantization, CUDA/Tensor Cores, entraînement vs inférence,
LoRA/QLoRA, panorama LLM).

## Environnement confirmé

- **Control/exécution** : WSL2 Ubuntu-24.04 (converti depuis WSL1 —
  bloquant initial résolu)
- **GPU** : NVIDIA GeForce RTX 3070, **8 Go VRAM**, passthrough WSL2
  fonctionnel (`nvidia-smi` OK depuis WSL, driver 580.159.03 côté Linux /
  596.49 côté Windows, CUDA 13.2)
- Point d'attention : 8 Go pile, bas de la fourchette "8-12 Go" — moins
  de marge que 12 Go, paramètres à adapter en conséquence (batch size,
  longueur de contexte réduits).

## Phase 1 — Inférence locale avec Ollama

**Objectif** : faire tourner un petit LLM en local, sans dépendre d'une
API, et se familiariser avec le concept de modèle quantifié qui tourne
réellement sur son propre GPU.

**Étapes envisagées**
1. Installer Ollama dans WSL2 (`curl -fsSL https://ollama.com/install.sh | sh`).
2. Vérifier qu'Ollama détecte bien le GPU (pas de fallback CPU silencieux).
3. Télécharger et lancer un modèle adapté à 8 Go :
   - `ollama run llama3.1:8b-instruct-q4_K_M` (~5 Go, référence "tier 8 Go")
   - Alternative à tester : `mistral:7b` ou `qwen2.5:7b`
4. Tester quelques prompts, observer la vitesse de génération
   (tokens/seconde) et la consommation VRAM en direct via `nvidia-smi`
   dans un second terminal pendant la génération.
5. Comparer subjectivement la qualité des réponses à ce qu'on obtient
   via l'API Claude (pour ancrer la différence "petit modèle local" vs
   "gros modèle cloud").

**Point pédagogique** : observer concrètement, avec `nvidia-smi` ouvert
en parallèle, la VRAM qui monte au chargement du modèle puis reste
stable pendant l'inférence — donne un visage concret à tout ce qu'on a
vu en théorie sur le chargement des poids.

## Phase 2 — Fine-tuning QLoRA avec Unsloth

**Objectif** : pratiquer un vrai fine-tuning léger sur le modèle testé
en phase 1, et observer la différence de consommation VRAM par rapport
à la simple inférence.

**Étapes envisagées**
1. Installer Unsloth dans un environnement Python dédié (venv), pour ne
   pas polluer l'installation Ansible/`.py3` existante.
2. Préparer un petit jeu de données (500 exemples suffisent pour une
   adaptation de style/format, comme vu dans nos notes) — idée concrète
   et ancrée dans ton terrain : un jeu d'exemples "log brut → résumé
   structuré", pour prolonger le TP Ansible+API déjà fait.
3. Configurer QLoRA (quantization 4-bit du modèle de base + LoRA sur
   l'ajout) avec des hyperparamètres adaptés à 8 Go :
   - batch size réduit (1-2, avec gradient accumulation pour compenser)
   - séquence courte (1024-2048 tokens plutôt que plus)
4. Lancer l'entraînement, observer la VRAM occupée pendant
   l'entraînement (`nvidia-smi` en parallèle) vs pendant l'inférence
   seule de la phase 1 — bon point de comparaison concret pour le
   facteur "×4-6" vu en théorie (nuancé ici par QLoRA qui réduit
   fortement ce facteur).
5. Fusionner l'adaptateur LoRA obtenu avec le modèle de base, puis le
   tester en inférence (via Ollama ou directement) pour voir l'effet du
   fine-tuning sur des exemples nouveaux.

## Prérequis à vérifier avant de lancer la Phase 2

- Espace disque suffisant (modèles + checkpoints + environnement Python
  dédié peuvent représenter plusieurs dizaines de Go)
- Dataset d'exemples préparé à l'avance (format attendu par Unsloth à
  vérifier dans sa doc au moment de s'y mettre)

## Ce qu'on n'a pas encore vu et qu'il faudra probablement pendant l'exécution

- Format exact du dataset attendu par Unsloth (JSON/JSONL avec structure
  précise)
- Choix concret des hyperparamètres LoRA (rang `r`, `alpha`) — on avait
  vu le principe, pas encore la pratique du réglage
- Évaluation du résultat (comment juger objectivement si le fine-tuning
  a amélioré quelque chose, au-delà du ressenti qualitatif)
