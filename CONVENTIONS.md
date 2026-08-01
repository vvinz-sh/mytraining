# Conventions du repo — structure des modules

Document de référence pour structurer un nouveau module (après
`ia-concepts` et `logstash`), dégagé des patterns qui ont émergé
naturellement plutôt que décidés à l'avance. À ajuster si un futur
module révèle un meilleur pattern — ce document lui-même peut évoluer.

## Structure de dossier par module

```
module/
├── README.md              — suivi détaillé (voir plus bas)
├── notes/                 — numérotation indépendante, repart à 1
├── exercices/ (ou pipelines/) — code/config, un dossier par sujet/TP
├── ressources-externes.md — ressources générales du module
└── rsc/                   — images (radar, captures d'écran)
```

Le nom du second dossier (`exercices/` vs `pipelines/`) s'adapte au
vocabulaire naturel du domaine — pas de règle rigide, choisir ce qui
parle le plus dans le contexte du module.

## Organisation de `notes/`

- **Numérotation indépendante** par module, repart à 1 — pas de
  numérotation globale partagée entre modules
- **Reste plate au départ** (`notes/01-xxx.md`, `notes/02-xxx.md`...)
- **Bascule en sous-dossiers thématiques** seulement une fois qu'un
  vrai pattern se dégage naturellement du contenu accumulé — jamais
  anticipée ou décidée à l'avance sur un module encore jeune
- Une fois la bascule faite, la numérotation des fichiers est
  **conservée** (déplacement via `git mv`, pas renommage) — elle sert
  d'historique de l'ordre d'écriture, distinct du classement
  thématique
- **Une note peut couvrir plusieurs thèmes à la fois** — accepter
  cette imperfection plutôt que fragmenter une note ou forcer un
  classement incertain. Si une note ne rentre pas naturellement dans
  un thème existant, la laisser à plat dans `notes/` en attendant
  qu'un meilleur classement se révèle avec plus de contenu

## Convention d'une note

- Section `## Sources` en fin de note — uniquement les liens
  **réellement utilisés** pour rédiger cette note précise, pas une
  liste générale (celle-ci va dans `ressources-externes.md`)
- Section "Lien avec les notes existantes" — tisser les ponts internes
  au module, et vers d'autres modules quand pertinent
- Un design doc (`*-draft.md`) précède un TP ; un `*-resultat.md` le
  documente une fois exécuté

## Méthodologie du radar de couverture

- Mesure la **couverture du repo** (notes/scripts/résultats testés),
  jamais la maîtrise personnelle de la personne qui écrit le module
- Le "10" de l'échelle doit être un **plafond externe fixe** — un
  profil de référence estimé (ex : "quelqu'un pratiquant le sujet au
  quotidien depuis 2-3 ans"), jamais le propre plan du module qui
  évolue au fil des sessions. Comparer à son propre plan gonfle
  artificiellement le score, puisque le dénominateur bouge dans le
  bon sens à mesure qu'on avance
- Toujours accompagner le radar d'un texte explicite précisant ce que
  représente le "10" et les limites de l'estimation (approximative,
  pas vérifiée par une source externe formelle sauf mention contraire)
- Si une partie du module est un simple bonus (pas l'objectif
  central), le préciser explicitement pour qu'un score bas à cet
  endroit ne soit pas lu comme un retard préoccupant

## Progression organique acceptée

- Démarrer par une organisation **chronologique** (paliers, vagues,
  phases) est normal et attendu pour un module jeune
- Basculer vers une organisation **thématique** une fois la densité
  de contenu suffisante — sans cependant réorganiser le README
  principal tant que l'ancienne structure reste lisible et cohérente
  (le README et l'organisation des fichiers peuvent rester dans un
  état hybride un moment, ce n'est pas un problème à corriger
  immédiatement)
