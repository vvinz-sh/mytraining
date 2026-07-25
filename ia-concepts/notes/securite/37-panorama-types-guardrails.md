# IA — Panorama des types de guardrails

Session de synthèse, partie d'une limite concrète du TP sécurité déjà
réalisé : la petite base d'exemples fixes du guardrail sémantique.

## La limite qui a motivé cette session

`garde_fous_injection` ne contient que 5 phrases exemples fixes,
comparées par similarité. Une attaque avec une formulation
**complètement différente** de ces 5 exemples (angle nouveau, emojis,
langage codé) passerait à travers — le guardrail ne détecte que ce qui
**ressemble** à ses exemples, jamais mis à jour automatiquement.

## Guardrail par classificateur entraîné (moderation model)

Au lieu de comparer par similarité à une petite liste fixe, utiliser un
**modèle spécifiquement entraîné** (souvent sur des dizaines de milliers
d'exemples réels d'attaques, mis à jour régulièrement) pour classifier
"ceci est-il une tentative de manipulation, oui/non". Exemple réel :
les API de modération proposées par certains fournisseurs LLM en
complément de leur modèle principal.

### Pourquoi ça généralise mieux à du jamais-vu

Écho direct du principe ML de base (le chat blanc/noir) : un modèle
entraîné sur des milliers d'exemples variés n'apprend pas à mémoriser
chaque cas individuel, il apprend le **motif sous-jacent**. Avec 5
exemples comparés par similarité, aucun apprentissage n'a lieu — juste
une comparaison directe. Un classificateur entraîné apprend des
caractéristiques **abstraites** (structure de phrase impérative envers
le modèle, contexte de rupture d'instructions...) plutôt que "est-ce que
ça ressemble mot pour mot à mes 5 phrases" — généralise donc à des
formulations jamais vues.

## Guardrail par contrainte structurelle (constrained decoding)

Les **Structured Outputs** de l'API Claude (`output_config.format`,
utilisés dans le TP agent Ansible — `deploiement-serving/...` ou
`exercices/tp-ansible-agent/`) sont en fait une forme de guardrail :
forcer la sortie à respecter un schéma JSON précis **élimine
structurellement** certaines catégories de sorties indésirables — le
modèle ne peut physiquement pas générer du texte libre malveillant s'il
est contraint à produire uniquement des champs typés définis à l'avance.

Garantie **dure**, par construction — pas probabiliste comme les
guardrails de détection de contenu.

## Rate limiting / throttling

Pas une détection de **contenu** du tout — une limite sur la
**fréquence** des requêtes.

Utilité concrète contre l'extraction attack (rappel :
`securite/32-memorisation-extraction-attack-differential-privacy.md`) :
ce type d'attaque demande souvent de multiplier les tentatives avec des
variations de prompt pour espérer déclencher une mémorisation exacte.
Le rate limiting ne bloque aucune requête individuelle sur son contenu,
mais rend l'attaque **économiquement et temporellement coûteuse** à
mener à grande échelle — même principe défensif qu'un verrouillage de
compte après plusieurs tentatives de mot de passe échouées en sécurité
classique.

## En production — s'appuyer sur des services managés plutôt que réinventer

Question posée en session : est-ce qu'un développeur en production
pourrait s'appuyer sur un service cloud exposant un LLM de sécurité
dédié pour faire du guardrail, plutôt que de construire sa propre
implémentation comme dans ce TP ?

**Oui, et c'est devenu une pratique courante en 2026** — deux niveaux
existent :

### Services de guardrail intégrés à une plateforme cloud

**AWS Bedrock Guardrails** s'applique par-dessus n'importe quel modèle
du catalogue (Claude, Llama, Titan), avec des politiques couvrant les
catégories de contenu, les sujets interdits, la détection/masquage de
PII, la vérification de fidélité contextuelle contre l'hallucination
(faithfulness, voir `monitoring/35-...md`), et des heuristiques de
détection d'attaques de prompt. Équivalents chez les autres fournisseurs
: Azure AI Content Safety, Google Model Armor.

### Passerelles de guardrail multi-fournisseurs (LLM gateways)

Architecture plus avancée : un point de contrôle central (gateway) par
lequel transite toute requête LLM, appliquant automatiquement les mêmes
politiques de sécurité sans changement de code applicatif — pouvant
combiner plusieurs fournisseurs de sécurité (filtrage de contenu +
détection d'hallucination + scan de secrets) derrière une seule
configuration. C'est exactement le principe du TP (regex secrets +
similarité sémantique combinés), mais industrialisé et mutualisé entre
toutes les applications LLM d'une organisation plutôt que réimplémenté
projet par projet.

### Ce que ça change en pratique

- Plus besoin de construire son propre classificateur d'injection
  depuis zéro (ce qu'on a fait en mode "artisanal" avec 5 exemples
  fixes) — un service géré fait ce travail, entraîné sur des volumes
  bien plus larges (rejoint le guardrail par classificateur entraîné
  vu plus haut).
- Évite le problème d'implémentation incohérente entre équipes (une
  politique de sécurité interprétée différemment selon les projets,
  avec le risque qu'une implémentation manquante devienne le point
  faible lors d'un audit).
- Contrepartie : dépendance au fournisseur, coût, et parfois des
  contraintes de résidence des données selon la région (écho direct de
  la gouvernance/RGPD vue dans `gouvernance/36-...md`).

**Conclusion pédagogique** : garder une implémentation "maison" comme
dans ce TP reste excellent pour comprendre *pourquoi* ça marche (et
apprendre à calibrer, déboguer, tester) — mais en contexte
professionnel réel, s'appuyer sur un service managé plutôt que
réinventer la roue à chaque projet est la pratique recommandée.

## Récapitulatif — tous les guardrails vus dans le repo

| Type | Détecte | Garantie |
|---|---|---|
| Pattern/regex | Format structuré et prévisible (clé API, email) | Dure, quasi 100% |
| Sémantique (similarité) | Formulations proches d'exemples connus | Probabiliste, 95-99% (limite ANN) |
| NER | Entités non structurées (noms propres) | Probabiliste, ambigu sur cas limites |
| Classificateur entraîné | Motifs abstraits, généralise à du jamais-vu | Probabiliste, meilleure généralisation |
| Contrainte structurelle (Structured Outputs) | Élimine des catégories entières de sortie | Dure, garantie par construction |
| Rate limiting | Pas le contenu — la fréquence/volume | Dur sur la métrique, pas sur le contenu |

## Principe transversal

Aucun guardrail seul n'est jamais suffisant (écho direct de la
**défense en profondeur** vue dans
`securite/25-guardrails-prompt-injection-moindre-privilege.md`) — un
système robuste combine plusieurs de ces types, chacun couvrant un
angle mort différent des autres : formats prévisibles (pattern),
sémantique connue (similarité), motifs abstraits (classificateur),
structure de sortie (contrainte), et volume/fréquence (rate limiting).
