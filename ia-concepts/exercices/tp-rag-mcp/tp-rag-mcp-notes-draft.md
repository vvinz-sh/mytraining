# TP — RAG sur son propre repo + serveur MCP maison (draft)

Statut : **design posé, pas encore exécuté**. Combine RAG de bout en
bout et création (pas simple consommation) d'un serveur MCP — TP léger,
sans GPU nécessaire.

## Objectif

Construire un assistant capable de chercher dans les notes du repo
`mytraining` par similarité sémantique, puis l'exposer comme outil
utilisable par Claude via un serveur MCP maison.

## Architecture en 4 étapes

```
Fichiers .md du repo
   → chunking (découper en passages)
   → embeddings (vectoriser chaque chunk)
   → stockage dans Chroma (base vectorielle locale)
   → [Étape RAG terminée : recherche par similarité fonctionnelle]
   → envelopper dans un serveur MCP (outil "search_notes")
   → connecter à Claude Desktop/Code
   → [Étape MCP terminée : Claude peut interroger le repo via tool use]
```

## Étape 1 — Chunking des notes

Contrairement au TP embeddings (mots isolés), ici on découpe des
**documents entiers** en passages de taille raisonnable (ex : 300-500
mots, avec un léger chevauchement entre chunks pour ne pas couper une
idée en plein milieu).

```python
import os
import glob

def chunk_text(text, taille=500, chevauchement=50):
    mots = text.split()
    chunks = []
    for i in range(0, len(mots), taille - chevauchement):
        chunks.append(" ".join(mots[i:i + taille]))
    return chunks

fichiers = glob.glob("mytraining/**/*.md", recursive=True)
tous_chunks = []
for f in fichiers:
    with open(f, encoding="utf-8") as fh:
        contenu = fh.read()
    for chunk in chunk_text(contenu):
        tous_chunks.append({"texte": chunk, "source": f})
```

Point à vérifier en codant : la taille de chunk optimale dépend du
contenu — des notes très denses (comme celles sur l'attention) pourront
nécessiter des chunks différents de notes plus procédurales (comme les
résultats de TP).

## Étape 2 — Embeddings

Deux options, à choisir selon la disponibilité :
- **Voyage AI** (partenaire recommandé par Anthropic pour les
  embeddings) — nécessite une clé API séparée, comme pour Claude.
- **Alternative locale, gratuite** : `sentence-transformers`
  (bibliothèque Python, modèles légers tournant bien sur CPU) — pas de
  clé API à gérer, cohérent avec l'esprit léger du TP.

```bash
pip install sentence-transformers chromadb --break-system-packages
```

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')  # léger, rapide sur CPU

embeddings = model.encode([c["texte"] for c in tous_chunks])
```

## Étape 3 — Stockage et recherche avec Chroma

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_notes_db")
collection = client.create_collection("notes_formation")

collection.add(
    documents=[c["texte"] for c in tous_chunks],
    embeddings=embeddings.tolist(),
    metadatas=[{"source": c["source"]} for c in tous_chunks],
    ids=[str(i) for i in range(len(tous_chunks))]
)

# Test de recherche
resultats = collection.query(
    query_texts=["qu'est-ce que QLoRA"],
    n_results=3
)
```

Point pédagogique : ici, Chroma gère lui-même la vectorisation de la
requête si on utilise `query_texts` avec le bon embedding function
configuré — sinon, il faut vectoriser la question manuellement avec le
même modèle `sentence-transformers` avant de faire `query_embeddings`.
À vérifier/choisir en codant.

## Étape 4 — Serveur MCP maison

Utiliser le SDK Python officiel MCP (`mcp` sur PyPI) pour exposer la
recherche Chroma comme un outil standardisé :

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("notes-formation")

@mcp.tool()
def search_notes(question: str) -> str:
    """Cherche dans les notes de formation Vincent (RHEL, Ansible, IA, Git...)"""
    resultats = collection.query(query_texts=[question], n_results=3)
    return "\n---\n".join(resultats["documents"][0])

if __name__ == "__main__":
    mcp.run()
```

## Étape 5 — Connexion à Claude Desktop/Code

Ajouter le serveur dans la config MCP de Claude Desktop (fichier de
config JSON, chemin à vérifier selon l'OS) :

```json
{
  "mcpServers": {
    "notes-formation": {
      "command": "python",
      "args": ["/chemin/vers/serveur_mcp.py"]
    }
  }
}
```

Une fois connecté, tester en conversation normale : poser une question
du type "qu'est-ce qu'on avait vu sur QLoRA ?" et observer Claude
appeler l'outil `search_notes` (tool use en direct, visible dans
l'interface).

## Ce qu'il faudra vérifier/clarifier en codant

- Choix définitif entre Voyage AI (qualité probablement supérieure) et
  sentence-transformers (gratuit, local, suffisant pour un usage perso)
- Taille de chunk optimale selon le type de notes
- Chemin exact du fichier de config MCP selon l'OS (Windows/WSL dans le
  cas de Vincent — potentiellement une subtilité liée à l'interaction
  entre Claude Desktop côté Windows et un serveur Python lancé depuis
  WSL, à vérifier en pratique)
- Gestion des mises à jour : que se passe-t-il quand de nouvelles notes
  sont ajoutées au repo — faut-il réindexer tout, ou seulement les
  nouveaux fichiers (écho direct de la discussion sur la réindexation
  vue dans une série de questions précédente) ?

## Compétences pratiquées

- Chunking de documents (nouveau, pas vu avant — different du chunking
  de mots isolés du TP embeddings)
- Embeddings via bibliothèque dédiée (sentence-transformers) ou API
  (Voyage AI)
- Base de données vectorielle en pratique (Chroma) — jusqu'ici vue
  uniquement en panorama théorique
- Construction d'un serveur MCP de A à Z (pas juste consommation d'un
  serveur existant)
- Connexion et test d'un serveur MCP custom avec Claude Desktop/Code
- RAG de bout en bout sur un cas d'usage réel et personnel

## Lien avec les notes existantes

Prolonge `02-exercices-agent-mcp-rag-embeddings.md` (MCP théorique),
`07-recap-agent-rag-hallucination.md` (pipeline RAG), le schéma
`pipeline_rag_embedding_generation`, et
`27-panorama-outils-ecosysteme-hermes-mcp.md` (bases vectorielles,
panorama MCP) — première fois que RAG et MCP sont pratiqués ensemble
dans un seul TP, plutôt que séparément.
