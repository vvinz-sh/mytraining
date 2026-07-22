from mcp.server.fastmcp import FastMCP
from sentence_transformers import SentenceTransformer
import chromadb

# Chargement au démarrage du serveur (une seule fois, pas à chaque requête)
model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="/home/vinz/chroma_notes_db/")
collection = client.get_collection("notes_formation")

mcp = FastMCP("notes-formation")

@mcp.tool()
def search_notes(question: str) -> str:
    """Cherche dans les notes de formation de Vincent (RHEL, Ansible, Git, IA...)
    et retourne les passages les plus pertinents avec leur fichier source."""
    question_embedding = model.encode([question])
    resultats = collection.query(
        query_embeddings=question_embedding.tolist(),
        n_results=3
    )

    reponse = []
    for doc, meta, distance in zip(
        resultats["documents"][0],
        resultats["metadatas"][0],
        resultats["distances"][0]
    ):
        reponse.append(f"[Source: {meta['source']}]\n{doc}")

    return "\n\n---\n\n".join(reponse)

if __name__ == "__main__":
    mcp.run()
