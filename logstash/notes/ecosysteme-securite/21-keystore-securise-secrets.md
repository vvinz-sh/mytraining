# Logstash — Keystore : sécuriser les secrets, testé en pratique

Complète le Palier 1 — dernier point de config avant `pipeline-to-pipeline`.

## Le problème résolu

Nos pipelines n'avaient jamais eu besoin de secret jusqu'ici (`stdin`/
`stdout`, aucune authentification). Le premier vrai besoin
apparaîtra au Palier 5 (sortie Elasticsearch, sécurisé par défaut
depuis 8.0 — *"Logstash throws an exception and the processing
pipeline is halted if authentication fails"*), et potentiellement
plus tôt pour la passphrase d'une clé TLS chiffrée (note 18).

**Risque identifié sans Keystore** : un mot de passe en clair dans un
`.conf` committé via `git-push-perso` finit dans l'**historique Git
pour toujours**, même après suppression du fichier — un vrai risque
concret pour notre propre workflow, pas théorique.

## Keystore et permissions filesystem : complémentaires, pas redondants

Question posée avant de pratiquer : la doc dit *"rather than relying
on file system permissions... use the Logstash keystore"*, mais un
guide communautaire recommande aussi *"restrict the keystore file
permissions to 0600"* — contradiction ?

**Non, deux couches protégeant des scénarios différents** :
- `.conf` fuite, keystore intact → protégé (le `.conf` ne contient que
  `${ES_PWD}`, inutilisable sans le keystore)
- Keystore fuite malgré permissions → chiffrement protège, mais pas
  éternellement (un algorithme d'aujourd'hui peut être cassé demain —
  ne jamais compter sur "chiffré = définitivement sûr")
- Permissions filesystem → protection locale immédiate, moindre
  privilège, indépendante de la solidité du chiffrement

**Principe retenu** : même en lab, aucun fichier keystore réel ne
devrait être poussé sur le repo public — question de discipline,
pas seulement de nécessité immédiate.

## API key plutôt que user/password pour Elasticsearch

Recommandation Elastic officielle : privilégier une **API key** sur
`user`/`password` pour la sortie Elasticsearch. Avantages confirmés,
cohérents avec le principe de moindre privilège déjà pratiqué
(deploy key GitHub scopée, `git-push-perso`) :
- **Scope réduit** via `role_descriptors` — ex : `write`/`create`
  limité à des index `logstash-api-key-*`, pas un compte utilisateur
  aux droits potentiellement plus larges
- **Révocation individuelle** — une clé compromise se révoque seule,
  sans casser d'autres pipelines partageant le même compte
- **Traçabilité** — une clé nommée par host/pipeline

**Piège à connaître** : la création d'une API key renvoie **deux**
valeurs — la brute `id:api_key` (à utiliser dans `api_key => "..."`)
et une version encodée en base64 (`"encoded"`, pour un usage HTTP
direct différent) — utiliser la mauvaise échoue silencieusement ou
avec une erreur peu claire.

## Test pratique complet

### Création (protégée par mot de passe)

```bash
export LOGSTASH_KEYSTORE_PASS="..."
sudo -u logstash /usr/share/logstash/bin/logstash-keystore --path.settings /etc/logstash create
```

### Ajout d'une entrée

```bash
/usr/share/logstash/bin/logstash-keystore --path.settings /etc/logstash add ES_PWD
```

### Deux échecs diagnostiqués avant le succès

**Échec 1** : `${es_pwd}` puis `${ES_PWD}` échouent tous les deux au
premier essai, malgré une entrée confirmée par `add`/`list`.

**Diagnostic** : le pipeline de test était lancé **sans**
`--path.settings /etc/logstash` — Logstash cherchait le keystore dans
son emplacement par défaut, pas là où il avait réellement été créé.
Combiné à `LOGSTASH_KEYSTORE_PASS` non réexportée dans le shell du
test — deux prérequis manquants, pas un bug de casse.

**Correction** : relancer avec les deux paramètres présents dans le
même shell :
```bash
export LOGSTASH_KEYSTORE_PASS="..."
/usr/share/logstash/bin/logstash -f pipeline.conf --path.settings /etc/logstash --path.data /home/vinz/logstash-lab/data
```

Résultat : `${ES_PWD}` correctement substitué, champ `PASSWORD`
affichant la vraie valeur stockée.

### Découverte empirique : insensible à la casse, contrairement à une source lue

Une source communautaire affirmait *"key names are case-sensitive
and must match the keystore entry exactly"*. Testé directement :
`${ES_PWD}` (majuscules, casse d'ajout d'origine) **et** `${es_pwd}`
(minuscules, casse affichée par `list`) fonctionnent **tous les
deux** une fois les deux prérequis corrigés. La documentation
officielle Elastic ne mentionnait pas cette contrainte de casse —
la source communautaire était probablement imprécise ou datée sur ce
point précis. Résultat vérifié par test, pas simplement cité d'une
doc tierce sans confirmation.

### Test négatif (mauvais mot de passe)

Testé rapidement : un `LOGSTASH_KEYSTORE_PASS` incorrect empêche le
pipeline d'atteindre l'étape `input` — refus net, message d'erreur
Java clair dès les premières lignes malgré sa longueur.

## Résumé

1. Premier vrai besoin de secret : Palier 5 (Elasticsearch, sécurisé
   par défaut) — jamais rencontré avant faute d'authentification sur
   `stdin`/`stdout`
2. Keystore et permissions filesystem sont complémentaires, pas
   redondants — chacun protège un scénario de fuite différent
3. API key préférée à `user`/`password` pour Elasticsearch — scope
   réduit, révocation individuelle, cohérent avec le principe de
   moindre privilège déjà pratiqué ailleurs
4. `${KEY}` fonctionne quelle que soit la casse en pratique, malgré
   une affirmation contraire trouvée dans une source communautaire —
   vérifié par test plutôt qu'accepté sur parole
5. Deux prérequis systématiquement nécessaires au lancement (pas
   seulement à la création) : `--path.settings` pointant vers le bon
   dossier, `LOGSTASH_KEYSTORE_PASS` réexportée dans le même shell

## Lien avec les notes existantes

`18-panorama-tls-mtls.md` (passphrase de clé TLS, autre candidat
Keystore), README Palier 5 (premier vrai besoin de secret,
Elasticsearch), `01-panorama-alternatives-interfacage-securite.md`
(moindre privilège, principe déjà appliqué à `git-push-perso`).

## Sources

- [Secrets keystore for secure settings (Elastic, 8.19)](https://www.elastic.co/guide/en/logstash/8.19/keystore.html)
- [Secure your connection to Elasticsearch (Elastic Docs)](https://www.elastic.co/docs/reference/logstash/secure-connection)
- [How to add secrets to a Logstash keystore (Simplified Guide)](https://www.simplified.guide/elastic/logstash/keystore-add-entry)
- [How to use an Elasticsearch API key with Logstash output (Simplified Guide)](https://www.simplified.guide/elastic/logstash/api-use-key-elasticsearch)
- [Do you know: how to use Elastic API Keys in Logstash code? (Devoteam)](https://www.devoteam.com/expert-view/do-you-know-how-to-use-elastic-api-keys-in-logstash-code/)
