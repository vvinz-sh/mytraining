# IA — AI Act : les 4 niveaux de risque et l'obligation de transparence

Complète la note 36 (RGPD) — un cadre légal **distinct**, pas une
extension du RGPD. Le RGPD protège la donnée personnelle ; l'AI Act
classe et encadre le système d'IA lui-même selon son **usage et son
impact potentiel**, indépendamment de si la donnée manipulée est
sensible ou non.

## La pyramide à 4 niveaux

1. **Risque inacceptable** (Article 5) — interdit purement et
   simplement
2. **Haut risque** (Article 6, Annexe III) — autorisé sous obligations
   lourdes (gestion des risques, supervision humaine, documentation)
3. **Risque limité** (Article 50) — autorisé sous obligation de
   **transparence**
4. **Risque minimal** — aucune obligation spécifique (la grande
   majorité des usages IA : filtres anti-spam, IA dans un jeu vidéo...)

## Niveau 1 — Pratiques interdites (Article 5)

Couvre les usages qui manipulent les décisions des personnes,
exploitent leurs vulnérabilités, notent/classent socialement les
individus, prédisent le risque qu'une personne commette un crime sur
la seule base du profilage, créent des bases de reconnaissance faciale
par extraction non ciblée d'images (internet/vidéosurveillance),
déduisent des émotions au travail/en établissement scolaire, ou
classent des personnes selon leurs données biométriques pour en
déduire origine, opinions politiques, religion, orientation sexuelle.

**Exceptions** (uniquement pour l'identification biométrique à distance
"en temps réel" dans l'espace public, à des fins répressives) : recherche
de personnes disparues/victimes, prévention d'une menace terroriste
imminente, recherche d'un suspect pour un crime grave (peine ≥ 4 ans).
Ces exceptions ne sont pas vagues dans l'intention (usage précis et
étroit visé) mais encadrées par une procédure lourde : autorisation
judiciaire préalable, limites temporelles/géographiques strictes,
notification obligatoire, rapports annuels publics, et surtout —
**aucune décision défavorable ne peut être prise sur la seule base des
résultats du système**.

**Pourquoi "la mise sur le marché" est répété à chaque point** : ce
n'est pas de la lourdeur stylistique — l'AI Act vise 3 moments distincts
du cycle de vie, avec une responsabilité différente à chacun : mise sur
le marché (le fournisseur qui vend/distribue), mise en service (le
déploiement effectif), utilisation (l'usage courant). Cette répétition
permet de couvrir toute la chaîne (fabricant, déployeur, utilisateur)
sous la même interdiction.

## Niveau 2 — Haut risque (Article 6, Annexe III)

Un système est haut risque s'il est composant de sécurité d'un produit
couvert par la législation d'harmonisation de l'Union (Annexe I), ou
s'il relève d'un des usages listés à l'Annexe III (santé, RH/recrutement,
justice, éducation, etc.). Marge d'appréciation : un système listé à
l'Annexe III peut échapper à la classification s'il exécute une tâche
procédurale limitée, améliore juste le résultat d'une activité humaine
déjà réalisée, ou ne remplace pas une évaluation humaine préexistante
sans contrôle approprié — mais le fournisseur qui s'auto-exempte doit
documenter cette évaluation. Un système de **profilage de personnes
physiques** reste toujours classé haut risque, sans exception possible.

## Niveau 3 — Risque limité, obligation de transparence (Article 50)

**Entrée en application : 2 août 2026** (marquage machine-readable :
délai de grâce jusqu'au 2 décembre 2026 pour les systèmes déjà
commercialisés avant cette date — l'information des utilisateurs et
l'étiquetage visible, eux, sont dus dès le 2 août, sans report).

S'applique à **tous** les systèmes d'IA générative, pas seulement aux
systèmes à haut risque — aucun seuil de taille d'entreprise, aucune
classification de risque n'exempte. Quatre situations couvertes :

1. **Systèmes qui interagissent avec des personnes** (chatbots,
   assistants vocaux) — informer clairement dès le début de
   l'interaction, sauf si évident au point que la précision serait
   absurde
2. **Systèmes qui génèrent/manipulent du contenu** (texte, image,
   audio, vidéo) — marquage lisible par machine (watermarking,
   métadonnées C2PA/IPTC côté fournisseur) + étiquetage visible côté
   déployeur (icône "IA" à un emplacement fixe)
3. **Reconnaissance d'émotions / catégorisation biométrique** —
   informer les personnes exposées du fonctionnement du système
4. **Deepfakes et textes d'intérêt public générés** — signaler
   explicitement le caractère artificiel du contenu

**Exceptions** :
- Texte généré par IA exonéré si revue humaine/éditoriale par une
  personne compétente (pas un simple correcteur orthographique)
- Œuvre évidemment artistique, créative, satirique ou fictive :
  divulgation minimale et non intrusive suffit
- Un chatbot de support client ou un avatar humain réaliste **ne
  bénéficie jamais** de l'exception artistique — il faut toujours
  afficher
- **Usage purement personnel** — mais exemption étroite : un deepfake
  d'un élu posté sur les réseaux sociaux pour critiquer une décision
  n'est **pas** couvert, l'impact sur le débat public retire le
  caractère "purement personnel", même produit par un individu isolé

**Qui est concerné** : entreprises et indépendants logés à la même
enseigne (aucune exemption de taille). Les **utilisateurs finaux
ordinaires** ne sont pas soumis à l'obligation — ils en sont les
bénéficiaires protégés. Un particulier peut cependant basculer côté
"déployeur" dès qu'il génère/diffuse lui-même du contenu IA avec un
minimum d'impact public.

**Sanctions** : jusqu'à 15 millions d'euros ou 3% du chiffre d'affaires
mondial annuel — du même ordre que les sanctions RGPD les plus lourdes.

## Niveau 4 — Risque minimal

Pas d'obligation spécifique — la majorité des systèmes d'IA (filtres
anti-spam, IA de jeu vidéo, recommandations basiques) relèvent de ce
niveau par défaut, en l'absence de classification supérieure.

## Résumé pratique — checklist

1. Le système relève-t-il d'une pratique interdite (Article 5) ? Si
   oui, stop — aucune mise en conformité possible
2. Le système est-il listé à l'Annexe III ou composant de sécurité
   d'un produit réglementé ? → Haut risque, obligations lourdes
3. Le système génère du contenu, interagit avec des personnes, ou fait
   de la reconnaissance d'émotions/biométrie ? → Risque limité,
   obligation de transparence (Article 50) dès le 2 août 2026
4. Sinon → risque minimal, pas d'obligation spécifique

Identifier son **rôle** (fournisseur vs déployeur) pour chaque système
avant de déterminer l'obligation précise — l'AI Act attribue des
responsabilités différentes selon le rôle, pas seulement selon le
niveau de risque.

## Ressources externes:
- [IAACT EU](https://artificialintelligenceact.eu/fr/ai-act-explorer/)

## À venir (gouvernance)

- [ ] Documentation type "model card" / "system card"
- [ ] Audit trail — tracer qui a demandé quoi, quelle version de modèle
      a répondu
- [ ] Biais et équité (fairness) — angle gouvernance, pas ML pur
