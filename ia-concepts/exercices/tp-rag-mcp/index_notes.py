import glob

def chunk_text(text, taille=300, chevauchement=50):
    mots = text.split()
    chunks = []
    for i in range(0, len(mots), taille - chevauchement):
        chunk = " ".join(mots[i:i + taille])
        if chunk:
            chunks.append(chunk)
    return chunks

fichiers = glob.glob("/mnt/c/Users/Vinz/Documents/mytraining/ia-concepts/**/*.md", recursive=True)
tous_chunks = []
for f in fichiers:
    with open(f, encoding="utf-8") as fh:
        contenu = fh.read()
    for chunk in chunk_text(contenu):
        tous_chunks.append({"texte": chunk, "source": f})

print(f"{len(fichiers)} fichiers traités, {len(tous_chunks)} chunks générés")
for c in tous_chunks[:3]:
    print(f"--- {c['source']} ---")
    print(c['texte'][:150], "...\n")


from sentence_transformers import SentenceTransformer

print("Chargement du modèle d'embeddings...")
model = SentenceTransformer('all-MiniLM-L6-v2')

textes = [c["texte"] for c in tous_chunks]
print(f"Génération des embeddings pour {len(textes)} chunks...")
embeddings = model.encode(textes, show_progress_bar=True)

print(f"Forme des embeddings : {embeddings.shape}")

import chromadb

client = chromadb.PersistentClient(path="/home/vinz/chroma_notes_db/")

# Supprime la collection si elle existe déjà (pratique pour relancer le script sans erreur)
try:
    client.delete_collection("notes_formation")
except Exception:
    pass

collection = client.create_collection("notes_formation")

collection.add(
    documents=textes,
    embeddings=embeddings.tolist(),
    metadatas=[{"source": c["source"]} for c in tous_chunks],
    ids=[str(i) for i in range(len(tous_chunks))]
)

print(f"{collection.count()} chunks indexés dans Chroma")

# Test de recherche
question = "qu'est-ce que QLoRA"
question_embedding = model.encode([question])
resultats = collection.query(
    query_embeddings=question_embedding.tolist(),
    n_results=3
)

print(f"\n--- Résultats pour : '{question}' ---")
for doc, meta, distance in zip(resultats["documents"][0], resultats["metadatas"][0], resultats["distances"][0]):
    print(f"\n[{meta['source']}] (distance={distance:.3f})")
    print(doc[:200], "...")
