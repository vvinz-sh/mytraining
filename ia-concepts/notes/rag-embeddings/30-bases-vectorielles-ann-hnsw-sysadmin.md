# IA — Bases de données vectorielles en profondeur

Approfondissement du panorama théorique déjà vu
(`27-panorama-outils-ecosysteme-hermes-mcp.md`), avec le mécanisme
technique réel et l'angle maintenance/sysadmin.

## Ce que le SQL classique ne peut pas faire

Une requête SQL (`WHERE titre = '...'`) fait une correspondance
**exacte** — aucune notion de sens. Chercher "tous les articles sur le
même sujet, même avec des mots différents" ('Panne réseau' vs 'Coupure
de connexion') est impossible avec un simple `WHERE`.

**Solution de contournement classique** : ajouter des tags/catégories
manuels. Mais limite structurelle, pas juste pratique : les tags forcent
une classification **discrète et prédéfinie** (un article est dans telle
catégorie ou non), alors que le sens d'un texte est **continu et
multi-dimensionnel** — un article peut appartenir "un peu" à plusieurs
catégories à la fois. Les tags obligent à trancher arbitrairement, ou à
multiplier les catégories jusqu'à l'ingérable (dérive, oublis, maintenance
impossible à l'échelle).

Les embeddings n'ont pas ce problème : le vecteur capture naturellement
ce mélange de sens sans qu'un humain décide à l'avance des catégories —
écho direct de l'hypothèse distributionnelle (`23-...md`), tout émerge
des données, aucune catégorie prédéfinie nécessaire.

## Pourquoi un index SQL classique (B-tree) ne marche pas sur des vecteurs

Un B-tree fonctionne parce qu'il existe un **ordre total** sur les
valeurs (5 < 8 < 12), permettant une recherche dichotomique en O(log n).
Des vecteurs à 100+ dimensions n'ont **pas d'ordre naturel** — impossible
de dire "ce vecteur est plus petit qu'un autre", seulement calculer une
distance entre deux vecteurs précis. Un B-tree classique est donc
inutilisable ici.

## La solution : recherche approximative (ANN) et HNSW

Comparer une requête à **chaque** vecteur un par un (recherche exacte)
donnerait un temps de réponse énorme sur des millions de documents.

**ANN (Approximate Nearest Neighbor)** : au lieu du résultat exact,
trouve rapidement des vecteurs **très probablement proches**, sans
garantie à 100%, mais avec une précision suffisante en pratique (souvent
95-99% de rappel).

**HNSW (Hierarchical Navigable Small World)** : une des techniques ANN
les plus utilisées — un graphe à plusieurs niveaux : les niveaux
supérieurs ont peu de nœuds très espacés (navigation rapide et grossière,
comme des autoroutes sur une carte), les niveaux inférieurs ont tous les
nœuds avec des liens fins (navigation précise, comme des routes locales).
La recherche descend niveau par niveau, se rapprochant progressivement
de la bonne zone plutôt que de tout parcourir.

## Pourquoi l'approximation est acceptable en RAG mais jamais en transaction bancaire

- **Transaction bancaire** : une erreur "approximative" (mauvais compte)
  est catastrophique — un seul mauvais résultat casse tout, exactitude
  garantie à 100% obligatoire.
- **RAG** : si le 5ᵉ document récupéré sur 5 n'est pas *exactement* le
  plus pertinent mais reste proche en sens, l'impact est minime — 4 bons
  documents sur 5 suffisent largement au LLM pour générer une réponse
  correcte.

Le contexte détermine si l'approximation est acceptable : la conséquence
d'une petite erreur doit être négligeable pour justifier le compromis
vitesse/précision de l'ANN.

## Implication pour un guardrail de sécurité basé sur la similarité

Si un guardrail vérifie qu'une réponse générée n'est pas vectoriellement
proche d'un contenu interdit connu (via une base d'exemples), l'imprécision
structurelle de l'ANN (rappel de 95-99%, pas 100%) peut laisser passer
un contenu réellement problématique — **sans aucune reformulation
délibérée de la part d'un attaquant**, juste par construction
probabiliste de l'algorithme. Une faille silencieuse et structurelle,
différente du contournement de pattern/regex vu dans
`25-guardrails-prompt-injection-moindre-privilege.md`.

