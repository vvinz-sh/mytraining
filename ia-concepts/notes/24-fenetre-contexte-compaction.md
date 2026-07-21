# IA — Fenêtre de contexte en pratique : compaction, résumé progressif

Dernier point manquant de la vague 2 ("paramètres et fonctionnement
pratique").

## Le problème : une conversation qui dépasse la fenêtre de contexte

Une conversation longue (comme nos sessions de formation) accumule des
tokens jusqu'à potentiellement dépasser la fenêtre de contexte du
modèle. Deux mauvaises solutions possibles :

- **Rejet pur et simple** une fois la limite atteinte (bloquant).
- **Troncature brutale** (jeter les premiers messages, garder juste les
  N derniers) — perd des informations potentiellement importantes sans
  aucune discrimination sur ce qui compte ou pas (ex : perdre le niveau
  RHCSA de l'utilisateur, ses préférences, le design d'un TP posé il y a
  longtemps).

## La solution : la compaction (résumé progressif)

Terme officiel côté Anthropic : **compaction**. Plutôt que de tout garder
brut ou de couper aveuglément, le système remplace automatiquement le
contenu le plus ancien par un **résumé concis**, gardant le contexte actif
léger, tout en préservant l'essentiel du fil de la conversation.

Points pratiques confirmés par la documentation officielle :
- Se déclenche avant la limite dure (autour de ~83,5% de la fenêtre de
  contexte utilisée), avec de la marge.
- L'historique complet reste consultable en remontant dans la
  conversation — seul le **contexte de travail actif** (ce que le modèle
  utilise réellement pour générer sa réponse) est compacté, pas
  l'affichage visible pour l'utilisateur.
- Comportement systémique, ne peut pas être désactivé.
- Trade-off assumé : les résumés perdent inévitablement des détails.
  Même si les points clés sont bien identifiés, des détails précis
  (valeurs exactes, instructions fines) peuvent être compressés ou omis.

## Distinction avec le "memory tool"

La documentation mentionne aussi un mécanisme différent : le **memory
tool** — stocker des informations dans des **fichiers persistants en
dehors de la fenêtre de contexte**, consultables à la demande plutôt que
reconstruits depuis un résumé compressé. Différent de la compaction :
- **Compaction** = résumé automatique et systémique du contexte de
  conversation, avec perte de détail inévitable.
- **Memory tool** = stockage explicite de faits dans des fichiers
  externes, récupérables intégralement à la demande (pas de perte par
  résumé).

## Application concrète à notre repo de formation

Bonne pratique déjà appliquée sans le savoir explicitement : noter
systématiquement chaque session dans des fichiers `.md` versionnés sur
GitHub, plutôt que de compter uniquement sur l'historique de
conversation, rend ces informations **indépendantes** du risque de
compaction. Même si la conversation active perdait des détails via un
résumé, le contenu structurel important (designs de TP, décisions,
résultats de tests) reste intact et consultable dans le repo — jouant
le même rôle qu'un memory tool, en version "faite maison".

## Principe à retenir

Pour tout ce qui est **structurellement important** (designs, décisions,
résultats), externaliser dans des fichiers persistants reste plus
fiable que de compter sur la mémoire de la conversation elle-même,
compaction ou pas — la compaction est une bonne solution pour ne pas
perdre le fil général d'une longue conversation, mais elle ne remplace
pas une vraie trace écrite pour ce qui compte vraiment.

## Module "paramètres et fonctionnement pratique" — vague 2 complet ✅

Avec cette note, les 5 points de cette section sont couverts :
fenêtre de contexte, paramètres de génération, multimodalité — plus
guardrails et coûts/facturation restent à voir séparément.
