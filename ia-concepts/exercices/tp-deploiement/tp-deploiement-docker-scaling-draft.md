# TP — Conteneuriser le serveur MCP + scaling horizontal léger (draft)

Statut : **design posé, pas encore exécuté**. Rattaché à la
sous-catégorie "Déploiement & serving" de la vague 3
(`deploiement-serving/34-...md`).

## ⚠️ Point de conception important à poser avant de commencer

Le serveur `serveur_mcp_notes.py` communique via **stdio** (entrée/sortie
standard), pas via HTTP — c'est le mécanisme normal d'un serveur MCP
local, lancé et possédé par un seul client (Claude Desktop) à la fois.
Le scénario qu'on a discuté en théorie ("10 requêtes simultanées, load
balancer entre plusieurs copies") suppose un **service HTTP**, pas un
process stdio 1-pour-1.

Ce TP est donc découpé en **deux parties bien distinctes**, pour ne pas
mélanger les deux :
- **Partie 1** : conteneuriser le serveur MCP tel quel (packaging pur,
  aucune notion de scaling — un conteneur reste 1-pour-1 avec un client)
- **Partie 2** : construire un **wrapper HTTP minimal** autour de la
  fonction `search_notes` (pas le serveur MCP lui-même), pour pouvoir
  réellement tester scaling horizontal + load balancer sur un vrai
  service HTTP — plus représentatif de "une API de modèle en prod" que
  le protocole MCP stdio.

## Partie 1 — Conteneuriser le serveur MCP

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Dépendances en premier (couche rarement modifiée, mise en cache)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir sentence-transformers chromadb mcp

# Code applicatif en dernier (couche souvent modifiée, cache préservé pour le reste)
COPY serveur_mcp_notes.py .

CMD ["python", "serveur_mcp_notes.py"]
```

Point volontairement appliqué du principe vu en théorie
(`deploiement-serving/34-...md`) : `torch` en CPU-only explicite dès la
première ligne, pour ne pas reproduire le bug de gonflement disque
rencontré dans le TP RAG/MCP original.

### La question de la base Chroma — volume, pas COPY

Contrairement à un `COPY` figé au build, la base `chroma_notes_db/`
doit rester **modifiable** (réindexation possible sans reconstruire
l'image) — donc montée en **volume** au lancement, pas copiée dans
l'image :

```bash
docker run -v /home/vinz/chroma_notes_db:/app/chroma_notes_db mon-serveur-mcp
```

Point de vigilance à vérifier en pratique : le chemin dans le code
(`PersistentClient(path="/home/vinz/chroma_notes_db")`) doit être
adapté au chemin **à l'intérieur** du conteneur (`/app/chroma_notes_db`
dans cet exemple), pas au chemin hôte.

### Test de la Partie 1

Vérifier que le conteneur démarre sans erreur et que la config Claude
Desktop peut lancer `docker run ...` à la place de `wsl.exe python3
...` — remplace juste la commande dans `claude_desktop_config.json`,
le protocole stdio traverse Docker de la même façon.

## Partie 2 — Wrapper HTTP pour tester scaling + batching

### Petit serveur HTTP autour de search_notes

```python
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
import chromadb

app = FastAPI()
model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="/app/chroma_notes_db")
collection = client.get_collection("notes_formation")

@app.get("/search")
def search(question: str):
    embedding = model.encode([question])
    resultats = collection.query(query_embeddings=embedding.tolist(), n_results=3)
    return {"documents": resultats["documents"][0]}
```

### Docker Compose — plusieurs copies + load balancer

```yaml
services:
  api:
    build: .
    volumes:
      - /home/vinz/chroma_notes_db:/app/chroma_notes_db
    deploy:
      replicas: 3

  nginx:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api
```

`nginx.conf` minimal en round-robin vers les 3 copies du service `api`
— répartit les requêtes automatiquement.

### Protocole de test — mesurer la latence réelle

1. Lancer un test de charge simple (`ab` ou `hey`, outils de
   benchmark HTTP) avec 10 requêtes simultanées sur un **seul**
   conteneur (`replicas: 1`), mesurer le temps de la dernière réponse.
2. Repasser à `replicas: 3`, relancer le même test, comparer.
3. Vérifier si le résultat se rapproche du calcul théorique qu'on avait
   fait (2s → ~0,7s en passant de 1 à 3 copies) — ou si la réalité
   diverge, et pourquoi (overhead réseau du load balancer, temps de
   connexion, etc., non comptés dans le calcul théorique simplifié).

## Ce qu'il faudra vérifier/clarifier en codant

- Le chemin exact du volume Chroma partagé entre les 3 replicas —
  accès **concurrent en lecture** à la même base SQLite depuis 3
  process différents, à vérifier que ça ne pose pas de souci
  (contrairement à l'écriture concurrente identifiée comme risquée dans
  le TP sécurité)
- Outil de benchmark HTTP à installer (`ab` via apache2-utils, ou `hey`)
- Si le résultat mesuré diverge significativement du calcul théorique,
  documenter précisément où (c'est prévu et attendu, pas un échec du TP)

## Compétences pratiquées

- Écriture d'un Dockerfile réel avec ordre de couches optimisé
- Volumes Docker pour données persistantes/modifiables
- Docker Compose pour orchestrer plusieurs replicas
- Configuration basique nginx en round-robin
- Benchmark de charge HTTP et comparaison théorie vs mesure réelle

## Lien avec les notes existantes

Prolonge `deploiement-serving/34-deploiement-serving-concurrence-batching.md`
(concurrence, scaling horizontal, coût mémoire, couches Docker) — ce TP
en est la mise en pratique directe, avec la nuance stdio vs HTTP
clarifiée dès le départ plutôt que découverte en cours de route.
