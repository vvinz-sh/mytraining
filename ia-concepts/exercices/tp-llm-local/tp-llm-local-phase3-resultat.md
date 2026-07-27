# TP — LLM local, Phase 3 (lancement effectif de l'entraînement QLoRA) : en cours 🔄

Complète `tp-llm-local-phase2-resultat.md` (préparation dataset,
terminée). Cette phase couvre la configuration réelle d'Unsloth, le
diagnostic VRAM approfondi, et le premier entraînement qui tourne
effectivement.

## Script d'entraînement — première version

Basé sur la syntaxe Unsloth à jour pour Qwen3 (`FastLanguageModel`,
`get_chat_template`, `get_peft_model`, `SFTTrainer`/`SFTConfig`).
LoRA : `r=16`, `lora_alpha=16`, cible les 7 couches linéaires standard
(q/k/v/o_proj, gate/up/down_proj). Pas de mix 75/25
raisonnement/non-raisonnement (décision prise en Phase 2, capacité de
raisonnement de Qwen3 jugée non prioritaire pour cette tâche).

## Bugs système, dans l'ordre de découverte

### 1. `AttributeError: ThinkingBlock` puis erreurs d'installation en cascade
Résolus en Phase 2 (thinking désactivé, extraction par type de bloc).

### 2. `ValueError: Some modules are dispatched on the CPU`
`device_map="auto"` de `transformers` a mal évalué la VRAM disponible
malgré de la VRAM libre confirmée via `nvidia-smi`. Corrigé en forçant
`device_map={"": 0}` explicitement.

### 3. `RuntimeError: Failed to find C compiler`
Triton (utilisé par Unsloth pour compiler ses kernels GPU à la volée)
nécessite un compilateur C. Corrigé via `sudo apt install
build-essential`.

### 4. `fatal error: Python.h: No such file or directory`
Même mécanisme Triton, nécessite aussi les en-têtes de développement
Python. Corrigé via `sudo apt install python3-dev` (ou la version
exacte, `python3.12-dev`, à vérifier avec `python3 --version` dans le
venv).

### 5. `CUDA out of memory` au tout premier pas d'entraînement (modèle 8B)
Diagnostic en plusieurs temps :
- Empreinte mémoire du modèle seul : **7.38 Go** sur 8 Go de carte —
  bien au-delà des ~4.5-5 Go attendus pour un 8B en 4-bit pur
- Cause identifiée : la table d'embeddings et `lm_head` ne sont
  généralement **pas quantifiées** par bitsandbytes (question de
  précision), et Qwen3 a un vocabulaire de ~150k tokens — ces couches
  seules représentent probablement 1-2 Go supplémentaires en
  bfloat16
- **Point méthodologique important** : la quantification GGUF
  utilisée par Ollama (Phase 1, ~6.2 Go pour le 8B en inférence) et la
  quantification bitsandbytes NF4 utilisée par Unsloth pour
  l'entraînement ne sont **pas équivalentes** en efficacité mémoire —
  un modèle qui tourne confortablement en inférence via Ollama peut ne
  pas laisser assez de marge pour l'entraînement QLoRA via
  bitsandbytes

