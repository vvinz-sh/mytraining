# TP — LLM local, Phase 2 (fine-tuning QLoRA) : en cours 🔄

Complète `tp-llm-local-ollama-qlora-draft.md`, Phase 2. Suite de
`tp-llm-local-phase1-resultat.md` (inférence Ollama validée).

## Choix du modèle

`qwen3:8b` retenu plutôt que Llama 3.1 8B (utilisé en Phase 1) — à
taille égale, Qwen3 8B bat Llama 3.1 8B sur la plupart des benchmarks
(maths, raisonnement, multilingue) et propose un mode "thinking".
Écosystème Unsloth bien documenté pour cette famille — avantage
pratique pour un premier TP QLoRA.

Vérifié explicitement avant de choisir : `qwen3:8b` est **dense**, pas
une variante MoE (Mixture-of-Experts) — point de vigilance identifié
car un nom similaire peut recouvrir des profils mémoire très
différents à l'entraînement.

## Baseline (avant fine-tuning)

### Jeu de test réservé (4 cas, jamais utilisés pour l'entraînement)

1. Disque plein en cascade (réutilisé de `tp-ansible-agent`, log de
   520 lignes, `generate-incident-log.sh`)
2. OOM kill applicatif (généré via API)
3. Panne réseau/DNS par règle iptables (généré via API)
4. Authentification SSSD/LDAP désynchronisée (généré via API)

Résumé de référence généré pour chaque cas via l'API Claude (Sonnet 5,
thinking désactivé, Structured Outputs avec le schéma à 5 champs :
`type_incident`, `cause_racine`, `symptome_observe`, `service_affecte`,
`action_recommandee`) :
- `generer_test_logs.py` — génère les 3 cas de test (OOM, DNS, LDAP),
  produit `dataset_test.json`
- `generer_reference_disque_plein.py` — génère uniquement le résumé
  de référence pour le 4e cas (le log lui-même préexistait dans
  `tp-ansible-agent`), l'ajoute à `dataset_test.json`
- `baseline_test.py` — fait tourner `qwen3:8b` sur les 4 cas de
  `dataset_test.json`, produit `baseline_avant_finetuning.json`

### Bugs rencontrés en préparant les cas de test

- **`AttributeError: 'ThinkingBlock' object has no attribute 'text'`** —
  extraction par position (`content[0].text`) au lieu de par type ;
  corrigé en filtrant explicitement les blocs `type == "text"`, et en
  désactivant le thinking (`thinking={"type": "disabled"}`), inutile
  pour une tâche de génération structurée
- **Troncature par `max_tokens` trop bas** (2000 puis 3000
  insuffisants) — diagnostiqué via la console API (tokens de sortie
  strictement égaux à la limite configurée = signature de troncature),
  résolu en montant à 6000

### Résultats de la baseline

Sur les 3 cas courts (OOM, DNS, LDAP) : Qwen respecte la structure
demandée, contenu globalement fidèle à la référence mais parfois
partiellement inexact (ex : cas LDAP — invente une cause de certificat
SSL au lieu du vrai problème de connectivité réseau au backend).

