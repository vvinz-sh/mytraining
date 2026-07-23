# IA — Limites et biais : hallucinations et sur-confiance

Dernière note du module IA de base.

## Le ton ne trahit jamais une hallucination

Scénario : demander une commande + chemin de fichier exact pour
configurer `vm.max_map_count` sur RHEL 8. Une réponse fausse est formulée
**exactement** de la même manière qu'une réponse vraie — même fluidité,
même absence d'hésitation, même niveau de détail précis.

Pourquoi techniquement : le modèle est entraîné à prédire la suite la
plus **plausible** d'un texte, pas à vérifier des faits contre une base de
vérité. Face à un type de requête vu des milliers de fois à
l'entraînement (config sysctl RHEL), il génère quelque chose qui
**ressemble** à une vraie réponse de ce type — même s'il invente un chemin
inexistant ou mélange deux versions de RHEL sans le signaler.

## La parade : vérification indépendante, jamais confiance sur le ton

Face à une réponse technique, réflexe à conserver : vérifier via une
source indépendante de moi (doc/man, test en environnement isolé/dev)
avant d'appliquer en prod. Ça marche parce que ces sources peuvent révéler
une erreur que **rien dans le ton de ma réponse** n'aurait pu indiquer.

Point important : ce réflexe est d'autant plus critique sur des sujets où
l'expertise personnelle est **faible** — sur un domaine maîtrisé (ex :
RHEL), on a le bagage pour repérer une incohérence avant même de tester.
Le vrai danger de l'hallucination est maximal précisément là où on n'a pas
ce garde-fou d'expertise pour repérer l'erreur soi-même.

## Hallucination vs sur-confiance — deux axes indépendants

- **Hallucination** = le contenu de la réponse est factuellement **faux**
  (commande inexistante, fichier inventé, date erronée).
- **Sur-confiance** = le **ton** exprime une certitude non justifiée,
  indépendamment de si le contenu est vrai ou faux.

Les 4 combinaisons possibles :
| Contenu | Ton | Résultat |
|---|---|---|
| Vrai | Nuancé ("vérifie selon ta version") | Idéal |
| Vrai | Sur-confiant | Correct par hasard, ton pas fiable pour autant |
| Faux | Sur-confiant | **Cas le plus dangereux** |
| Faux | Nuancé | Rare chez un LLM, mais moins dommageable (le doute pousse à vérifier) |

Point pratique clé : la **sur-confiance est quasi systématique** chez un
LLM, qu'il ait raison ou tort — pas de mécanisme interne fiable pour
"sentir" et exprimer proportionnellement son incertitude dans le ton.
D'où l'importance du réflexe de vérification indépendante : il compense
ce que le ton ne peut jamais garantir.

## Récap — module IA de base terminé

Avec cette note, les points prévus initialement pour le module IA de base
sont tous couverts :
- Terminologie (LLM, tokens, tool use, agents, MCP, RAG, embeddings,
  fine-tuning)
- ML vs programmation classique
- Réseaux de neurones — intuition
- Prompting — précision, few-shot
- Usage pratique — appel API depuis un script/Ansible
- RAG vs fine-tuning — critères de décision
- Limites et biais — hallucinations, sur-confiance

Reste ouvert : le TP prévu (`ia-concepts/exercices/tp-ansible-llm/tp-ansible-llm.md`),
à faire quand une clé API sera disponible.