### 6. Décision : pivot du modèle de base, 8B → 4B
Plutôt que de continuer à réduire les paramètres d'entraînement sur un
8B trop juste, bascule vers `unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit`
(version pré-quantifiée "Dynamic 2.0" d'Unsloth, variante non-thinking).
Empreinte mémoire du 4B : **3.50 Go** — marge confortable retrouvée.

**Conséquence méthodologique assumée** : une nouvelle baseline a été
générée spécifiquement sur `qwen3:4b` (voir section suivante) plutôt
que de comparer le résultat fine-tuné à la baseline 8B déjà établie —
pour garder une comparaison avant/après cohérente sur le même modèle.

### 7. `Triton is not supported on current platform, roll back to CPU`
Warning initialement jugé possiblement inoffensif (concerne un
chemin de code `fla`/flash-linear-attention non utilisé par
l'architecture standard de Qwen3). Réévalué après coup : le vrai
signal pertinent était ailleurs dans le banner (`FA [Xformers = None.
FA2 = False]`) — Flash Attention 2 n'était pas actif, ce qui a une
vraie conséquence mémoire (coût quadratique de l'attention standard
sur les longues séquences).

### 8. `CUDA out of memory` toujours présent sur le 4B malgré la marge
Diagnostiqué comme lié à l'absence de Flash Attention 2 (croissance
quadratique de la mémoire d'attention avec la longueur de séquence).
Installation de `flash-attn` via wheels précompilés
(github.com/mjun0812/flash-attention-prebuild-wheels) plutôt que
compilation locale (souvent longue et capricieuse) — vérification
préalable de la correspondance exacte Python 3.12 / PyTorch 2.11 /
CUDA 13.0 (version tirée du banner Unsloth : `Torch: 2.11.0+cu130`,
pas de `nvidia-smi` ni `nvcc`, qui indiquent des versions différentes
et moins pertinentes ici). `FA2 = True` confirmé après installation.

### 9. `CUDA out of memory` une troisième fois malgré Flash Attention 2
Nouveau message apparu : `Unsloth: Double buffering enabled (parallel
H2D + compute) for backward pass` — mécanisme échangeant de la
mémoire contre de la vitesse (~8% de gain), maintenant deux buffers
simultanés. Pas de toggle simple trouvé pour le désactiver
spécifiquement. Décision pragmatique : réduire `max_seq_length` de
4096 à **3072** plutôt que de continuer à chasser un réglage
non documenté — accepte l'exclusion de 124/504 exemples (24.6%) du
dataset d'entraînement en échange d'une marge de sécurité réelle.

### 10. `CUDA out of memory` au step 20, spécifiquement pendant l'évaluation
L'entraînement tournait correctement (20 premiers pas passés, loss en
baisse). Le plantage survient précisément dans `evaluation_loop` →
`prediction_step` → conversion des logits en **float32** — une
opération de précision pleine qui, combinée au grand vocabulaire de
Qwen3, demande significativement plus de mémoire qu'un pas
d'entraînement classique (qui reste en bfloat16/4-bit).
Corrections combinées :
- `per_device_eval_batch_size=1` explicite (jamais fixé jusque-là)
- `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` (variable
  d'environnement, à définir avant tout import) pour réduire la
  fragmentation mémoire signalée dans le message d'erreur
  ("3.04 Go réservés mais non alloués")

## État à ce stade

Script corrigé, relance en cours au moment de la rédaction de cette
note. Premiers résultats avant le plantage de l'évaluation :
`train/loss` en baisse cohérente (1.074 → 0.788 sur les 20 premiers
steps), `grad_norm` stable et décroissant (0.24 → 0.137) — signaux
d'un entraînement sain, pas d'instabilité observée avant l'interruption.

## Nouvelle baseline sur qwen3:4b (avant fine-tuning)

Générée via `baseline_test.py` adapté (modèle `qwen3:4b` au lieu de
`qwen3:8b`), sur les mêmes 4 cas de test que la baseline 8B.

Résultats globalement similaires au 8B sur les cas courts (OOM, DNS) —
structure respectée, contenu globalement fidèle. Cas 2 (LDAP) : même
confusion que le 8B (invente un problème de certificat TLS au lieu du
vrai problème de connectivité réseau au backend) — erreur reproduite
à l'identique sur les deux tailles de modèle.

Cas 3 (disque plein, 520 lignes) : échec différent du 8B mais de même
nature — le 8B avait halluciné une "attaque par force brute SSH", le
4B part sur "trop de connexions SSH simultanées" (variante proche mais
pas identique). Confirme que le biais de prior + "lost in the middle"
documenté en note 42 n'est pas spécifique à la taille du modèle — les
deux tombent dans le même piège, avec une variante différente de la
mauvaise réponse.

## Débrief — lecture des métriques d'entraînement

Point pédagogique traité en parallèle du diagnostic technique :
- **`loss`** : cross-entropy entre prédiction et réponse de référence,
  token par token — la métrique centrale à suivre, doit baisser
  globalement
- **`grad_norm`** : ampleur du gradient à chaque étape — jauge de
  stabilité (explosion = divergence, quasi-zéro trop tôt = apprentissage
  qui s'arrête)
- **`learning_rate`** : suit la montée progressive du warmup
  (`warmup_steps=10`) jusqu'au taux cible (`2e-4`)
- **`epoch`** : simple indicateur de progression dans le dataset

Point de vigilance découvert en pratique sur TensorBoard : plusieurs
runs d'essais avortés restent visibles par défaut dans l'interface et
peuvent fausser la lecture visuelle — nécessité de décocher les
anciennes runs pour n'afficher que l'entraînement en cours.

Le vrai signal à surveiller pour détecter le surapprentissage :
comparer `eval/loss` à `train/loss` au même step, pas juste regarder
`train/loss` seule.

## Prochaine étape

Relancer l'entraînement complet avec les corrections des points 9 et
10. Si stable jusqu'au bout, comparer les 4 cas de test post-fine-tuning
à la baseline 4B fraîchement établie, avec une attention particulière
au cas 3 (biais de prior sur signal affaibli).

## Compétences pratiquées

- Diagnostic mémoire multi-couches : quantification (bnb vs GGUF),
  vocabulaire du modèle, Flash Attention, double buffering — plusieurs
  causes distinctes contribuant au même symptôme (OOM), traitées une
  par une plutôt que supposées résolues après un seul correctif
- Lecture de traceback pour localiser précisément la phase concernée
  (entraînement vs évaluation) avant de choisir un correctif
- Vérification de compatibilité de version tirée de la bonne source
  (banner du framework, pas `nvidia-smi`/`nvcc` qui mesurent autre
  chose) avant d'installer un binaire précompilé
- Arbitrage pragmatique entre poursuite d'optimisation et obtention
  d'un résultat qui fonctionne (accepter une perte de 24.6% du
  dataset plutôt que de chasser indéfiniment un réglage non documenté)
- Lecture et interprétation de métriques d'entraînement (loss,
  grad_norm, learning_rate) en conditions réelles
