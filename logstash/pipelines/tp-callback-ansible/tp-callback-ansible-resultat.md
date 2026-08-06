# TP — Callback plugin `community.general.logstash` : résultat

Complète `tp-callback-ansible-draft.md`. Playbook `deployer_filebeat.yml`
rejoué contre une nouvelle VM (`rh8102.localdomain`) via le callback,
en TCP + `codec json`, sans passer par un fichier texte ni par
`multiline`/grok — contrairement au TP `ansible-playbook -v` auquel
celui-ci sert d'alternative (jamais dit explicitement pendant le TP,
comme prévu au draft).

## Mise en place

- `pip install python-logstash` sur le nœud de contrôle (WSL)
- `ansible.cfg` : `callbacks_enabled = timer, profile_tasks,
  community.general.logstash` (syntaxe moderne confirmée,
  `ansible-core 2.21.2`) + section `[callback_logstash]`
  (`server`, `port`, `type`) — `pre_command` laissé au défaut
  (exécute `ansible --version | head -1`, pensé pour tracer un commit
  git en CI/CD, pas pertinent ici)
- Logstash (Rocky) : pipeline nommé `ansible` ajouté à `pipelines.yml`,
  aux côtés de `beats-tls` déjà existant — les deux tournent
  simultanément sans conflit (`Pipelines running {:count=>2,
  :running_pipelines=>[:ansible, :"beats-tls"]}`)
- Input `tcp { port => 5000, codec => json, add_field =>
  {"[@metadata][beat]"=>"notify"}, add_field =>
  {"[@metadata][type]"=>"ansible"} }` (exemple de la doc officielle,
  conservé tel quel)
- Output `elasticsearch`, index dédié `ansible`, mot de passe `elastic`
  ajouté manuellement au Keystore Logstash pour ce test
  (`ssl_verification_mode => "none"`, CA non copié — hors scope de ce
  TP, déjà validé ailleurs sur le TP mTLS)

## Scénario pour obtenir les 4 statuts (`ok`/`changed`/`failed`/`skipped`)

Rôle Filebeat existant réutilisé tel quel (pas de modification), en
jouant sur une variable `host_vars` plutôt qu'en touchant au rôle :

1. **Run 1** — `filebeat_logs_path` pointé vers un fichier inexistant
   (`/var/log/mymessages`) → `ok` (Gathering Facts) + plusieurs
   `changed` + `failed` sur la task ACL (`Path not found or not
   accessible.`, confirmé : `ansible.posix.acl` échoue bien
   proprement sur un chemin inexistant, pas de comportement silencieux)
2. **Run 2** — variable corrigée → `ok=21 changed=8`, 0 échec
   (première exécution des tasks keystore, encore rien à `skipped`)
3. **Run 3** — relancé sans rien changer → `ok=17 changed=0 skipped=2`
   (tasks keystore conditionnées par leur `when:`, déjà peuplées)

Les 4 statuts couverts sur l'ensemble des 3 runs, aucun run
individuel n'ayant besoin de les avoir tous en même temps.

## Découvertes

**`@metadata` confirmé invisible dans la sortie**, malgré les deux
`add_field` de l'input — comportement voulu, pas un oubli. Deux
usages concrets clarifiés : (1) conditionnel dans un `filter`
(`if [@metadata][beat] == "notify" { ... }`, pour router différemment
selon la source quand plusieurs outils partagent le même input TCP —
cas d'usage concret identifié : un port mutualisé entre ce callback
et un futur autre flux), (2) ingrédient pour construire un vrai champ
visible via `sprintf` (`add_field => { "champ" => "%{[@metadata][type]}" }`).
Aucun des deux usages testé dans ce TP (pas de `filter` écrit), donc
comportement par défaut observé : présent pendant le traitement,
absent de la sortie finale.

