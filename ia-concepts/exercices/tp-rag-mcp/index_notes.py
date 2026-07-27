# index_notes.py
import glob
import hashlib
import json
import os

CHEMIN_NOTES = "/home/vinz/mytraining/ia-concepts/**/*.md"  # corrigé, natif Linux
CHEMIN_CHROMA = "/home/vinz/chroma_notes_db/"
FICHIER_ETAT = "/home/vinz/mytraining/ia-concepts/exercices/tp-rag-mcp/index_state.json"

def chunk_text(text, taille=300, chevauchement=50):
    mots = text.split()
    chunks = []
    for i in range(0, len(mots), taille - chevauchement):
        chunk = " ".join(mots[i:i + taille])
        if chunk:
            chunks.append(chunk)
    return chunks

def hash_contenu(texte):
    return hashlib.sha256(texte.encode("utf-8")).hexdigest()

# 1. État précédent
if os.path.exists(FICHIER_ETAT):
    with open(FICHIER_ETAT) as f:
        etat_precedent = json.load(f)
else:
    etat_precedent = {}

# 2. État actuel
fichiers_actuels = glob.glob(CHEMIN_NOTES, recursive=True)
etat_actuel = {}
contenus = {}
for f in fichiers_actuels:
    with open(f, encoding="utf-8") as fh:
        contenu = fh.read()
    contenus[f] = contenu
    etat_actuel[f] = hash_contenu(contenu)

# 3. Diff
fichiers_nouveaux_ou_modifies = [
    f for f, h in etat_actuel.items()
    if f not in etat_precedent or etat_precedent[f] != h
]
fichiers_supprimes = [f for f in etat_precedent if f not in etat_actuel]

print(f"{len(fichiers_nouveaux_ou_modifies)} fichier(s) nouveau(x)/modifié(s), {len(fichiers_supprimes)} supprimé(s), {len(etat_actuel) - len(fichiers_nouveaux_ou_modifies)} inchangé(s)")

if not fichiers_nouveaux_ou_modifies and not fichiers_supprimes:
    print("Rien à faire, index déjà à jour.")
else:
    import chromadb
    client = chromadb.PersistentClient(path=CHEMIN_CHROMA)
    collection = client.get_or_create_collection("notes_formation")

    # 4. Supprimer les chunks des fichiers modifiés (avant réajout) et supprimés
    for f in fichiers_nouveaux_ou_modifies + fichiers_supprimes:
        collection.delete(where={"source": f})

    # 5. Ré-indexer uniquement les fichiers nouveaux/modifiés
    if fichiers_nouveaux_ou_modifies:
        from sentence_transformers import SentenceTransformer
        print("Chargement du modèle d'embeddings...")
        model = SentenceTransformer('all-MiniLM-L6-v2')

        tous_chunks = []
        for f in fichiers_nouveaux_ou_modifies:
            for chunk in chunk_text(contenus[f]):
                tous_chunks.append({"texte": chunk, "source": f})

        textes = [c["texte"] for c in tous_chunks]
        print(f"Génération des embeddings pour {len(textes)} chunks...")
        embeddings = model.encode(textes, show_progress_bar=True)

        collection.add(
            documents=textes,
            embeddings=embeddings.tolist(),
            metadatas=[{"source": c["source"]} for c in tous_chunks],
            ids=[f"{c['source']}::{i}" for i, c in enumerate(tous_chunks)]
        )
        print(f"{len(textes)} chunks (ré)indexés")

    # 6. Sauvegarder le nouvel état
    with open(FICHIER_ETAT, "w") as f:
        json.dump(etat_actuel, f, indent=2)

    print(f"Total dans la collection : {collection.count()} chunks")
