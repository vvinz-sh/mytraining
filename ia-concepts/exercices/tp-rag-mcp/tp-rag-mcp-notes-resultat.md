# TP — RAG sur son propre repo + serveur MCP maison : réalisé avec succès ✅

Complète `tp-rag-mcp-notes-draft.md`. Le TP a été mené à bien de bout en
bout : indexation RAG des notes du repo, serveur MCP maison, connexion
réelle à Claude Desktop, test concluant en conversation.

## Pipeline final réalisé

```
39 fichiers .md (ia-concepts/) → 128 chunks (300 mots, chevauchement 50)
   → embeddings (sentence-transformers, all-MiniLM-L6-v2, 384 dimensions)
   → stockage Chroma (PersistentClient)
   → serveur MCP maison (FastMCP, outil search_notes)
   → connecté à Claude Desktop (config JSON, wsl.exe)
   → testé en conversation réelle : succès
```

## Choix techniques

- **Embeddings** : `sentence-transformers` (local, CPU, gratuit) plutôt
  que Voyage AI — pas de clé API supplémentaire à gérer.
- **Chunking** : 300 mots par chunk, chevauchement de 50 mots, pour ne
  pas couper une idée en plein milieu.
- **Base vectorielle** : Chroma, en mode `PersistentClient` (local, pas
  de serveur à monter).

## Bugs rencontrés et corrigés (tous des problèmes d'infra, pas de code Python)

### 1. `sentence-transformers` a installé torch avec support CUDA complet

Symptôme : `pip install sentence-transformers` a embarqué tous les
paquets `nvidia-cu*` (plusieurs Go), saturant l'espace disque (4 Go
restants).

**Correction** : désinstallation ciblée (`pip freeze | grep -E
"^(torch|triton|nvidia-)"` pour lister précisément, puis
désinstallation groupée) et réinstallation de `torch` en version
**CPU-only** (`--index-url https://download.pytorch.org/whl/cpu`) —
suffisant pour un modèle léger comme `all-MiniLM-L6-v2`, sans besoin de
CUDA. Espace récupéré : 4 → 8 Go.

Piège annexe rencontré : tenter de désinstaller en donnant les noms de
paquets avec leur numéro de version accolé (ex :
`nvidia-cublas-13.1.1.3`) ne fonctionne pas — le vrai nom de paquet est
`nvidia-cublas-cu13` (sans version dans le nom). Génération de la liste
via `pip freeze` plutôt que retaper à la main, plus fiable.

### 2. Distro WSL par défaut incorrecte pour `wsl.exe`

Symptôme : Claude Desktop signale le serveur MCP "failed", log montrant
`/bin/bash: /home/vinz/.py3/bin/python3: No such file or directory` —
alors que ce chemin existe bel et bien (vérifié avec `ls -l`).

**Cause** : deux distros WSL installées (`Ubuntu` en v1, distro par
défaut ; `Ubuntu-24.04` en v2, celle utilisée pour tout le reste du
repo — convertie plus tôt pour le GPU passthrough). `wsl.exe` sans
précision lance la distro **par défaut**, pas celle où le venv existe.

**Correction** : forcer explicitement la distro dans la config JSON,
avec `"-d", "Ubuntu-24.04"` en premier argument, avant le chemin de
l'interpréteur.

### 3. Chroma incompatible avec un chemin sur système de fichiers Windows monté (DrvFs)

Symptôme : `chromadb.errors.InternalError: Permission denied (os error
13)` sur les bindings Rust de Chroma, alors que le script fonctionnait
très bien lancé manuellement depuis le même dossier.

**Cause** : le verrouillage de fichiers (file locking) utilisé en
interne par les bindings Rust de Chroma ne fonctionne pas correctement
sur un montage `/mnt/c/...` (DrvFs) — un problème connu, indépendant du
code Python lui-même.

**Correction** : déplacer la base Chroma sur le système de fichiers
Linux natif (`/home/vinz/chroma_notes_db`), avec un chemin **absolu**
plutôt que relatif (`./chroma_notes_db`) — important aussi parce que le
dossier de travail au lancement diffère entre une exécution manuelle et
un lancement par Claude Desktop.

## Configuration finale (Claude Desktop, Windows + WSL2)

Fichier trouvé au chemin réel (app packagée MSIX, différent du chemin
`%APPDATA%` classique documenté) :
```
C:\Users\Vinz\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json
```

```json
{
  "mcpServers": {
    "notes-formation": {
      "command": "wsl.exe",
      "args": [
        "-d", "Ubuntu-24.04",
        "/home/vinz/.py3/bin/python3",
        "/mnt/c/Users/Vinz/Documents/mytraining/ia-concepts/exercices/tp-rag-mcp/serveur_mcp_notes.py"
      ]
    }
  }
}
```

## Test final réussi

Question posée en conversation Claude Desktop : *"Utilise l'outil
notes-formation pour chercher ce qu'on a vu sur le RAG"*.

