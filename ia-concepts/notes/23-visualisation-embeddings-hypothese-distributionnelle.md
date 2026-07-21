# IA — Visualisation des embeddings : arithmétique vectorielle et hypothèse distributionnelle

Suite pratique à la vidéo 3Blue1Brown — la visualisation des vecteurs de
mots dans l'espace rend tangible ce qu'on avait vu en théorie sur les
embeddings (analogie GPS/coordonnées).

## Arithmétique vectorielle sur les mots

Exemple classique : **roi - homme + femme ≈ reine**. Prendre le vecteur
de "roi", soustraire celui de "homme", ajouter celui de "femme" — le
résultat de ce calcul se rapproche du vecteur de "reine". Littéralement
de l'arithmétique sur des mots, qui fonctionne parce que la direction
géométrique "masculin → féminin" est à peu près la même dans l'espace,
peu importe le mot de départ.

## Pourquoi cette relation émerge sans qu'on la programme — l'hypothèse distributionnelle

Le modèle n'a **aucune notion explicite** de "genre grammatical" — jamais
de règle du type "roi est masculin, reine est féminin" ne lui a été
donnée. La structure géométrique cohérente émerge du principe de
**l'hypothèse distributionnelle** : des mots utilisés dans des contextes
similaires ont des sens similaires.

Concrètement : le modèle a vu des milliards de phrases où "roi" apparaît
dans des contextes proches de ceux où apparaît "homme" (avec des
variations autour de la royauté), et "reine" apparaît dans des contextes
proches de ceux de "femme", avec le **même type de variation** que celle
observée entre "roi" et "homme". Cette variation contextuelle, répétée de
façon cohérente à travers des milliers de paires similaires
("acteur/actrice", "prince/princesse"...), se traduit en une direction
géométrique stable dans l'espace des vecteurs — pas parce qu'on lui a dit
"ça, c'est le genre", mais parce que le motif contextuel était
statistiquement présent et cohérent dans les données.

### Lien avec le principe ML de base

Belle illustration du principe vu depuis le début (poids ajustés à
partir de données, pas de règles écrites à la main) : le modèle **déduit**
une structure purement à partir de motifs statistiques dans le texte, et
cette structure déduite **coïncide** avec une catégorie que les humains
connaissent intuitivement (le genre grammatical), sans que personne ne
l'ait jamais programmée explicitement.

## ⚠️ Point de vigilance — le revers de cette propriété : les biais

Cette même propriété géométrique a un revers bien documenté : si les
données d'entraînement contiennent des biais sociétaux (ex :
"infirmière" statistiquement plus proche de "femme" et "docteur" plus
proche de "homme" dans le texte d'origine), le modèle **apprend et
reproduit ces associations** de la même manière géométrique — sans
distinguer une corrélation statistique neutre (roi/reine) d'un biais
sociétal problématique (métier/genre).

Écho direct avec le **biais de dataset** vu avec le chat blanc/noir —
sauf qu'ici, le "biais" vient du texte produit par des humains (reflétant
des biais sociétaux réels dans le corpus d'entraînement), pas d'un
simple manque de diversité d'images.

## Résumé

- Les relations sémantiques entre mots se traduisent en relations
  géométriques (distance, direction) dans l'espace des embeddings.
- Ces relations émergent uniquement de motifs statistiques dans les
  données (hypothèse distributionnelle), sans règle explicite.
- Cette propriété a un revers : elle capture aussi les biais sociétaux
  présents dans les données d'entraînement, de la même façon qu'elle
  capture des relations "neutres" comme le genre grammatical.
