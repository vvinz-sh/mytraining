# IA — Vague 3 (MLOps/Ops) : Gouvernance & conformité — RGPD appliqué à une app LLM

Session théorique partie du TP RAG/MCP réel comme point de départ
concret.

## Sous-traitance dès qu'une donnée transite

Une donnée personnelle (nom, email d'un collègue) présente dans une note
indexée : tant qu'elle reste uniquement dans la base Chroma locale,
seul l'opérateur du repo la traite. Dès qu'elle part vers l'API Claude
(même sans jamais être stockée durablement côté Anthropic), un
**tiers** entre dans la chaîne de traitement — Anthropic devient
**sous-traitant** au sens RGPD.

Point important : le RGPD définit le "traitement" très largement —
**toute opération** sur une donnée personnelle compte (collecte,
consultation, transmission, structuration...), pas seulement le
stockage durable. Un simple passage dans une requête API, même jamais
conservé après, constitue déjà un traitement.

## Détection automatique de données personnelles — au-delà du NER

Rappel du guardrail par pattern déjà vu (`securite/25-...md`) : un email
a un format structuré et prévisible (`@`, domaine) → une regex
fonctionne bien, quasi garantie. Un nom propre n'a **aucun format
distinctif** — impossible à repérer par une règle de syntaxe.

**NER (Named Entity Recognition)** : modèle spécialisé capable de
repérer "ceci est probablement un nom de personne" à partir du contexte
grammatical, pas d'un format fixe. Mais même limite structurelle que
les guardrails sémantiques déjà vus : des mots comme "Charles", "Rose",
"Justine" sont à la fois des prénoms **et** des mots communs (couleur,
fleur, adjectif) — un détecteur NER peut se tromper dans les deux sens
(rater un vrai nom, signaler à tort un mot courant). Aucune garantie à
100%, juste un signal statistique plus ou moins fiable — même famille
de compromis que l'ANN (`rag-embeddings/30-...md`).

## Le DPA d'Anthropic — ce qu'il couvre, et surtout ce qu'il ne couvre pas

### Quel accès change tout

Le DPA (Data Processing Agreement) d'Anthropic est inclus dans les
**Commercial Terms** (Claude for Work, API commerciale, Claude
Enterprise) — les offres **Free, Pro, Max** (Consumer Terms) n'incluent
**pas** de DPA. Une application backend en production doit donc
utiliser l'accès commercial, pas un simple abonnement personnel, pour
bénéficier de ce cadre contractuel.

Dans le cadre commercial : le client reste **responsable de
traitement**, Anthropic devient **sous-traitant**, et les données ne
sont pas utilisées pour l'entraînement des modèles dans ce contexte.

### Ce que le DPA couvre déjà

- Clauses contractuelles types (SCC) automatiquement incluses pour les
  transferts internationaux
- Options de résidence des données en Europe pour les clients entreprise
- Engagement à ne traiter les données que selon les instructions du
  client, jamais les "vendre" ni les "partager"
- **Zero Data Retention (ZDR)** : option empêchant Anthropic de
  stocker les prompts ou réponses générées — pertinent pour minimiser
  le risque même en cas de fuite accidentelle d'une donnée personnelle
- Préavis de 15 jours avant tout nouveau sous-traitant ultérieur,
  permettant au client de s'y opposer

### ⚠️ Ce qui reste la responsabilité du développeur/déployeur

Le DPA d'Anthropic ne rend **jamais automatiquement conforme** —
l'organisation doit quand même :
- Réaliser sa propre évaluation du fournisseur (vendor assessment)
- Documenter la **base légale du traitement** (Article 6 RGPD :
  consentement, intérêt légitime...)
- Respecter les principes de l'Article 5 RGPD, indépendamment du
  DPA ou du ZDR :
  - **Limitation de la finalité** : une donnée collectée pour un usage
    précis (ex : obtenir une réponse médicale) ne doit pas être
    réutilisée pour un usage incompatible (ex : sécurité/anti-abus)
    sans base légale propre
  - **Limitation de la conservation** : une donnée ne doit être
    conservée que le temps nécessaire à la finalité d'origine — le
    ZDR répond à ce principe côté fournisseur, mais ne dispense pas
    de vérifier l'alignement finalité/conservation en amont
- Réaliser une **analyse d'impact (DPIA)** si le traitement présente un
  risque élevé
- **Informer les personnes concernées** — les collègues dont les notes
  pourraient contenir leurs données savent-ils qu'elles peuvent
  transiter par une API tierce ?
- Vérifier les sous-traitants ultérieurs d'Anthropic

## Cas particulier — usage à haut risque (AI Act)

Pour un usage à haut risque (exemple type : santé), obligations
supplémentaires pour le déployeur : gestion des risques, supervision
humaine sur les décisions critiques, évaluation de conformité,
documentation et traçabilité du fonctionnement. Pour un TP interne
comme le RAG/MCP (pas de décision automatisée impactante), le risque
est faible — mais le principe général reste : plus l'usage est
sensible, plus les obligations grimpent.

## Résumé pratique — checklist pour une app LLM en prod

1. Utiliser l'API sous conditions **commerciales** (pas un abonnement
   perso) pour bénéficier du DPA
2. Envisager le **Zero Data Retention** pour une garantie
   supplémentaire
3. Ne jamais compter sur le DPA seul — documenter sa propre base légale
   et informer les personnes concernées reste la responsabilité du
   développeur/déployeur
4. Les guardrails (regex, NER, sémantique) restent une bonne pratique
   de **minimisation** des données, mais ne remplacent jamais les
   obligations contractuelles et documentaires

## Ressource externe

- [RGPD — Chapitre II : Principes](https://www.cnil.fr/fr/reglement-europeen-protection-donnees/chapitre2) (CNIL) - articles 5 à 11, dont la limitation de finalité et de conservation

## À venir (gouvernance)

- [ ] AI Act européen — grandes lignes, catégories de risque (au-delà
      du cas "haut risque" effleuré ici)
- [ ] Documentation type "model card" / "system card"
- [ ] Audit trail — tracer qui a demandé quoi, quelle version de modèle
      a répondu
- [ ] Biais et équité (fairness) — angle gouvernance, pas ML pur
