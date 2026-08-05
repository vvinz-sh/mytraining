# Elasticsearch — Architecture de base : nœud, index, shard/replica, mapping

Premier point théorique du Palier 5, en continuité directe de
l'installation ES/Kibana (note 31) — appuyé sur des observations
concrètes déjà faites (`_cluster/health` en `yellow`, un event de test
indexé sans mapping défini à l'avance) plutôt que de repartir de zéro.

## Nœud

Une instance du process Elasticsearch — un process Java, un
`elasticsearch.yml`. Le cluster de test (note 31) n'en a qu'un
(`number_of_nodes: 1`).

## Index, shard, replica

Un **index** stocke la donnée. Il est découpé en **shards**
(sous-divisions de l'index, réparties potentiellement sur plusieurs
nœuds d'un cluster). Un **replica** est une copie — pas de l'index
entier, mais de **chaque shard individuellement** (un shard primaire →
une ou plusieurs copies replica de ce même shard, idéalement sur un
nœud différent du primaire).

Constat déjà fait en pratique (note 31) : `_cluster/health` en
`yellow`, pas `green`, sur le cluster de test — un replica est
configuré mais ne peut jamais se placer sur un cluster mono-nœud
(aucun autre nœud pour l'héberger). Pas une panne, juste "personne
pour dupliquer cette donnée ailleurs".

## Mapping dynamique : mécanisme générique, pas spécifique à un produit

Hypothèse de départ (écartée) : Elasticsearch aurait reconnu la
structure parce que la donnée "vient de Filebeat". En réalité, deux
mécanismes bien distincts, tous deux génériques :

1. **Champs ECS déjà couverts par des templates d'index intégrés** —
   n'importe quel client qui respecte la convention de nommage ECS en
   bénéficie automatiquement (constaté : le test `stdin` via Logstash,
   sans jamais toucher à Filebeat, en a profité aussi)
2. **Mapping dynamique pour tout champ inconnu/custom** — Elasticsearch
   regarde uniquement le **type JSON** de la valeur reçue (string,
   nombre, date reconnaissable) et devine un type en conséquence,
   sans aucune connaissance du produit d'origine

## Piège du mapping dynamique sur une string : `text` + `.keyword`, pas un choix

Une string reçue via mapping dynamique devient **automatiquement les
deux à la fois** :
- **`text`** — la chaîne est *analysée* (tokenisée : découpée en mots
  individuels, mise en minuscule, etc.), ce qui permet de retrouver un
  document en cherchant un simple mot-clé sans connaître la phrase
  entière
- **`keyword`** — la chaîne est conservée **intacte**, nécessaire dès
  qu'on veut trier, filtrer ou agréger sur la valeur **exacte** (un
  champ découpé en mots séparés ne permet ni l'un ni l'autre
  proprement)

Pas une redondance inutile — les deux répondent à des besoins
incompatibles avec un seul type de stockage.

## Mapping dynamique : le vrai risque n'est pas juste "moins précis"

Une fois le type d'un champ fixé par mapping dynamique (déterminé par
le **premier** document qui l'introduit), tout document **suivant**
envoyant une valeur incompatible pour ce même champ est **rejeté à
l'indexation** — une `mapping_exception`, pas juste un enregistrement
à trier plus tard. Le document n'entre jamais dans l'index.

**Lien direct avec le DLQ natif (note 30)** : ce scénario précis est
exactement le cas "documents individuels refusés (code 400)" qui
restait abstrait dans la note 30. Exemple concret tracé : un champ
`RC` vaut `0` sur le premier event (mapping dynamique décide
`integer`), un event suivant envoie `RC: "erreur"` (string) — la
requête bulk globale réussit (`200 OK`), mais cet event précis est
rejeté individuellement (`400`, conflit de mapping). Avec le DLQ
activé, cet event atterrit dans la Dead Letter Queue plutôt que d'être
perdu silencieusement, retraitable plus tard (correction du type, puis
ré-émission).

**Mapping statique** — fixer le type de chaque champ à l'avance
(souvent via un **index template**, appliqué automatiquement à tout
futur index correspondant à un pattern de nom), pour éviter que le
premier document "au hasard" décide arbitrairement du type pour tous
les suivants. Pas encore mis en pratique — repéré comme utile
maintenant que le piège concret (rejet, pas juste ambiguïté) est
compris.

## Résumé

1. Un shard est une sous-division d'un index ; un replica copie
   chaque shard individuellement, pas l'index en bloc
2. `yellow` sur un mono-nœud = replica non placé, pas une panne
3. Mapping ECS reconnu = templates intégrés génériques ; mapping
   inconnu = déduction par type JSON, aucun des deux n'est spécifique
   à un produit Elastic
4. Une string en mapping dynamique produit toujours `text` (analysé,
   recherche) + `.keyword` (intact, tri/filtre/agrégation) — deux
   besoins incompatibles, pas une redondance
5. Le vrai risque du mapping dynamique sur la durée : rejet
   (`mapping_exception`) d'un document dont un champ change de type,
   pas juste une gêne pour les dashboards — cas concret directement
   couvert par le DLQ natif (note 30)

## Lien avec les notes existantes

`31-installation-elasticsearch-kibana.md` (cluster de test, `yellow`
observé, event indexé sans mapping défini), `30-dead-letter-queue-native.md`
(scénario "document rejeté avec code 400", ici rendu concret avec un
exemple de conflit de type de champ).
