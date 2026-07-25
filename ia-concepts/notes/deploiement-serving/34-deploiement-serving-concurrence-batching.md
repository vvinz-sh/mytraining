# IA — Vague 3 (MLOps/Ops) : Déploiement & serving

Session théorique partie du serveur MCP déjà construit
(`exercices/tp-rag-mcp/`) comme point de départ concret.

## Le problème de la concurrence

Un process Python classique (comme `serveur_mcp_notes.py`) traite les
requêtes **séquentiellement** — rien n'est perdu ou rejeté, mais les
requêtes s'accumulent en file d'attente, et la latence perçue par les
derniers arrivés grandit **linéairement** avec le nombre de requêtes
simultanées.

Exemple concret : si chaque requête `search_notes` prend ~200ms
(embedding + recherche Chroma), et que 10 requêtes arrivent en même
temps sur un seul process, la 10ᵉ personne attend ~2 secondes (10 ×
200ms) avant sa réponse, même si son traitement individuel ne prend
que 200ms.

## Scaling horizontal — plusieurs copies en parallèle

Solution naturelle, écho direct du parallélisme vu ailleurs (multi-head
attention, forêt aléatoire, Ansible sur plusieurs hosts) : faire tourner
**plusieurs copies indépendantes** du serveur, chacune traitant une
requête en parallèle des autres, plutôt qu'une seule instance
séquentielle.

Avec 3 copies, la charge se répartit environ par 3 — la 10ᵉ personne
attend ~0,7s au lieu de 2s.

### Le composant qui répartit : le load balancer

Décide "quelle copie reçoit cette requête" — terme déjà utilisé comme
analogie ailleurs dans le repo (routing multi-modèles, comportement des
guardrails), mais ici c'est littéralement la brique d'infra à ajouter
devant les copies du serveur.

### ⚠️ Le coût caché du scaling horizontal naïf

Chaque copie charge son **propre exemplaire** du modèle en mémoire au
démarrage — avec 3 copies, coût mémoire ×3 pour un modèle strictement
identique (les poids sont figés en inférence, aucune raison qu'ils
diffèrent entre process). Un vrai gaspillage si rien ne mutualise le
modèle chargé entre les copies.

Solution plus sophistiquée : des frameworks de serving dédiés (**vLLM**,
**TGI**, déjà cités dans le panorama outils) sont conçus spécifiquement
pour éviter cette duplication — ils gèrent le partage du modèle en
mémoire et le traitement de plusieurs requêtes en parallèle sur une
seule instance de poids chargés, plutôt que de dupliquer bêtement le
process entier.

## Batching — exploiter le parallélisme du GPU sur plusieurs requêtes

### Pourquoi une seule requête sous-utilise un GPU

Rappel : un GPU excelle sur les multiplications de matrices massives
grâce à des milliers de cœurs travaillant en même temps sur des données
différentes (voir `hardware/12-...md`). Envoyer **une seule** requête au
GPU n'utilise qu'une infime fraction de ces cœurs — le reste de la
puissance de calcul est gaspillé.

Point de vigilance : ce n'est pas le même problème que "GPU plus lent
que CPU en séquentiel" (vu pour une tâche où chaque étape dépend de la
précédente, comme la génération token par token pour **une seule**
requête). Ici, les 10 requêtes sont **indépendantes** entre elles —
aucune ne dépend du résultat d'une autre.

### Le principe du batching

Regrouper plusieurs requêtes indépendantes en un seul paquet (une
matrice à 10 lignes plutôt qu'une seule requête isolée), pour que le
GPU les traite **toutes en un seul passage**, exploitant tout son
parallélisme au lieu de le laisser inutilisé.

Nuance importante : le batching parallélise plusieurs requêtes
**différentes**, chacune continuant sa propre génération en interne
(token par token, toujours séquentiel pour elle-même) — mais toutes
ensemble à chaque étape, pas une seule requête qui se paralléliserait
elle-même.

### Le compromis : dynamic batching

Batcher n'est pas gratuit — il faut **attendre** un peu pour accumuler
plusieurs requêtes avant de les envoyer ensemble (sinon batcher une
requête seule n'apporte aucun gain).

**Dynamic batching** (implémenté dans vLLM/TGI) : attendre un court
instant (quelques millisecondes) pour regrouper les requêtes arrivées
entre-temps, avant de lancer le calcul groupé — compromis entre latence
individuelle (attendre un peu) et débit global (traiter plus de
requêtes efficacement par unité de temps).

⚠️ Piège si mal calibré : une requête isolée qui attend inutilement un
hypothétique groupe qui ne vient jamais subit une latence ajoutée sans
aucun gain en retour. D'où l'usage d'un **timeout de batching** —
attendre au maximum quelques millisecondes, puis lancer le traitement
même seul, plutôt qu'attendre indéfiniment.

## Résumé de la session

1. Un process séquentiel accumule les requêtes (latence linéaire), ne
   les rejette pas.
2. Scaling horizontal (plusieurs copies + load balancer) réduit la
   latence, mais duplique le coût mémoire du modèle si fait
   naïvement.
3. Des frameworks de serving dédiés (vLLM, TGI) résolvent ce gaspillage
   en partageant le modèle entre requêtes.
4. Le batching exploite le parallélisme du GPU sur plusieurs requêtes
   indépendantes simultanées — pas la même chose que paralléliser une
   seule requête séquentielle.
5. Le dynamic batching introduit un compromis latence/débit, calibré
   par un timeout pour ne pas pénaliser une requête isolée.
