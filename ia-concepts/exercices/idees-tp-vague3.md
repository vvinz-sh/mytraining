# Idées de TP — vague 3 (une par sous-catégorie)

Pistes notées telles quelles, pas encore designées en détail. À
développer un jour si l'envie prend, sur le modèle des autres TP du
repo (`ia-concepts/exercices/`).

## 1. Déploiement & serving
Conteneuriser le serveur MCP — écrire le `Dockerfile` pour
`serveur_mcp_notes.py` (poids/dépendances en premier, code en dernier),
puis tester un scaling horizontal léger (2 conteneurs + load balancer
simple) pour observer concrètement la réduction de latence.

## 2. Monitoring & évaluation
Golden dataset automatisé — un petit fichier de questions avec leurs
documents attendus, un script calculant le recall@k automatiquement, et
un appel LLM-as-judge pour vérifier la faithfulness des réponses
générées.

## 3. CI/CD & pipelines MLOps
Pipeline d'intégration continue sur le repo — workflow GitHub Actions
qui relance l'indexation + le golden dataset à chaque push, et fait
échouer le build si le recall@k descend sous un seuil.

## 4. Gouvernance & conformité
Rédiger une vraie "system card" pour le serveur `notes-formation" —
données utilisées, modèle d'embedding, guardrails en place, limites
connues, obligations RGPD identifiées.

## 5. Ingénierie de données
Versionner la base Chroma avec DVC (Data Version Control) — pouvoir
revenir à une version antérieure de l'index, le réflexe Git appliqué
aux données plutôt qu'au code.