Dilemme de conception : pousser l'ANN vers 99,9% de précision fait
perdre l'avantage de vitesse qui le justifiait — jusqu'à potentiellement
revenir au coût d'une recherche exhaustive. Pour un guardrail de
sécurité critique, ce compromis mérite d'être pesé soigneusement, voire
d'accepter une recherche exacte (plus lente) plutôt qu'ANN, précisément
parce que l'enjeu de sécurité dépasse celui d'une simple recherche RAG
documentaire.

## Angle sysadmin — ce que ça change pour la maintenance

### Restauration (RTO) plus lourde qu'en SQL classique

Le graphe HNSW est construit progressivement (insertion vecteur par
vecteur, création de niveaux et de liens). Un simple dump des données
brutes (vecteurs + métadonnées, sans le graphe) ne suffit pas à la
restauration : il faut **reconstruire tout le graphe depuis zéro**,
potentiellement des heures sur des millions de vecteurs — contrairement
à un index B-tree SQL qui se reconstruit généralement bien plus vite.

Conséquence pratique : le vrai RTO n'est pas juste "temps de restaurer
les données" mais doit inclure le **temps de reconstruction de l'index
vectoriel**, potentiellement le facteur dominant. Les bases vectorielles
sérieuses (Qdrant, Weaviate...) permettent de sauvegarder un **snapshot
incluant le graphe déjà construit** — la stratégie de backup doit
spécifiquement viser ce type de snapshot, pas un simple export de
données brutes.

### Insertion incrémentale (contrairement à une intuition de recalcul complet)

Bonne nouvelle : HNSW est conçu pour insérer un nouveau vecteur
**incrémentalement** — pas besoin de recalculer tout le graphe, juste
trouver où placer le nouveau nœud et créer ses quelques liens locaux.
Pas de dégradation de performance immédiate à chaque ajout, contrairement
à une intuition naïve de "recalcul complet à chaque insertion".

### Suppressions — équivalent du VACUUM PostgreSQL

Supprimer un vecteur peut laisser un "trou" structurel — plus subtil
qu'en SQL classique : le nœud supprimé servait potentiellement de
**pont de navigation** (un nœud de niveau supérieur sert de raccourci
vers plusieurs zones du niveau inférieur). Le supprimer peut fragmenter
localement le graphe, ou forcer les recherches à emprunter des chemins
plus longs pour contourner le trou — pas juste "de l'espace gaspillé"
comme en SQL, mais une possible dégradation réelle de la qualité de
recherche dans cette zone.

D'où une pratique de maintenance équivalente au `VACUUM`/`REINDEX` :
une **réindexation périodique** (rebuild complet ou partiel du graphe)
après un volume significatif de suppressions/mises à jour — à planifier
en maintenance programmée, avec un coût potentiellement plus lourd
qu'un VACUUM SQL puisque ça touche la topologie du graphe entier.

## Résumé — SQL classique vs base vectorielle

| Aspect | SQL classique | Base vectorielle |
|---|---|---|
| Recherche | Exacte (`WHERE`) | Approximative (ANN/HNSW) |
| Structure d'index | B-tree (ordre total) | Graphe multi-niveaux (pas d'ordre naturel) |
| Restauration | Rapide, index reconstruit vite | Lente si pas de snapshot du graphe inclus |
| Insertion | Rapide (B-tree) | Incrémentale, rapide aussi (pas de recalcul complet) |
| Suppression | Espace récupéré (VACUUM) | Peut fragmenter le graphe (réindexation périodique nécessaire) |
| Garantie de précision | 100% | 95-99% (compromis assumé pour la vitesse) |