Résultat : Claude a bien invoqué l'outil `search_notes` (visible dans
l'interface : "Outils chargés, a utilisé l'intégration
notes-formation"), et la réponse générée reprenait fidèlement le
contenu réel des notes (critère du retrieval, pipeline RAG, analogie
hash/GPS), en citant correctement le fichier source
(`02-exercices-agent-mcp-rag-embeddings.md`).

## Code final complet

### `index_notes.py` — chunking, embeddings, indexation Chroma

```python
import glob
from sentence_transformers import SentenceTransformer
import chromadb

# --- Étape 1 : chunking des fichiers .md ---
def chunk_text(text, taille=300, chevauchement=50):
    mots = text.split()
    chunks = []
    for i in range(0, len(mots), taille - chevauchement):
        chunk = " ".join(mots[i:i + taille])
        if chunk:
            chunks.append(chunk)
    return chunks

fichiers = glob.glob("mytraining/ia-concepts/**/*.md", recursive=True)
tous_chunks = []
for f in fichiers:
    with open(f, encoding="utf-8") as fh:
        contenu = fh.read()
    for chunk in chunk_text(contenu):
        tous_chunks.append({"texte": chunk, "source": f})

print(f"{len(fichiers)} fichiers traités, {len(tous_chunks)} chunks générés")

# --- Étape 2 : génération des embeddings ---
model = SentenceTransformer('all-MiniLM-L6-v2')
textes = [c["texte"] for c in tous_chunks]
embeddings = model.encode(textes, show_progress_bar=True)
print(f"Forme des embeddings : {embeddings.shape}")  # (128, 384)

# --- Étape 3 : indexation dans Chroma ---
# Chemin absolu sur système de fichiers Linux natif (pas /mnt/c/...),
# indispensable sous WSL : Chroma plante en "Permission denied" sur un
# montage Windows (DrvFs) à cause du verrouillage de fichiers Rust.
client = chromadb.PersistentClient(path="/home/vinz/chroma_notes_db")

try:
    client.delete_collection("notes_formation")  # repartir propre si relancé
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

# --- Test rapide de recherche ---
question = "qu'est-ce que QLoRA"
question_embedding = model.encode([question])
resultats = collection.query(query_embeddings=question_embedding.tolist(), n_results=3)
for doc, meta, distance in zip(resultats["documents"][0], resultats["metadatas"][0], resultats["distances"][0]):
    print(f"[{meta['source']}] (distance={distance:.3f})")
    print(doc[:200], "...\n")
```

**Points clés à retenir de ce script** :
- Le chevauchement (`chevauchement=50`) évite qu'une idée soit coupée
  net entre deux chunks — le début du chunk suivant répète la fin du
  précédent.
- `embeddings.tolist()` est nécessaire car Chroma attend des listes
  Python natives, pas des tableaux NumPy.
- La `distance` retournée par Chroma est à l'inverse de la similarité
  cosinus vue avec gensim : **plus proche de 0 = plus similaire** (pas
  l'inverse).
- `try/except` autour de `delete_collection` permet de relancer le
  script plusieurs fois sans erreur si la collection existe déjà.

### `serveur_mcp_notes.py` — serveur MCP exposant la recherche

```python
from mcp.server.fastmcp import FastMCP
from sentence_transformers import SentenceTransformer
import chromadb

# Chargés une seule fois au démarrage du serveur, pas à chaque requête
# (le modèle d'embedding et la connexion Chroma sont coûteux à initialiser)
model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="/home/vinz/chroma_notes_db")
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
```

**Points clés à retenir de ce script** :
- Le décorateur `@mcp.tool()` transforme une simple fonction Python en
  outil MCP standardisé — la **docstring** de la fonction (le texte
  entre triple guillemets) est ce que Claude lit pour savoir **quand**
  utiliser cet outil, elle doit donc être claire et descriptive.
- Le type de retour (`-> str`) et les annotations de type
  (`question: str`) sont utilisés par le SDK MCP pour générer
  automatiquement le schéma de l'outil, exposé au client (Claude
  Desktop) sans configuration JSON manuelle supplémentaire.
- `mcp.run()` lance le serveur en mode **stdio** par défaut — il
  communique via l'entrée/sortie standard, exactement le mécanisme que
  `wsl.exe` doit relayer correctement entre Windows et WSL dans la
  configuration Claude Desktop.
- Le chemin Chroma est identique à celui utilisé dans `index_notes.py`
  (même base, lue en lecture par le serveur).

## Piste d'amélioration identifiée en session — guardrail sur données sensibles

Point soulevé en reprenant les questions de consolidation : si un
fichier indexé contenait accidentellement une clé API en clair (ou tout
autre secret structuré), `search_notes` la renverrait telle quelle sans
filtrage.