Sur le cas long (520 lignes, disque plein) : **échec méthodologique
révélateur**, documenté en détail dans la note 42 (5e mode d'échec).
Trois tentatives successives, toutes dans `baseline_test.py` :
- 1er essai (`num_ctx` par défaut ~4096, consigne en tête de prompt) :
  structure complètement hors sujet (métadonnées génériques du log),
  cause = troncature silencieuse de la consigne
- 2e essai (`num_ctx=8192` explicite, mais consigne toujours en tête) :
  structure **encore fausse** (champs improvisés, pas les 5 attendus)
  — confirme que le dépassement de `num_ctx` seul n'expliquait pas
  tout le problème
- 3e essai (consigne déplacée en **fin** de prompt, `num_ctx=8192`
  inchangé) : structure enfin respectée (les 5 bons champs), mais
  diagnostic complètement faux ("attaque par force brute SSH" au lieu
  de la saturation disque réelle) — combinaison "lost in the middle"
  + biais de prior hérité du pré-entraînement, malgré l'absence de
  troncature cette fois

Correction appliquée pour la suite : consigne/question systématiquement
placée en **fin** de prompt, jamais en tête, sur du contenu long.

## Préparation du dataset d'entraînement

### Réduction du coût API

Bascule de Sonnet 5 vers **Haiku 4.5** pour la génération du dataset
(non nécessaire pour cette tâche de génération structurée) — facteur
~3x moins cher. Batch API noté comme piste d'optimisation
complémentaire (50% de réduction supplémentaire), non implémentée pour
ce TP — à explorer plus tard si le besoin se répète à plus grande
échelle.

### 18 types d'incidents, hors des 4 cas de test réservés

Liste couvrant du terrain sysadmin varié (TLS, quotas, kernel,
systemd, cron, SELinux, pare-feu, PXE, RADIUS, NFS, paquets, rotation
de logs, NTP/Kerberos, Ansible, pool de connexions DB, CPU, RAID,
swap) — voir `generer_dataset_entrainement.py` pour la liste complète
(constante `TYPES_INCIDENTS`).

### Génération : séquentiel puis parallélisé

Script `generer_dataset_entrainement.py` :
- Version séquentielle initiale, verbeuse (avancement, ETA)
- Bascule en parallèle contrôlé (`ThreadPoolExecutor`, concurrence
  limitée) après constat que les 504 appels sont indépendants —
  passage d'une estimation ~3h à ~35 minutes réelles
- **Bug rencontré** : erreurs HTTP 499 sous concurrence — diagnostiqué
  comme un timeout **côté client** (SDK Python), pas un rejet serveur,
  aggravé par la charge simultanée des 8 threads. Corrigé en
  augmentant le timeout du client (`timeout=120.0`) et réduisant la
  concurrence de 8 à 5

### Résultat final

**504 exemples générés en 34min59s, 0 erreur**, produit
`dataset_entrainement.json`. Répartition vérifiée via `verif_dataset.py` :
parfaitement équilibrée, 28 exemples par type sur les 18 types.

### Conversion au format Unsloth

Format Alpaca (instruction/input/output) écarté au profit d'un format
**conversationnel** (ChatML/ShareGPT) — recommandé pour les modèles
Instruct comme `qwen3:8b`, contrairement aux modèles de base qui
utilisent plutôt Alpaca.

Décision prise de ne pas suivre la recommandation Unsloth de mix
75% raisonnement / 25% non-raisonnement pour préserver la capacité de
raisonnement de Qwen3 — jugée non prioritaire vu la faiblesse déjà
observée du modèle sur ce point (cf. note 42) et la nature de la tâche
(extraction structurée, pas de raisonnement visible attendu en sortie).

Script `convertir_dataset_unsloth.py` : reformate chaque exemple en
deux tours (`user` = log + consigne, `assistant` = JSON de résumé),
consigne systématiquement placée **après** le log — même correction
que celle apprise sur le cas de test disque plein, appliquée par
précaution à l'ensemble du dataset même si les logs d'entraînement
sont bien plus courts (30-80 lignes).

Vérification post-conversion : 504/504 exemples valides (structure
`conversations` correcte, 5 champs exacts dans chaque réponse
assistant, consigne bien en fin de prompt) — `dataset_entrainement_chatml.json`
prêt pour l'entraînement.

### Rappel — rôle de QLoRA et Unsloth dans ce TP

**QLoRA** : le modèle de base est gelé et quantifié en 4-bit (comme en
Phase 1), seuls de petits adaptateurs LoRA (quelques millions de
paramètres greffés sur certaines couches) sont réellement entraînés —
ce qui rend le fine-tuning possible sur 8 Go de VRAM plutôt que
d'exiger un ré-entraînement complet du modèle.

**Unsloth** : optimise l'exécution de ce processus (kernels GPU
réécrits, gestion mémoire plus efficace) sans changer les principes
de QLoRA — entraînement plus rapide et moins gourmand en VRAM pour un
résultat équivalent.

**Objectif du TP** : vérifier si l'entraînement sur les 504 exemples
corrige les erreurs observées en baseline, en particulier le biais de
prior sur le cas disque plein (5e mode d'échec, note 42).

## Prochaine étape

Configurer et lancer l'entraînement QLoRA proprement dit.

## Compétences pratiquées jusqu'ici

- Distinction overfitting vs biais de prior hérité du pré-entraînement
  vs "lost in the middle" — trois explications plausibles à un même
  symptôme, correctement départagées
- Diagnostic de troncature via un signal indirect (tokens de sortie =
  limite configurée) plutôt que par supposition
- Isolation méthodique d'une variable à la fois (`num_ctx` puis ordre
  du prompt) pour identifier laquelle des deux causait réellement le
  problème, plutôt que de changer les deux en même temps
- Parallélisation contrôlée d'appels API indépendants (concurrence
  limitée, pas de course effrénée), avec verrou (`lock`) pour protéger
  un état partagé entre threads — notion de concurrency vue en théorie
  (Vague 3), rencontrée ici en pratique pour la première fois
- Diagnostic d'une erreur HTTP par élimination (côté client vs côté
  serveur) plutôt que suppose un rejet de l'API
- Arbitrage coût/qualité de modèle (Haiku vs Sonnet) appliqué à une
  tâche réelle, pas juste en théorie
