# IA — Sycophancie : la complaisance qui casse une bonne réponse

Complète la note 11 (hallucinations et sur-confiance) — un troisième
mode d'échec, distinct des deux premiers, découvert en testant
`llama3.1:8b` en local (TP `tp-llm-local`).

## Le scénario qui a révélé le phénomène

Question posée à un petit LLM local : *"qui a créé Claude ?"* — deux
mauvaises réponses différentes et confiantes (Meta AI, puis Google).
En lui proposant un "joker", il trouve enfin la bonne réponse
(Anthropic). Mais à la simple question *"certain de cette réponse ?"* —
sans aucune information nouvelle, juste un doute exprimé — il abandonne
la bonne réponse et repart sur "je ne sais pas vraiment".

## Ce que c'est, et ce que ce n'est pas

- **Hallucination** (note 11) : le modèle invente un contenu faux face
  à un vide de connaissance, avec un ton tout aussi confiant que s'il
  disait vrai.
- **Sycophancie** : le modèle **abandonne une réponse correcte** sous
  simple pression sociale (désaccord, doute, reformulation insistante
  de l'utilisateur) — sans qu'aucune nouvelle information ne
  justifie ce changement.

Les deux se ressemblent en surface (le ton ne reflète jamais la vérité
du contenu), mais les mécanismes et les moments où ils apparaissent
sont différents : l'hallucination naît d'un vide de connaissance ;
la sycophancie naît d'une **interaction sociale** avec l'utilisateur,
même quand la connaissance sous-jacente était correcte.

## Pourquoi techniquement : un effet de bord du RLHF

Pendant l'entraînement par feedback humain (RLHF), des évaluateurs
notent les réponses du modèle. Statistiquement, une réponse qui **cède
face à un désaccord poli** ("tu as raison, je me suis trompé") est
souvent mieux notée par un humain qu'une réponse qui **insiste et
contredit** — même quand insister serait la bonne chose à faire. Le
modèle apprend donc, sans qu'on le lui dise explicitement, que
"céder = bien noté", et ça se généralise à des situations où céder
est objectivement une erreur.

C'est parfois appelé le "yes-man problem" dans la littérature sur
l'alignement — un sujet de recherche actif, pas un bug isolé de ce
petit modèle en particulier.

## La parade

Même réflexe que pour l'hallucination : une réponse qui change ne
veut pas dire qu'elle est devenue plus juste. Face à un modèle (ou une
personne) qui revient sur une affirmation, la question à se poser
n'est pas "il/elle a l'air plus confiant(e) maintenant" mais "qu'est-ce
qui, concrètement, justifie ce changement ?" — si la réponse est
"rien de nouveau, juste mon insistance", c'est un signal d'alarme, pas
une validation.

## Quatrième mode observé : dégénérescence par répétition

Test ultérieur (toujours en session ludique) : demander à `qwen3:8b`
de réciter les 151 Pokémon de la 1re génération, en français. Résultat
au-delà d'un certain point : le modèle se bloque sur un seul nom
inventé ("Cocodémon", type "Serpent") répété en boucle jusqu'à la fin
de la liste (151 fois), tout en refusant d'admettre l'erreur quand
challengé.

**Mécanisme** : différent des trois précédents. Ce n'est ni une
hallucination isolée, ni de la sycophancie — c'est de la
**dégénérescence par répétition** (parfois appelée "repetition trap") :
plus un modèle génère un texte long, plus chaque token généré
influence fortement la prédiction du suivant. Le modèle peut se
retrouver piégé dans une boucle où répéter le token précédent devient
statistiquement "la suite la plus plausible" du texte qu'il vient
lui-même de produire — un effet qui s'aggrave avec la longueur de la
génération, surtout sur un petit modèle avec moins de garde-fous
internes.

**Le lien avec la langue n'est pas un hasard** : les noms Pokémon
localisés en français sont beaucoup moins représentés dans les données
d'entraînement que les noms anglais (contenu à poids largement
anglophone). Le modèle a assez de matière pour bien démarrer, puis
s'effondre dès qu'il manque de connaissance solide — et comble le vide
en répétant un nom plausible plutôt que d'admettre l'incertitude ou de
varier ses inventions.

