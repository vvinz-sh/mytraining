# IA — Chunking en profondeur : chevauchement, taille adaptée, chunking par structure

Approfondissement du TP RAG/MCP, sur un point qu'on avait appliqué sans
détailler pendant le TP (`ia-concepts/exercices/tp-rag-mcp/tp-rag-mcp-notes-resultat.md`).

## Pourquoi découper du tout

Un embedding transforme un texte en **un seul vecteur**. Donner un
fichier entier (ex : 3000 mots couvrant 5 sujets différents) à un modèle
d'embedding produirait un seul vecteur "moyenne" de tout le contenu —
flou, peu utile pour retrouver précisément un passage précis. D'où le
découpage en chunks plus petits, chacun avec son propre vecteur ciblé.

## Le rôle du chevauchement

**Sans chevauchement**, un découpage strict par blocs peut couper une
phrase en plein milieu :
```
Chunk 1 (mots 1-300)   : "...QLoRA combine la quantization avec"
Chunk 2 (mots 301-600) : "LoRA pour réduire la mémoire nécessaire..."
```
Ni l'un ni l'autre chunk ne contient la phrase complète — l'embedding
de chacun est dégradé, ne capturant qu'une moitié d'idée.

**Avec un chevauchement** (ex : 50 mots), chaque nouveau chunk répète la
fin du précédent avant de continuer, donc la phrase complète apparaît
intacte dans au moins un chunk, même si elle tombait sur la frontière.

Mécanisme dans le code : le pas d'avancement est `taille - chevauchement`
(ex : 300 - 50 = 250), pas `taille` — chaque chunk démarre 250 mots après
le précédent, créant une zone partagée de 50 mots entre chunks
consécutifs.

## Le compromis à trouver — pas "plus de chevauchement = toujours mieux"

Un chevauchement disproportionné (ex : 250 sur 300 mots, donc un pas
d'avancement de seulement 50) produit des chunks **quasi redondants**
(83% de contenu partagé) :
- Plus de chunks générés au total
- Temps de calcul des embeddings plus long
- Gaspillage de stockage sans gain réel de qualité de recherche
  au-delà d'un certain point (le chevauchement ne fait plus que dupliquer,
  sans capturer d'idée supplémentaire coupée)

Valeur courante en pratique : un chevauchement d'environ 15-20% de la
taille du chunk (ex : 50 sur 300) — assez pour couvrir une phrase à
cheval sur la frontière, sans duplication excessive.

## ⚠️ Piège important : "dense" ne veut pas dire "chunks plus petits"

Intuition initiale à corriger : on pourrait penser qu'un contenu dense
(comme la note sur l'attention Q/K/V) bénéficie de chunks plus **petits**
pour "chercher plus finement". C'est l'inverse dans ce cas précis.

Pour du contenu où les idées ont de **fortes dépendances entre elles**
(la définition de "Query" n'a de sens qu'avec celles de "Key" et
"Value"), des chunks plus petits risquent d'**isoler** une notion de ses
voisines indispensables — produisant un embedding **incomplet**, qui
capture mal le vrai sens du passage. Résultat : la recherche se dégrade,
alors qu'on cherchait à l'améliorer.

### Le vrai critère : cohérence locale, pas densité

Pas "dense = petit chunk", mais : **est-ce que ce passage garde du sens
tout seul, ou a-t-il besoin de ses voisins pour être compris ?**

- **Contenu à dépendances fortes** (raisonnement qui s'enchaîne sur
  plusieurs phrases, comme l'attention) → chunks **plus grands**, pour
  garder les dépendances ensemble.
- **Contenu procédural, étapes indépendantes** (ex : TP avec étapes
  numérotées "1. Installer, 2. Configurer, 3. Tester") → chunks **plus
  petits** tolérables, chaque étape portant son propre contexte minimal
  dans sa formulation même (numéro + titre), se comprenant seule.

## Chunking adaptatif (par structure) — au-delà du découpage uniforme

Technique de RAG plus avancée : au lieu d'une taille fixe unique pour
tout le corpus (le découpage à 300 mots appliqué uniformément dans le
TP), découper **selon la structure du document** — par section (titres
Markdown `##`), par étape numérotée, ou par paragraphe naturel, plutôt
que par un simple compte de mots aveugle.

Un chunker structuré détecterait par exemple les titres Markdown et
découperait à ces frontières naturelles, donnant des chunks de taille
**variable mais sémantiquement cohérents** — plutôt que des coupures
arbitraires au milieu d'une section.

Application concrète au repo `mytraining` : découper les notes
conceptuelles (attention, couches) par grande section `##`, et les TP
procéduraux par étape numérotée — amélioration possible par rapport au
découpage uniforme à 300 mots utilisé dans le premier TP (qui a très
bien fonctionné comme test rapide, mais reste une simplification).

## Chunking sémantique — l'adaptation automatique

Question de suite logique : l'adaptation de la taille/coupure des
chunks au contenu (vue plus haut) est-elle manuelle ou automatisable ?
Réponse : les deux existent, avec un spectre entre chunking basique
(nombre de mots fixe, ce qu'on a fait dans le TP) et chunking
sémantique (automatique, basé sur les embeddings eux-mêmes).

### Principe

Calculer l'embedding de **chaque phrase** d'un document, puis mesurer la
similarité entre chaque phrase et la **suivante**. Tant que les phrases
parlent du même sujet, la distance reste faible (proche). Au moment où
le document **change de sujet**, la distance fait un **bond** — ce
saut de distance devient le signal pour placer une frontière de chunk,
détectée automatiquement plutôt que décidée à la main par un humain qui
lirait chaque note.

### Toujours besoin d'une calibration

Ce n'est pas magique pour autant : il faut définir un **seuil** ("à
partir de quelle distance je considère que c'est un vrai changement de
sujet") — même type de calibration empirique que pour le guardrail de
sécurité vu dans `ia-concepts/exercices/tp-securite/tp-securite-rag-mcp-guardrails-draft.md`. Plus coûteux
en calcul que le découpage par mots fixe, puisqu'il faut calculer un
embedding par phrase avant même de décider où couper.

### Pourquoi ça reste praticable, contrairement à l'attention complète

Le chunking sémantique ne compare que des **paires consécutives**
(phrase 1 avec phrase 2, phrase 2 avec phrase 3...) — pour N phrases, ça
fait N-1 comparaisons, une croissance **linéaire**. L'attention, elle,
compare chaque token à **tous les autres** (croissance **quadratique**,
N² comparaisons, voir `20-mecanisme-attention-qkv-multihead.md`).

Pour un document de 100 phrases : le chunking sémantique fait ~99
comparaisons "voisin par voisin", alors qu'une comparaison de type
attention en ferait 10 000 ("tout contre tout") — écart qui grandit
encore plus vite à mesure que le document s'allonge. C'est cette
différence de **structure de comparaison** (voisin par voisin vs tout
contre tout), pas juste "moins de données", qui rend le chunking
sémantique praticable même sur de gros corpus, là où un mécanisme de
type attention appliqué à l'échelle d'un document entier serait
prohibitif.

## Résumé

1. Le chevauchement évite qu'une idée soit coupée net à la frontière
   entre deux chunks.
2. Trop de chevauchement gaspille calcul/stockage sans gain de qualité
   au-delà d'un certain seuil.
3. Le bon critère de taille de chunk n'est pas la densité du contenu,
   mais sa cohérence locale (dépendances entre idées voisines).
4. Le chunking par structure (sections, étapes) dépasse le simple
   découpage uniforme par nombre de mots, en respectant les frontières
   naturelles du document.
