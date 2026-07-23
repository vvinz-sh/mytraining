# IA — Multimodalité : patches d'image, PDF, positional embedding

## Comment un modèle "texte" peut traiter des images

Tout le mécanisme vu jusqu'ici (logits, softmax, tokens) fonctionne sur
des séquences de tokens. Une image n'a pas de "mots" au départ — il faut
la convertir en quelque chose de comparable à des tokens.

### Patches — les "tokens visuels"

Une image est découpée en petits carrés (**patches**, ex : blocs de 16x16
pixels). Chaque patch est transformé en un vecteur numérique, un peu
comme chaque mot devient un token — sauf qu'ici, un petit carré de
l'image devient l'équivalent d'un "mot visuel".

Exemple : une photo découpée en grille 14x14 = 196 patches. Ces 196
"tokens visuels" rejoignent la **même séquence** que le texte du prompt
— le modèle traite alors une séquence mixte texte + patches, avec le
même mécanisme que pour du texte pur (couches, prédiction du token
suivant), juste avec des tokens venant de deux origines différentes.

### Mécanisme précis : pixel brut → vecteur appris

1. Le patch (16x16 pixels, 3 canaux R/G/B) est "aplati" en une longue
   liste de nombres bruts (16×16×3 = 768 valeurs d'intensité de couleur).
2. Cette liste est transformée par une **couche apprise** (multiplication
   par une matrice de poids, comme pour un neurone classique) en un
   vecteur de taille fixe — une représentation "apprise" du contenu du
   patch, pas juste les pixels bruts.

Différence avec le texte : un token de texte a un vecteur "figé", appris
une fois pour toutes (table de correspondance). La transformation
pixel → vecteur pour l'image est une **vraie couche de calcul**,
exécutée à chaque nouvelle image, pas une table déjà calculée.

### Pourquoi des détails bruts plutôt qu'un résumé global

Donner au modèle une seule information globale toute faite ("il y a un
chat") lui donnerait directement la conclusion, sans qu'il puisse
**construire** cette compréhension lui-même à partir des détails —
écho direct de l'abstraction progressive vue avec les couches de
neurones (bords → formes → parties). En découpant en patches, le modèle
reçoit les détails bruts et construit sa propre compréhension
progressive.

Raison pratique en plus : pour une question spécifique sur l'image
("quelle couleur a le collier du chat ?"), le modèle a besoin d'accéder
aux **détails locaux** précis (le patch contenant le collier) — un
résumé global aurait perdu cette information.

## Le problème de la position — positional embedding

Le mécanisme interne qui traite la séquence de tokens (l'**attention**,
pas encore détaillé) regarde en réalité **tous les tokens en même
temps**, pas dans un ordre séquentiel intuitif — comme recevoir tous les
mots d'une phrase mélangés dans un sac. Sans information de position,
"Le chat mange la souris" et "La souris mange le chat" pourraient être
traités comme équivalents, puisque ce sont les mêmes mots.

⚠️ Point corrigé en cours de session : ce problème n'est **pas
spécifique aux images** — le texte a exactement le même problème, pour
la même raison (l'attention traite tout simultanément). Texte et image
utilisent donc la **même solution** : le **positional embedding**, un
vecteur ajouté à chaque token (mot ou patch) qui encode sa position
("je suis le patch en ligne 3, colonne 8" / "je suis le 3ème mot de la
phrase").

Ce n'est donc pas "le texte n'a pas ce problème" mais "texte et image
partagent le même problème sous-jacent et la même solution", parce que
le mécanisme d'attention est le même pour les deux, indépendamment de
l'origine du token.

## PDF — deux mécanismes combinés, pas un seul

1. **Extraction du texte réel** — si le PDF contient du texte natif (pas
   scanné), il est extrait et traité comme du texte classique (tokens
   normaux, pas de patches).
2. **Rendu visuel en image** (souvent en plus, pas à la place) — chaque
   page est aussi traitée comme une image (patches), pour capturer ce
   que l'extraction de texte seule perd :
   - Tableaux avec colonnes alignées (l'extraction peut casser
     complètement la structure visuelle)
   - Graphiques/schémas (rien à extraire en texte)
   - Mise en page porteuse de sens (titres, notes en petit)
   - PDF scanné (aucun texte réel à extraire, tout passe par la vision,
     éventuellement complété par de l'OCR)

### Exemple concret — pourquoi un tableau financier pose problème en extraction seule

L'extraction de texte brut lit le contenu dans l'ordre où il est
**stocké dans le fichier**, pas forcément dans l'ordre **visuel** des
colonnes. Un tableau à 3 colonnes (Produit, Prix, Quantité) peut être
extrait en texte plat où tous les prix se retrouvent mélangés avec les
quantités — les chiffres sont présents, mais leur **relation
structurelle** (quel prix va avec quel produit/quelle ligne) est perdue.

Le rendu visuel en complément permet d'utiliser l'alignement spatial
(colonnes visuellement alignées) pour reconstituer correctement quelle
valeur appartient à quelle ligne — information que l'extraction de texte
seule ne capture pas.

## À creuser dans une prochaine session

- Le mécanisme d'**attention** lui-même — pourquoi les transformers
  traitent "tout en même temps" plutôt que séquentiellement, et comment
  ça fonctionne concrètement.

## À venir (vague 2)

- [ ] Guardrails et garde-fous en production
- [ ] Coûts et facturation (tokens → €, input vs output)
- [ ] Outils de l'écosystème (LangChain, bases vectorielles, MCP...)
