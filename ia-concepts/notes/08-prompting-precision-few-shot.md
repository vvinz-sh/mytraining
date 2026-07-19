# IA — Prompting : précision, ambiguïté, few-shot

## Prompt vague vs prompt précis — ce qui se joue vraiment

Comparaison : "écris-moi un script pour nettoyer les vieux logs" vs un
prompt précisant langage, extension ciblée, seuil d'âge, dossier, mode
`--dry-run`, et journalisation.

Point de vocabulaire important : ce n'est **pas** de l'hallucination (au
sens vu précédemment : le modèle invente des faits qui n'existent pas).
C'est un problème d'**ambiguïté comblée par des suppositions**. Face à un
prompt vague, le modèle ne devine pas au hasard — il fait des choix par
défaut raisonnables mais arbitraires (extension, seuil, dossier...), et
produit quelque chose de cohérent mais qui peut ne pas correspondre à
l'intention réelle.

Un prompt précis ne rend pas le modèle "moins halluciné" — il réduit le
nombre de décisions arbitraires qu'il doit prendre à sa place. Un modèle
peut très bien halluciner même sur un prompt très précis (ex : inventer
un nom de fonction qui n'existe pas dans une bibliothèque réelle).

## Deux catégories d'information dans un bon prompt

**Élimine une décision arbitraire** (répond à "quoi faire exactement") —
le modèle est de toute façon *forcé* de choisir quelque chose si l'info
manque :
- langage/système cible
- extension de fichier ciblée
- seuil (ex : âge des fichiers)
- dossier/chemin précis

**Contraint le format/structure de la sortie** (répond à "comment je veux
le résultat") — ce ne sont **jamais** des ambiguïtés à combler
nécessairement, ce sont des exigences que seul l'utilisateur connaît, et
qui ne viennent quasiment jamais spontanément si elles ne sont pas
explicitement demandées :
- fonctionnalités optionnelles (ex : mode `--dry-run`)
- comportements de traçabilité (ex : journalisation dans un fichier log)

Règle pratique : plus une exigence est "optionnelle mais utile", moins le
modèle a de chances de la deviner tout seul — rien ne l'oblige à la
déduire, contrairement à un choix qu'il est de toute façon forcé de faire
(langage, seuil, chemin...).

## Few-shot — montrer plutôt que décrire

Scénario : convention de nommage arbitraire pour des sauvegardes
(`backup_<service>_<date>_<env>.tar.gz`, avec environnement abrégé en 3
lettres majuscules selon une correspondance non standard : production →
PRD, staging → STG, development → DEV).

- **Instruction pure** : décrire la règle en mots. Fonctionne, mais laisse
  de la place à l'erreur d'interprétation ou d'application — le modèle
  doit d'abord *comprendre* correctement la description, puis
  l'*appliquer*, deux étapes où une erreur peut se glisser.
- **Few-shot** : donner 2-3 exemples sans expliquer la règle. Élimine
  l'étape "comprendre la règle" — le modèle repère et reproduit un motif
  observé directement, sans avoir à interpréter une explication en
  langage naturel.

Écho direct avec la distinction ML vs programmation classique vue plus
tôt : au lieu de décrire la règle (approche classique), on montre des
exemples et on laisse le système inférer le motif (approche ML) — la même
logique appliquée à la formulation d'un prompt.

## Limite du few-shot pur — généralisation fragile sur peu d'exemples

Avec seulement 2 exemples (production→PRD, staging→STG), demander une
conversion pour un environnement jamais vu (`qualification`, `sandbox`)
est risqué : le modèle infère un motif à partir de trop peu de cas
(souvent "prendre les 3 premières lettres" ou une variante), et ça peut
tomber juste... ou pas du tout (`qual`, `qul`, `quf` ?).

Écho direct avec la généralisation à partir de peu d'exemples vue en ML
(le chat blanc/noir) : trop peu d'exemples variés → motif déduit
potentiellement faux ou incomplet.

## Bonne pratique — combiner les deux approches

Le few-shot seul est fragile sur les cas non couverts par les exemples ;
l'instruction pure seule est fragile sur les règles arbitraires (risque
d'erreur d'interprétation/application). Le meilleur prompt combine les
deux : quelques exemples **et** une règle explicite pour les cas non
couverts.

Exemple : "abrège en 3 lettres majuscules selon : production→PRD,
staging→STG, development→DEV ; pour tout autre environnement, prends les
3 premières lettres en majuscules."

## À venir

- [ ] Usage pratique — appeler une API LLM depuis un script (Python/bash)
