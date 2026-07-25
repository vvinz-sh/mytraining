# TP — Golden dataset automatisé : recall@k + LLM-as-judge (draft)

Statut : **design posé, pas encore exécuté**. Rattaché à la
sous-catégorie "Monitoring & évaluation" de la vague 3
(`monitoring/33-...md`, `monitoring/35-...md`).

## Objectif

Construire un script rejouable qui mesure automatiquement deux choses
sur le serveur `notes-formation` :
1. **Recall@k** — les bons documents sont-ils bien récupérés par
   Chroma ?
2. **Faithfulness** (via LLM-as-judge) — une réponse générée à partir
   de ces documents reste-t-elle fidèle à leur contenu ?

Base pour un futur monitoring continu (via le TP CI/CD, à designer
ensuite).

## Étape 1 — Le golden dataset

Fichier `golden_dataset.json`, dans `exercices/tp-monitoring/` :

```json
[
  {
    "question": "qu'est-ce que QLoRA",
    "documents_attendus": ["hardware/14-panorama-llm-qlora.md"]
  },
  {
    "question": "comment fonctionne l'attention",
    "documents_attendus": ["attention-architecture/20-mecanisme-attention-qkv-multihead.md"]
  },
  {
    "question": "pourquoi utiliser le RAG plutôt que tout mettre dans le contexte",
    "documents_attendus": [
      "rag-embeddings/02-exercices-agent-mcp-rag-embeddings.md",
      "rag-embeddings/07-recap-agent-rag-hallucination.md"
    ]
  },
  {
    "question": "quels sont les guardrails vus dans ce repo",
    "documents_attendus": [
      "securite/25-guardrails-prompt-injection-moindre-privilege.md",
      "securite/37-panorama-types-guardrails.md"
    ]
  }
]
```

4 questions pour démarrer léger — à enrichir une fois le mécanisme
validé, en couvrant davantage de thématiques du repo.

## Étape 2 — Script de calcul du recall@k

```python
import json
import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="/home/vinz/chroma_notes_db")
collection = client.get_collection("notes_formation")

with open("golden_dataset.json") as f:
    golden_dataset = json.load(f)

def calculer_recall_at_k(question, documents_attendus, k=3):
    embedding = model.encode([question])
    resultats = collection.query(query_embeddings=embedding.tolist(), n_results=k)
    sources_trouvees = {meta["source"] for meta in resultats["metadatas"][0]}
    # Vérifier par sous-chaîne, les sources indexées incluent le chemin complet
    trouves = sum(
        1 for attendu in documents_attendus
        if any(attendu in source for source in sources_trouvees)
    )
    return trouves / len(documents_attendus)

scores = []
for cas in golden_dataset:
    score = calculer_recall_at_k(cas["question"], cas["documents_attendus"])
    scores.append(score)
    print(f"'{cas['question']}' -> recall@3 = {score:.2f}")

print(f"\nRecall@3 moyen : {sum(scores)/len(scores):.2f}")
```

Point à vérifier en codant : la correspondance par sous-chaîne
(`attendu in source`) est fragile si les chemins changent légèrement
(par exemple après une réorganisation de dossier, comme celle déjà
faite sur ce repo) — pourrait nécessiter un ajustement selon comment
`meta["source"]` est réellement formaté par `index_notes.py`.

## Étape 3 — LLM-as-judge pour la faithfulness

```python
import requests  # ou le SDK Anthropic officiel

def evaluer_faithfulness(question, reponse_generee, documents_sources, api_key):
    prompt_evaluation = f"""Tu es un évaluateur expert chargé de vérifier
si une réponse est fidèle aux documents sources fournis.

Documents sources :
{documents_sources}

Question posée : {question}

Réponse à évaluer : {reponse_generee}

Analyse chaque affirmation de la réponse et vérifie si elle peut être
justifiée par les documents sources.

Évalue selon cette échelle :
- 1.0 : Toutes les affirmations sont fidèles aux sources
- 0.5 : Certaines affirmations sont fidèles, d'autres non vérifiables
- 0.0 : La réponse contient des informations contredisant les sources
  ou inventées

Réponds uniquement au format JSON : {{"score": valeur, "justification": "texte court"}}
"""
    # Appel API avec Structured Outputs (pas de prefill obsolète,
    # cf. tp-ansible-agent/tp-ansible-agent-resultat.md)
    # ... construction de la requête avec output_config.format
    pass
```

Point à developper en codant : reprendre exactement le mécanisme
Structured Outputs déjà validé dans le TP agent Ansible
(`exercices/tp-ansible-agent/`), pas le prefill obsolète, pour garantir
un JSON parsable.

## Étape 4 — Protocole de test complet

1. Lancer le script sur les 4 questions du golden dataset
2. Noter le recall@3 moyen obtenu comme référence de départ
3. Générer une réponse via Claude pour chaque question (en réutilisant
   `search_notes` + un appel de génération), puis évaluer sa
   faithfulness avec le LLM-judge
4. **Test de calibration du judge** : injecter volontairement une
   réponse fausse (par exemple, inverser un fait) et vérifier que le
   judge détecte bien un score bas — même méthodologie de test
   adversarial que le TP sécurité (tester le "mauvais cas" délibérément,
   pas seulement le cas normal)

## Ce qu'il faudra vérifier/clarifier en codant

- Format exact de `meta["source"]` stocké par `index_notes.py`, pour
  fiabiliser la comparaison du recall@k
- Choix du modèle pour le LLM-judge (le même Sonnet que la génération,
  ou un modèle différent pour éviter la circularité identifiée dans
  `cicd-mlops/39-...md`)
- Coût réel de l'appel LLM-judge à répéter sur chaque question — à
  chiffrer une fois testé (écho de `generation-parametres/26-...md`,
  input/output pricing)

## Compétences pratiquées

- Construction d'un golden dataset réutilisable
- Calcul automatisé du recall@k
- Implémentation d'un LLM-as-judge avec Structured Outputs
- Test adversarial de calibration (injection volontaire d'une réponse
  fausse pour valider que le judge la détecte)

## Lien avec les notes existantes

Prolonge `monitoring/33-monitoring-evaluation-drift-recall.md` (recall@k,
golden dataset) et `monitoring/35-faithfulness-groundedness-llm-as-judge.md`
(faithfulness, LLM-as-judge, paradoxe du juge faillible) — première
mise en pratique de ces deux notes théoriques. Réutilise directement
l'infrastructure du TP RAG/MCP (`exercices/tp-rag-mcp/`).
