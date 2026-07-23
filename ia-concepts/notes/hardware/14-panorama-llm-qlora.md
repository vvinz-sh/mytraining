# IA — Panorama des LLM (mi-2026) et QLoRA

## Panorama des grandes familles de LLM

**Propriétaires (API/abonnement, pas de contrôle sur l'hébergement)**
- **OpenAI (GPT)** — GPT-5.5, généraliste solide, fort en agentique/terminal.
- **Anthropic (Claude)** — Opus 4.8 (code fin, sécurité, contexte 1M),
  Sonnet 5 (équilibre perf/prix).
- **Google (Gemini)** — Gemini 3.1 Pro, fort en raisonnement scientifique
  et très longs contextes (plusieurs millions de tokens selon les
  sources).
- **xAI (Grok)** — Grok 4.3, orienté temps réel et outils agentiques,
  intégré à X.

**Open-weight (téléchargeables, auto-hébergeables)**
- **Meta (Llama)** — Llama 4 (Scout, Maverick), référence pour le
  contrôle total de l'infra.
- **Mistral AI** (français) — Large 3 / Medium 3.5, positionné sur la
  souveraineté des données (hébergement UE, RGPD, AI Act).
- **Qwen** (Alibaba), **DeepSeek**, **GLM** (Z.AI) — très compétitifs
  sur le rapport performance/coût, notamment pour le code.

## Critères de choix (pas de "meilleur" absolu)

- Agents/coding critique → GPT-5.5 ou Claude Opus 4.8
- Volume courant, bon rapport perf/prix → Gemini 3.1 Pro ou Claude Sonnet 5
- Données sensibles / souveraineté → Mistral (UE, RGPD)
- Auto-hébergement, contrôle total → Llama, Mistral, Qwen (open-weight)

## Routing multi-modèles — écho direct avec ce qu'on avait vu

Beaucoup d'entreprises orchestrent un **routing multi-modèles** plutôt
qu'un seul choix figé : chaque requête part vers le modèle le plus
adapté à sa complexité/coût, plutôt que tout faire passer par le modèle
le plus cher par défaut.

Écho direct avec le principe déjà vu (choix de modèle selon la tâche —
Haiku effort bas pour du volume simple, Opus pour du complexe) : le
routing applique cette logique à l'échelle d'une architecture entière,
comme un load balancer qui choisit le bon serveur selon la charge plutôt
que de tout envoyer au plus puissant.

## Petit TP maison — modèles adaptés à 8-12 Go de VRAM

**Inférence**
- Llama 3.1 8B en Q4_K_M (~5 Go) — référence "tier 8 Go", très bonne
  qualité d'instruction-tuning.
- Mistral 7B en Q8 (~12 Go) — rapide, fiable, bon suivi d'instructions.
- Qwen 3 8B (Q5_K_M) ou Phi-4-mini — solides, bons en code.

Outil recommandé : **Ollama** (installation en une commande, gère le
téléchargement et la quantization automatiquement).

## QLoRA — la pièce manquante entre quantization et LoRA

**QLoRA = LoRA + quantization**, combinés pour résoudre **deux problèmes
différents** :
- **LoRA seul** résout le problème "gradients/états d'optimiseur pour
  des milliards de poids" (en gelant les poids de base et n'entraînant
  qu'un petit ajout).
- Mais LoRA seul **ne résout pas** un problème séparé : les poids de
  base gelés doivent quand même être **chargés en mémoire** pour
  fonctionner — à pleine précision (FP16), un modèle 7B pèse déjà ~14 Go,
  ce qui dépasse un budget de 12 Go avant même de commencer l'entraînement
  de l'ajout LoRA.
- **La quantization** résout précisément ce second problème : réduire le
  poids des poids de base gelés eux-mêmes (de ~14 Go en FP16 à ~3,5-4 Go
  en 4-bit), libérant la place pour que le petit entraînement LoRA
  (gradients + activations de l'ajout) tienne dans le reste du budget
  VRAM.

Résumé : LoRA et quantization s'attaquent à deux goulots d'étranglement
**différents**, pas au même problème résolu deux fois — c'est pour ça
qu'on les combine plutôt que d'utiliser l'un ou l'autre seul.

Repère de qualité : QLoRA atteint généralement **90-95%** de la qualité
d'un fine-tuning complet — largement suffisant pour la plupart des
tâches pratiques (ton, structure de réponse, vocabulaire spécifique).

Avec 8-12 Go de VRAM, **QLoRA est le choix indiqué** (contrairement au
LoRA classique en 16-bit, plutôt visé pour des cartes 24 Go+). Pour un
modèle 7-8B, c'est jouable confortablement.

Outil recommandé pour le fine-tuning : **Unsloth** ou **Axolotl** —
simplifient la mise en place de QLoRA (quantization, hyperparamètres)
comparé à une implémentation bas niveau à la main.

## À venir (vague 2)

- [ ] Paramètres de génération (`temperature`, `top_p`/`top_k`)
- [ ] Multimodalité, guardrails, coûts/facturation
- [ ] Panorama des serveurs MCP existants
- [ ] TP maison à designer : inférence (Ollama) puis QLoRA (Unsloth/Axolotl)