**`ansible_result` en JSON encodé dans une string**, confirmé sur un
vrai event : `"{\"changed\": false, \"msg\": \"Path not found or not
accessible.\"}"` — cohérent avec la lecture du code source du
callback faite en amont du TP (`self._dump_results()`). Nécessiterait
un filtre `json` (note 28) pour l'exploiter en champs structurés,
non fait ici (hors scope, le TP visait juste l'ingestion).

**Deux natures d'events distinctes, pas une seule** — point du draft
resté ouvert, tranché en pratique :
- `ansible_type: task`/`start` — un event par task individuelle
- `ansible_type: finish` — un event de synthèse en fin de playbook,
  avec le récap déjà structuré :
  `{"rh8102.localdomain": {"ok": 17, "failures": 0, "changed": 0,
  "skipped": 2, ...}}` — les mêmes compteurs qu'on avait dû extraire
  à la main via `kv`/grok sur le TP `ansible-playbook -v`, ici déjà
  prêts à l'emploi sans aucun parsing

**Détour résolu : deux `ansible_play_id` différents observés au
départ, pour un seul run apparent.** Investigation : un premier
lancement avait en fait échoué très tôt (`Attempting to decrypt but
no vault secrets found`, oubli de `--ask-vault-pass`) — mais le
callback avait déjà émis ses events de démarrage
(`v2_playbook_on_start`/`v2_playbook_on_play_start`) **avant** que le
déchiffrement du vault n'échoue plus loin dans le déroulé. Pas un bug
du plugin, un artefact d'une commande mal lancée puis relancée
correctement.

## Comparaison implicite avec le TP `ansible-playbook -v`

Même objectif final (savoir, par task, le statut d'exécution d'un
playbook) atteint par deux voies opposées :
- **`ansible-playbook -v`** : sortie texte, recollage `multiline`,
  grok sur mesure, bug `kv`/`target` découvert en cours de route —
  plusieurs sessions de travail
- **Callback direct** : JSON structuré nativement, aucun grok, champs
  déjà nommés (`status`, `ansible_task`, `ansible_result`...) — une
  seule session

Le second n'est pas juste "plus simple" — deux différences
structurelles, pas de degré :

**1. Live vs post-exécution.** `ansible-playbook -v` produit un
fichier texte à **relire après coup** — une analyse a posteriori,
même si le recollage `multiline` peut tourner en continu sur un
fichier qui grossit. Le callback, lui, envoie chaque event **au fil
de l'exécution du playbook**, en direct — un statut de task apparaît
dans Elasticsearch quasiment au moment où elle se termine, pas après
relecture d'un fichier de sortie. Deux cas d'usage réellement
différents, pas juste deux chemins vers le même résultat.

**2. Scalabilité multi-hosts.** Le recollage `multiline` sur
`ansible-playbook -v` ne tenait que parce que le TP portait sur **un
seul host** (limite déjà notée explicitement dans le draft d'origine
de ce TP-là) — avec plusieurs hosts en cible simultanément, les
lignes de sortie de plusieurs machines s'entremêlent dans le même
flux texte, rendant le recollage `multiline` fragile voire impossible
à faire correctement (même famille de risque que celui déjà identifié
en note 25 sur Beats : ne jamais faire du recollage multiline sur un
flux qui mélange plusieurs sources). Le callback, lui, n'a **aucun**
souci de ce genre : chaque event est déjà structuré et individuellement
tagué (`ansible_host`), quel que soit le nombre de hosts ciblés en
parallèle — rien à recoller, donc rien à mélanger.

## Limite de sécurité non traitée dans ce TP (contrairement au TP Filebeat)

Contrairement au TP `tp-filebeat-rh8103`, aucun effort mTLS n'a été
fait ici — pas un oubli, une **limite structurelle** du callback lui-même,
identifiée après coup.

**Côté Logstash (serveur, input `tcp`)** : le plugin `tcp` supporte
bel et bien le TLS nativement — mêmes options que celles déjà
manipulées sur l'input `beats` (`ssl_enabled`, `ssl_certificate`,
`ssl_key`, `ssl_certificate_authorities`,
`ssl_client_authentication => "required"` pour du mTLS complet).
Rien de nouveau à apprendre côté Logstash.

