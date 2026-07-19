# Git — Purger un fichier de tout l'historique (`git filter-repo`)

Module "hors-série", né d'un cas réel : un `vault.yml` (chiffré, donc
risque faible) commité/pushé par erreur.

## Les deux niveaux de "suppression"

- **Niveau 1 — Arrêter de suivre à partir de maintenant** : un simple
  `git rm --cached` + entrée `.gitignore`. Le fichier reste visible dans
  les anciens commits, mais n'apparaît plus dans les prochains.
- **Niveau 2 — Purger de tout l'historique** : réécrit **tous** les
  commits contenant le fichier (nouveaux hash), nécessite un
  `push --force`. Plus radical, utile si on veut qu'aucune trace ne
  subsiste, même dans l'historique.

## Outil : `git filter-repo` (pas `filter-branch`)

`git filter-branch` (l'ancien outil intégré à Git) est officiellement
déconseillé par Git lui-même — trop lent, trop piégeux. L'outil recommandé
aujourd'hui est **`git filter-repo`**, à installer séparément :

```bash
pip install git-filter-repo
```

## Repérer les commits concernés

```bash
git log --all --oneline -- chemin/vers/le/fichier
```

## Purger le fichier

```bash
git filter-repo --path chemin/vers/le/fichier --invert-paths --force
```

- `--path` cible le fichier concerné.
- `--invert-paths` inverse la logique : "garde tout **sauf** ce chemin"
  (sans cette option, `--path` ferait l'inverse — ne garder **que** ce
  fichier, supprimant tout le reste).
- `--force` nécessaire si le repo n'est pas un clone fraîchement cloné
  (mesure de sécurité par défaut de l'outil).

⚠️ Effet de bord automatique : `filter-repo` **supprime le remote
`origin`** après la réécriture, par sécurité (pour éviter un push
accidentel sur l'ancien historique sans réfléchir). Il faut le rajouter
après coup :

```bash
git remote add origin <url-du-remote>
```

Bien vérifier la forme de l'URL (HTTPS vs SSH) — l'outil affiche l'ancienne
URL supprimée dans son message, à réutiliser telle quelle.

## Vérifier que la purge a fonctionné

```bash
git log --all --oneline -- chemin/vers/le/fichier
```
Doit renvoyer **rien du tout**.

## Pousser l'historique réécrit

Les hash de tous les commits après le fichier purgé ont changé — un push
normal serait refusé (historique "divergent"). Il faut forcer :

```bash
git push origin main --force
```

⚠️ `--force` écrase l'historique distant sans négociation — dangereux sur
un repo partagé où d'autres auraient pu pousser entre-temps (perte de
leur travail sans prévenir). Sur un repo perso solo, sans risque.

Variante plus prudente à connaître pour un contexte en équipe :
`git push origin main --force-with-lease` — vérifie que personne d'autre
n'a poussé depuis le dernier `fetch` avant d'écraser.

## Piège rencontré — `.gitignore` basé sur un chemin fragile

Une entrée `.gitignore` contenant un `/` (autre qu'en fin de ligne) est
relative à l'emplacement du `.gitignore` — si le fichier est déplacé
(`mv`), le pattern ne matche plus et le fichier redevient trackable par
erreur au prochain commit.

**Solution** : un pattern **sans `/`** matche le nom de fichier n'importe
où dans l'arborescence, indépendamment du chemin :
```
vault.yml
```
ou, plus explicite à la lecture :
```
**/vault.yml
```

Point important : `.gitignore` ne s'applique qu'aux fichiers **non
encore trackés**. Un fichier déjà suivi avant l'ajout de la règle continue
d'être suivi même après — il faut un `git rm --cached` en plus si le
fichier était déjà tracké.

## Rappel de l'incident réel (deux vagues de purge)

1. Premier `vault.yml` purgé avec succès à son chemin d'origine.
2. Un `.gitignore` basé sur ce chemin précis (pas encore corrigé en
   pattern générique) n'a plus matché après un déplacement du fichier
   (`mv`) — le vault a été re-commité/pushé par erreur à son nouveau
   chemin.
3. Deuxième purge avec `filter-repo` sur le nouveau chemin, vérifiée sur
   un clone frais depuis GitHub pour confirmer l'absence totale de trace.
4. `.gitignore` finalement corrigé en pattern générique (`**/vault.yml`)
   pour éviter que l'incident se reproduise après un futur déplacement.