## Aparté — les bases vectorielles sont-elles utilisées dans le ticketing (Jira, ServiceNow) ?

Question posée en session : pourquoi ne voit-on presque jamais de base
vectorielle dans les outils de ticketing classiques, alors que le
problème des tags (lourd, sujet à dérive/oublis) semble un candidat
idéal ?

### Deux raisons identifiées

1. **Reporting fiable vs recherche approximative** — les tags/catégories
   servent aussi à des rapports chiffrés (SLA, facturation, stats). Un
   rapport a besoin de catégories **discrètes et fiables**, incompatible
   avec la nature approximative de l'ANN (95-99% de rappel, jamais
   100%). Le compromis vectoriel est acceptable pour de la recherche
   exploratoire/diagnostic, jamais pour du comptage garanti.
2. **Coût d'adoption élevé** — ajouter une base vectorielle en plus
   d'une infra SQL déjà établie depuis longtemps (avec ses propres
   sauvegardes, sa propre maintenance) représente un coût non
   négligeable, à mettre en balance avec le temps humain perdu en
   maintenance de tags (dérive, oublis, catégories jamais assez fines).

### Vérification concrète sur des outils réels

Recherche faite sur ServiceNow et Jira :
- **ServiceNow "AI Search"** : le moteur natif fait par défaut de la
  **correspondance de termes classique et un classement de pertinence**
  — pas de recherche vectorielle par défaut. La recherche vectorielle
  sémantique n'a été ajoutée qu'à partir d'une version récente
  (Vancouver Patch 4), comme un **mode alternatif** utilisé par
  certaines fonctionnalités IA spécifiques (Now Assist), pas le moteur
  historique du produit.
- **Jira** : pas de recherche vectorielle native par défaut non plus.
  Ce qui existe : des **intégrations tierces** (entreprises connectant
  Qdrant/Pinecone via l'API Jira) ou des projets de recherche
  académiques, pas une fonctionnalité socle d'Atlassian. Les
  fonctionnalités IA plus récentes (Atlassian Intelligence) commencent
  à intégrer ce type de capacité.

**Conclusion** : les outils de ticketing ont traditionnellement
fonctionné sur tags/texte/dates. La recherche vectorielle y arrive
progressivement, en couche additionnelle, souvent via des
fonctionnalités IA premium récentes — pas encore le socle par défaut.

## Leçon importante (pas 100% technique, mais à souligner) — le nom d'une fonctionnalité n'est pas une preuve de son mécanisme

Point de vigilance qui dépasse le cas du ticketing : le nom d'une
fonctionnalité contenant "AI" ou "Semantic" **ne garantit jamais** qu'il
y a réellement des embeddings/vecteurs derrière.

Exemple confirmé : **ServiceNow "AI Search"**, par défaut, se comporte
comme un moteur de correspondance de termes classique — la recherche
vectorielle sémantique **remplace** ce mécanisme normal seulement quand
elle est activée, ce n'est pas le comportement de base malgré le nom du
produit.

Cas similaire trouvé ailleurs : **Azure "Semantic ranker"** précise
explicitement dans sa propre documentation qu'il **n'utilise ni IA
générative ni vecteurs** pour son classement — malgré le mot "Semantic"
dans son nom.

**Règle à retenir** : un nom de fonctionnalité sophistiqué ("AI",
"Semantic", "Intelligent"...) peut très bien recouvrir un algorithme de
classement classique (BM25, TF-IDF, pondérations) sans aucun rapport
avec le ML/les embeddings vus dans ce module — souvent du marketing
produit plutôt qu'une description technique fidèle. Réflexe à garder :
vérifier la doc technique réelle plutôt que de supposer à partir du nom
commercial, exactement le fil conducteur de toutes les sessions IA de ce
repo.