**Côté callback Ansible (client)** : aucune option SSL/TLS parmi
celles documentées (`server`, `port`, `type`, `pre_command`). Le
callback s'appuie sur `python-logstash`, qui ouvre un socket TCP
simple — pas de couche TLS prévue dans son fonctionnement, contrairement
à Filebeat (`ssl.*` intégré nativement dans `output.logstash`).
**Conséquence concrète** : activer le TLS côté input Logstash rendrait
le callback tout simplement incapable de se connecter — pas un
réglage à ajuster, une fonctionnalité absente du client. Le flux
circule donc **en clair** sur le réseau, quoi qu'on fasse côté
Logstash.

**Sécurité réelle de ce flux, telle qu'elle est aujourd'hui** :
repose entièrement sur le filtrage réseau/firewall (qui peut
atteindre le port 5000), rien au niveau applicatif — pas
d'authentification, pas de chiffrement, pas de vérification d'identité
du client comme le permettait `ssl_verify_mode: force_peer` sur
l'input `beats`.

**Pistes de contournement, non testées ici** (le client ne sachant
pas faire du TLS, la solution passe par encapsuler le flux dans un
tunnel chiffré au niveau transport, transparent pour le callback) :
- **Tunnel SSH** (`ssh -L 5000:localhost:5000 rocky.localdomain`) —
  le plus simple ici, réutilise un accès déjà en place entre WSL et
  Rocky, aucune modification de la config du callback
- **`stunnel`** — outil dédié à ce cas précis, ne dépend pas d'une
  session SSH active contrairement au tunnel
- **VPN/WireGuard** entre les deux machines — chiffre tout le trafic,
  pas seulement ce flux ; pertinent seulement si d'autres flux à
  protéger existent aussi

**Confirmation empirique du point ci-dessus, et découverte plus
grave qu'attendu.** Deux tests réalisés :

1. **TLS activé côté input Logstash, sans exiger l'auth client**
   (`ssl_enabled => true`, pas de `ssl_client_authentication`) — le
   callback continue d'envoyer en TCP simple, sans savoir parler TLS.
   Côté Logstash : erreurs en boucle,
   `Caused by: io.netty.handler.ssl.NotSslRecordException: not an SSL/TLS record:`.
   Côté Ansible : **playbook exécuté sans le moindre avertissement**,
   même sans `-v` — rien n'indique que l'envoi des logs a échoué.
2. **Logstash complètement arrêté** — même résultat : playbook
   exécuté normalement, **aucune erreur ni avertissement** affiché par
   le callback, alors qu'il ne peut joindre personne.

**Conséquence à retenir, au-delà du seul défaut de TLS** : le
callback échoue **silencieusement** dans tous les cas de coupure de
connectivité testés, pas seulement sur un mismatch TLS. Un opérateur
qui compte sur ce flux pour de l'audit/traçabilité pourrait croire
disposer d'un historique complet dans Logstash alors qu'il n'a rien
reçu du tout, sans aucun signal l'alertant du problème — un vrai
risque opérationnel, indépendant du manque de chiffrement en soi.

## Lien avec les notes existantes

`26-multiline-implementation-ansible-v.md` et
`tp-parsing-ansible-verbose-resultat.md` (l'approche manuelle
comparée), `28-codec-filtre-json-approfondi.md` (JSON-dans-JSON,
`ansible_result` à parser plus tard si besoin), `01-panorama-alternatives-interfacage-securite.md`
(port API 9600 — même famille de vigilance sur un port TCP exposé),
`tp-filebeat-rh8103-resultat-phase2.md` (mTLS effectivement mis en
place là où le client le permettait — contraste direct avec la
limite du callback ici).
