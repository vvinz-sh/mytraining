# IA — Hardware : quantization, GPU vs CPU, CUDA vs Tensor Cores

Première session de la vague 2 (approfondissement).

## Pourquoi un modèle mange autant de RAM/VRAM

Exemple : un modèle à 70 milliards de paramètres nécessite ~140 Go de
VRAM juste pour charger les poids, avant même de traiter une requête.

Chaque poids est un nombre stocké en mémoire. Le format de stockage
détermine l'espace utilisé par paramètre :
- **FP32** (précision simple, format "classique") : 4 octets/nombre
- **FP16 / BF16** (demi-précision) : 2 octets/nombre — utilisé par la
  plupart des modèles récents en inférence

70 milliards × 2 octets (FP16) = 140 Go, au lieu de 280 Go en FP32.

## Quantization — le compromis mémoire vs qualité

FP16 stocke une version **arrondie** des poids par rapport à FP32 (moins
de décimales précises), mais avec une perte de qualité quasi
imperceptible une fois le modèle déjà entraîné — comme arrondir
19,99847€ à 20€ sur une étiquette.

**Quantization** = pousser cet arrondi encore plus loin (INT8 = 1
octet/poids, INT4 = 4 bits/poids...). Le compromis n'est pas linéaire :
- FP32 → FP16 : perte quasi imperceptible
- FP16 → INT8 : commence à se sentir sur des tâches complexes
- INT8 → INT4 : dégradation nette sauf techniques de quantization
  sophistiquées (calibration statistique, correction d'erreur)

Analogie : arrondir à la dizaine la plus proche fait que 17€, 20€ et 24€
deviennent indiscernables — le modèle perd sa capacité à distinguer des
situations proches, ce qui se traduit par plus d'erreurs de raisonnement
et d'incohérences à mesure que la précision baisse.

## Pourquoi le GPU plutôt que le CPU

Pas une question de "mieux gérer les flottants" (un CPU moderne le fait
très bien aussi) — la vraie différence est le **parallélisme massif**.

- **CPU** : quelques cœurs (4 à 32 en général), chacun très puissant et
  polyvalent, optimisé pour l'exécution séquentielle rapide.
- **GPU** : des milliers de cœurs beaucoup plus simples, conçus pour
  faire **la même opération en même temps sur des milliers de valeurs**.

L'opération de base d'un réseau de neurones (la somme pondérée vue en
ML) est en réalité une **multiplication de matrices**, qui se décompose
naturellement en millions de petits calculs indépendants — exactement le
type de travail où le parallélisme massif du GPU écrase le CPU.

⚠️ Nuance importante : le GPU n'est **pas meilleur en général**. Sur une
tâche **séquentielle pure** (chaque étape dépend absolument du résultat
de la précédente, impossible à paralléliser), le GPU est **plus lent**
que le CPU — chaque cœur GPU individuel est bien plus faible qu'un cœur
CPU, et sans pouvoir compenser par le nombre (un seul cœur utilisé à la
fois), le CPU gagne largement. C'est pour ça qu'un serveur garde toujours
un CPU en plus du GPU : le CPU gère tout ce qui entoure le calcul IA
(fichiers, réseau, orchestration), le GPU se concentre sur les
multiplications de matrices massives.

## CUDA vs Tensor Cores — ne pas confondre

- **CUDA** = plateforme **logicielle** NVIDIA qui permet de programmer un
  GPU pour du calcul généraliste (pas seulement l'affichage graphique,
  son usage historique). Interface, pas un composant physique.
- **Tensor Cores** = unité de calcul **matérielle** spécialisée, présente
  dans les GPU NVIDIA récents (depuis Volta, 2017), en plus des cœurs
  CUDA classiques. Un cœur CUDA fait une opération à la fois
  (multiplication OU addition). Un Tensor Core fait directement une
  **multiplication + addition de matrices entières en une seule
  instruction matérielle** — taillé sur mesure pour l'IA.

Analogie : cœurs CUDA = milliers de petits scripts génériques capables
d'un calcul basique chacun. Tensor Cores = un ASIC dédié (comme un ASIC
de minage crypto) intégré à côté, beaucoup plus rapide sur une tâche
précise mais incapable de faire autre chose.

### Pourquoi des Tensor Cores en plus des cœurs CUDA, plutôt que rendre les cœurs CUDA plus rapides

Principe de **spécialisation vs polyvalence** :
- Un cœur CUDA classique est polyvalent (addition, multiplication,
  comparaison...) — pour une multiplication de matrices, il doit
  enchaîner plusieurs instructions séparées via un circuit générique.
- Un Tensor Core sacrifie cette polyvalence pour ne faire qu'une seule
  chose, câblée directement dans le silicium : multiplier-additionner
  des blocs de matrices en une seule instruction.

Rendre les cœurs CUDA généralistes "plus rapides" pour rattraper cette
efficacité serait très inefficace — comme essayer de rendre un couteau
suisse aussi rapide qu'un couteau de chef sur une tâche de coupe précise.

### Hiérarchie de spécialisation (récap)

```
CPU (polyvalent, séquentiel)
  → GPU / cœurs CUDA (parallèle massif, mais généraliste)
    → Tensor Cores (parallèle ET ultra-spécialisé sur une seule opération)
```

Chaque niveau sacrifie de la polyvalence pour gagner en performance sur
une tâche précise — l'IA, avec ses milliards de multiplications de
matrices identiques, justifie ce sacrifice extrême.

## À venir (vague 2)

- [ ] VRAM comme goulot d'étranglement (lien direct avec nombre de
      paramètres et matériel nécessaire)
- [ ] Paramètres de génération (`temperature`, `top_p`/`top_k`)
- [ ] Multimodalité, guardrails, coûts/facturation
- [ ] Outils de l'écosystème (LangChain, bases vectorielles, etc.)
