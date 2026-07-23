# IA — Sécurité au-delà des guardrails : mémorisation et extraction de données d'entraînement

Approfondissement sécurité, volontairement en dehors des guardrails
déjà vus (`securite/25-guardrails-prompt-injection-moindre-privilege.md`)
— un risque qui se situe à un moment différent du pipeline.

## Le phénomène : la mémorisation (memorization)

Un LLM peut-il "recracher" mot pour mot un passage exact de ses données
d'entraînement ? Oui, c'est possible, et le mécanisme est une version
spécifique du **surapprentissage** vu avec le chat blanc/noir — appliqué
ici à un texte précis plutôt qu'à un jeu de données entier.

Si un texte apparaît des milliers de fois **quasi-identique** dans le
corpus d'entraînement, le modèle finit par le **mémoriser** comme un cas
particulier "trop appris", plutôt que d'apprendre le motif général de la
langue à partir de lui. Un texte vu une seule fois ne laisse qu'une
trace statistique diffuse, insuffisante pour se graver spécifiquement.

Différence avec l'hallucination : l'hallucination invente du **faux**,
la mémorisation reproduit du **vrai** contenu, mot pour mot, parce que
littéralement mémorisé plutôt qu'appris comme motif général.

## Quel contenu est le plus à risque de mémorisation

Pas tant le contenu "viral" (réseaux sociaux) — celui-ci subit souvent
des variations (citations tronquées, reformulations, traductions), donc
rarement identique partout.

Le vrai candidat fort : du contenu **copié-collé identique, caractère
pour caractère**, des dizaines de milliers de fois sur des sites
différents — code de bibliothèques open-source populaires, licences
standards (MIT...), textes légaux type CGU dupliqués d'un site à
l'autre. La **répétition exacte et massive** rend la mémorisation quasi
garantie, pas juste probable.

## Le vecteur d'attaque : extraction attack (model inversion)

Scénario concret : une entreprise fine-tune un modèle sur son code
interne. Si un fichier contenant une vraie clé API ou un identifiant
sensible apparaît de façon répétitive (ex : un template copié dans
plusieurs projets internes), le modèle peut la mémoriser.

Un attaquant (ou un employé, volontairement ou non) peut alors tenter de
faire "recracher" ce contenu — souvent en donnant le **début** d'un
texte soupçonné d'avoir été mémorisé, et en laissant le modèle
"compléter". Ça exploite directement la génération autorégressive : le
modèle continue le texte le plus probable, qui se trouve être une
mémorisation exacte plutôt qu'une génération statistique normale.

## Pourquoi les guardrails classiques ne protègent pas contre ça

Rappel du TP sécurité (guardrail pattern + guardrail sémantique) : les
deux fonctionnent parce qu'on connaît **à l'avance** ce qu'on cherche —
un format prévisible (regex) ou une base d'exemples connus
(similarité).

Pour la mémorisation, impossible d'écrire une regex ou de constituer une
base d'exemples : on ne sait **jamais à l'avance** quel texte précis a
été mémorisé parmi des milliards de documents d'entraînement — la
découverte ne se fait qu'**après coup**, en le voyant sortir, ou en
testant délibérément (recherche en sécurité). Un guardrail classique
suppose de savoir *quoi* chercher ; ici, le "quoi" est inconnu tant que
ça ne s'est pas produit une première fois.

## Où se joue la vraie défense : en amont, à l'entraînement

Puisque le guardrail de sortie ne peut pas prévenir un phénomène
inconnaissable à l'avance, la défense se joue **avant**, au moment de
l'entraînement lui-même.

### 1. Déduplication du corpus d'entraînement

Détecter et supprimer les textes en quasi-doublons massifs avant même
d'entraîner — réduire la répétition à la source réduit directement le
risque de mémorisation (logique directe avec le mécanisme identifié
plus haut).

### 2. Differential privacy pendant l'entraînement

Technique mathématique ajoutant un **bruit calibré aux gradients**
pendant l'ajustement des poids, garantissant qu'aucun exemple
individuel ne peut influencer les poids de façon disproportionnée par
rapport aux autres — une forme de "moindre privilège" appliquée à
chaque donnée d'entraînement individuelle, pas à un compte utilisateur.

### Le compromis de la differential privacy — confidentialité vs performance

Le bruit qui empêche le modèle d'apprendre des motifs **trop
spécifiques** à un exemple individuel empêche aussi d'apprendre des
motifs rares mais légitimes (tournure de phrase peu commune, fait vrai
mais peu répété). Le modèle devient globalement moins précis, moins
capable de nuances fines.

Écho avec d'autres compromis déjà vus dans le repo :
- Quantization : mémoire ↓, précision ↓
- ANN/HNSW : vitesse de recherche ↑, garantie de précision ↓ (95-99%)
- Differential privacy : confidentialité ↑, performance générale ↓

Aucun de ces mécanismes n'est gratuit — toujours un axe sacrifié pour
gagner sur l'autre.

## Résumé

1. La mémorisation est un phénomène distinct de l'hallucination
   (reproduction de vrai contenu, pas invention de faux).
2. Le contenu massivement dupliqué à l'identique (code, licences) est
   le plus à risque.
3. L'extraction attack exploite directement la génération
   autorégressive pour faire "recracher" du contenu mémorisé.
4. Les guardrails classiques (pattern, sémantique) ne protègent pas
   contre ce risque — le "quoi chercher" est inconnaissable à l'avance.
5. La vraie défense se situe en amont, à l'entraînement (déduplication,
   differential privacy), pas en sortie du modèle.
