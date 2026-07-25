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

## Conteneurisation (Docker) — appliquée aux bugs déjà vécus

Session partie des 3 bugs réels du TP RAG/MCP (torch/CUDA, distro WSL
par défaut, Chroma/DrvFs) pour évaluer ce que Docker aurait résolu.

### Ce que Docker aurait résolu — et ce qu'il n'aurait pas résolu

- **Distro WSL par défaut incorrecte** → résolu : un conteneur définit
  un seul environnement explicite, aucune ambiguïté possible entre
  plusieurs environnements comme avec `wsl.exe` sans précision.
- **Chroma/DrvFs (Permission denied)** → résolu : le système de
  fichiers à l'intérieur d'un conteneur est toujours un vrai filesystem
  Linux natif, jamais un montage Windows, peu importe l'OS hôte.
- **torch qui installe CUDA complet** → **pas résolu** : le problème
  venait de la commande d'installation elle-même (`pip install
  sentence-transformers` tire torch+CUDA par défaut), pas de
  l'environnement qui l'exécute. Un Dockerfile avec la même commande
  aurait reproduit le même bug — la solution reste identique dans les
  deux cas (spécifier l'index PyTorch CPU-only explicitement).

### Vocabulaire : Dockerfile, image, conteneur

- **Dockerfile** : recette texte, suite de commandes séquentielles
  (`RUN pip install...`, `COPY fichier.py`), exécutées dans l'ordre à
  partir d'une base propre — pas un parallèle avec un playbook Ansible
  (qui converge vers un état sur un système **existant**) : un
  Dockerfile construit **from scratch**, à chaque build. Plus proche
  d'un script bash qui construit quelque chose de A à Z, une seule fois.
- **Image** : instantané figé et portable de l'environnement, produit
  par le build du Dockerfile.
- **Conteneur** : instance en cours d'exécution d'une image.

### Le système de couches — mise en cache par contenu

Chaque ligne d'un Dockerfile devient une "couche" indépendante, mise en
cache. Si une ligne ne change pas, Docker réutilise la couche déjà
construite plutôt que de tout refaire.

**Ordre optimal** : dépendances (rarement modifiées, lourdes à
réinstaller) **avant** le code applicatif (modifié souvent, léger à
copier). Inverser l'ordre forcerait un `pip install` complet à chaque
modification du code — piège courant chez les débutants Docker.

**Détection par contenu, pas par date** : Docker compare le **contenu**
des fichiers (hash), pas leur horodatage. Si un dossier régénéré (ex :
`chroma_notes_db/` après un `index_notes.py` relancé) a un contenu
strictement identique au précédent, la couche correspondante reste en
cache, même si le script de génération a bien tourné entre-temps — écho
direct du principe d'idempotence déjà vu (Ansible, Git par hash de
contenu).

### Nuance cruciale : COPY (build) vs volume (runtime)

`COPY` fait une copie brute de fichiers **une seule fois, pendant le
build** — aucun verrouillage de fichiers en jeu à ce moment, donc copier
depuis un montage Windows (`/mnt/c/...`) fonctionnerait sans problème
DrvFs, même si le contenu source vient d'un système de fichiers Windows.

Le bug DrvFs resurgirait seulement si `chroma_notes_db/` était monté en
**volume** (accès continu au runtime) plutôt que copié une fois au
build — c'est à ce moment que Chroma ouvre réellement la base et tente
son verrouillage de fichiers. Distinction clé : copier une fois au
build (sans risque) vs monter en continu au runtime (risque si le
volume pointe vers un montage Windows).

## Spécificités Docker propres à l'IA

### La taille des images — un écart de plusieurs ordres de grandeur

Une image Docker classique (appli web) pèse souvent quelques centaines
de Mo. Une image contenant un vrai LLM peut dépasser 20-30 Go —
rien que les poids d'un modèle 8B en FP16 pèsent déjà ~16 Go (8
milliards × 2 octets, calcul déjà vu dans `hardware/12-...md`), avant
même d'ajouter Python, CUDA, PyTorch et les bibliothèques nécessaires.

⚠️ Point de vigilance : la taille sur **disque** (l'image) et la
mémoire au **runtime** (RAM/VRAM pendant l'exécution) sont deux choses
différentes, à ne pas confondre — les poids pèsent sur les deux, mais
séparément.

### Conséquences concrètes du même ordre que le TP déjà vécu

Espace disque (multiplié par la taille de l'image, potentiellement sur
chaque serveur en scaling horizontal — même problème de duplication que
le coût mémoire ×3 vu plus haut, mais côté stockage) et temps de
téléchargement/déploiement (dizaines de minutes plutôt que secondes).

### Bonne pratique spécifique IA : séparer les poids du reste de l'image

Plutôt que d'inclure les poids **dans** l'image (`COPY poids.safetensors
.`), les charger depuis un stockage externe (S3, volume monté, registre
de modèles) **au démarrage du conteneur**, pas au build.

Pourquoi, malgré le cache par couches qui gère déjà bien ce cas si
l'ordre est bon (poids en premier, code après) : le vrai problème
apparaît au **scaling horizontal** — si les poids sont dans l'image,
chaque nouvelle machine qui démarre une copie doit télécharger toute
l'image (poids inclus) avant de démarrer. Avec des poids externes,
l'image reste légère et rapide à distribuer, et les poids peuvent être
mis en cache **une seule fois par machine hôte**, partagés entre
plusieurs conteneurs sur cette machine plutôt que dupliqués dans chaque
image téléchargée — le même problème de duplication que le scaling
horizontal naïf (RAM), mais appliqué ici au disque/réseau.

## Résumé de la session Docker

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