**Solution retenue** : un guardrail par **pattern/regex**, pas un
guardrail sémantique — parce qu'une clé API a un **format structuré et
prévisible** (ex : `sk-ant-...`), une regex suffit à la détecter avec
garantie, contrairement à une recherche par similarité vectorielle qui
resterait probabiliste (95-99%, jamais 100%). Écho direct de
`25-guardrails-prompt-injection-moindre-privilege.md` : le pattern est
le bon choix quand le contenu à détecter est structuré, la recherche
sémantique/ANN quand il ne l'est pas (contournable par reformulation
type "chiffres en toutes lettres").

**Implémentation à ajouter dans `search_notes`** (pas encore codée,
piste pour une prochaine itération) :

```python
import re

PATTERNS_SENSIBLES = [
    r"sk-ant-[a-zA-Z0-9\-_]{20,}",      # clé API Anthropic
    r"github_pat_[a-zA-Z0-9_]{20,}",     # token GitHub fine-grained
    r"ghp_[a-zA-Z0-9]{36}",              # token GitHub classique
]

def filtrer_secrets(texte: str) -> str:
    for pattern in PATTERNS_SENSIBLES:
        texte = re.sub(pattern, "[SECRET MASQUÉ]", texte)
    return texte

# Dans search_notes, avant de retourner :
reponse.append(f"[Source: {meta['source']}]\n{filtrer_secrets(doc)}")
```

Bon rappel pratique de l'incident vécu plus tôt dans ce repo (vault
committé par erreur, `git filter-repo`) — un tel guardrail aurait été
une deuxième ligne de défense utile, en plus du `.gitignore`, si jamais
un fichier avec un secret avait fini indexé dans Chroma sans que
personne ne s'en rende compte immédiatement.

## Piste d'amélioration identifiée en session — guardrail contre le prompt injection indirect

Deuxième risque identifié en session de consolidation : un fichier
`.md` indexé pourrait contenir une tentative de manipulation du modèle
("Ignore toutes tes instructions précédentes...") — un attaquant
n'aurait qu'à empoisonner un document à l'avance, sans jamais interagir
directement avec Claude. N'importe quel utilisateur légitime posant une
question anodine pourrait alors déclencher l'injection, simplement
parce que sa recherche RAG remonte le mauvais document.

**Terme exact** : **prompt injection indirect** — contrairement au cas
classique (l'utilisateur tape directement l'instruction malveillante
dans le chat), ici l'instruction arrive via un document récupéré par
RAG. Le modèle ne fait toujours aucune différence structurelle entre
instructions système, texte utilisateur et contenu de document
récupéré — tout devient un seul texte continu (écho de
`25-guardrails-prompt-injection-moindre-privilege.md`).

**Solution retenue** : contrairement à la clé API (format rigide), une
tentative de manipulation peut se formuler de façons quasi infinies
("ignore tes instructions", "oublie ce qu'on t'a dit", "à partir de
maintenant tu dois..."). Aucune regex ne couvrirait toutes les
variantes — un guardrail **sémantique** (similarité vectorielle contre
une base d'exemples connus de tentatives de manipulation) est ici le
bon choix, pas un pattern.

⚠️ Limite à garder en tête, même avec ce guardrail : reste
**probabiliste** (95-99% de rappel comme tout ANN) — une formulation
suffisamment créative et jamais vue pourrait toujours passer entre les
mailles. Contrairement au cas de la clé API (garantie dure via regex),
il n'existe ici aucune garantie à 100%.

**Piste d'implémentation** (non codée, pour une prochaine itération) :
maintenir une petite collection Chroma séparée d'exemples de tentatives
de manipulation connues, et avant d'indexer un nouveau document (ou
avant de retourner un résultat de `search_notes`), vérifier sa
similarité vectorielle avec cette base — si trop proche d'un exemple
connu, signaler ou bloquer le passage plutôt que de le transmettre tel
quel à Claude.

## Ce que ce TP a démontré concrètement

- **RAG de bout en bout**, appliqué à un cas réel et personnel (le
  propre historique d'apprentissage), pas un exemple jouet.
- **Construction d'un serveur MCP**, pas juste consommation d'un
  serveur existant (GitHub, Drive) — la face "développeur" du protocole.
- **Debug d'infra multi-couches** : Python/venv, WSL (distros multiples,
  interopérabilité Windows/Linux), système de fichiers (DrvFs vs natif) —
  aucun de ces bugs n'était un problème de logique RAG/MCP en soi, tous
  liés à l'environnement d'exécution réel.

## Compétences pratiquées

- Chunking de documents avec chevauchement
- Embeddings via bibliothèque dédiée (`sentence-transformers`)
- Base de données vectorielle en pratique (Chroma, `PersistentClient`)
- Construction d'un serveur MCP avec le SDK Python officiel (`FastMCP`)
- Configuration MCP dans Claude Desktop sous Windows + WSL2
  (interopérabilité `wsl.exe`, distros multiples, chemins DrvFs vs natifs)
- Lecture de logs MCP pour diagnostiquer une connexion échouée