**Point intéressant, presque contradictoire avec le mode 3** : ici, le
modèle **campe sur une erreur évidente** au lieu de céder face à la
contestation — l'inverse de la sycophancie observée plus haut. Ça
confirme que ces comportements ne sont pas des "traits de caractère"
cohérents chez le modèle (tantôt trop conciliant, tantôt trop buté) —
c'est un système sans confiance calibrée, dont la réaction dépend
fortement du contexte précis du prompt, pas d'un principe stable.

## Cinquième mode observé : biais de prior sur signal affaibli (contexte long)

Contexte différent des précédents : pas une session ludique, mais le
test de baseline du TP `tp-llm-local` Phase 2 (avant fine-tuning
QLoRA). `qwen3:8b` analyse un vrai log d'incident de 520 lignes
(saturation disque en cascade, `tp-ansible-agent`) et doit produire un
résumé structuré en 5 champs.

**Résultat** : diagnostic complètement à côté — "attaque par force
brute SSH", alors que l'incident réel est une saturation de `/var` par
un job de sauvegarde, provoquant l'échec en cascade d'Apache. Aucune
mention du disque ou de l'espace disque dans la réponse.

**Mécanisme, combinaison de deux phénomènes distincts** :

1. **"Lost in the middle"** — biais positionnel documenté chez les
   LLM sur contexte long : le contenu en tout début et toute fin d'un
   texte est mieux exploité que celui du "milieu". Ici, la vraie cause
   racine (lignes ~21-30/520, donc plutôt en début) s'est retrouvée
   affaiblie dans l'attention du modèle malgré sa position pourtant
   précoce — signe que la capacité d'attention à longue portée d'un
   petit modèle 8B peut être plus limitée que ce que le "lost in the
   middle" classique décrit sur des modèles plus gros.

2. **Biais de prior hérité du pré-entraînement** — une fois le signal
   réel affaibli, le modèle ne répond pas "je ne sais pas" : il
   retombe sur l'association la plus statistiquement familière dans
   son corpus d'entraînement pour les bribes encore visibles
   ("connexions SSH répétées + erreurs de service" = un sujet très
   représenté dans la littérature sécurité/sysadmin sur le web),
   même si cette explication ne colle pas au reste du log.

**Différence avec l'overfitting** : à ce stade, le modèle n'a subi
*aucun* entraînement de notre part — l'overfitting suppose un écart
entre données d'entraînement et données de test, qui ne s'applique pas
ici puisqu'on est en pure inférence sur le modèle de base. Le biais
observé vient du pré-entraînement initial de Qwen, pas d'un fine-tuning
qu'on n'a pas encore fait.

**Portée méthodologique** : ce résultat de baseline (avant QLoRA) sert
justement de point de comparaison — la Phase 2 permettra de vérifier
si le fine-tuning sur des exemples variés corrige spécifiquement ce
type d'erreur (signal affaibli + bascule vers un prior familier mais
faux), ou si le problème persiste malgré l'entraînement.

## Récap des cinq modes d'échec observés dans une seule session de test

| Mode d'échec | Déclencheur | Exemple observé |
|---|---|---|
| Hallucination pure | Vide de connaissance (mot inventé) | Invente une fiche Pokémon complète pour "Caparaïce" |
| Connaissance figée dans le temps | Fait absent/rare dans les données d'entraînement | Créateur de Claude — deux réponses fausses différentes |
| Sycophancie | Pression sociale (doute exprimé) | Abandonne "Anthropic" (correct) face à "certain de cette réponse ?" |
| Dégénérescence par répétition | Génération longue + rareté linguistique (français) | Boucle sur "Cocodémon" x151, refuse de se corriger |
| Biais de prior sur signal affaibli | Contexte long + signal réel dilué (lost in the middle) | "Attaque SSH" diagnostiquée à la place d'une saturation disque réelle |

Point commun aux cinq : **le ton de confiance n'a jamais été un
indicateur fiable** — ni pour détecter l'erreur, ni pour valider une
correction.
