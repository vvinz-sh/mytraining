# Git — Branches (create / switch / merge)

Statut : **acquis**. À voir ensuite : remotes, résolution de conflits,
rebase vs merge.

## Le concept

Une branche est un simple pointeur mobile vers un commit. `HEAD` pointe
vers la branche courante, la branche pointe vers son dernier commit.
Créer une branche est quasi instantané : ça ne copie aucun fichier, ça
crée juste une référence.

```
main:    A---B---C
                   \
feature:            D---E   (HEAD → feature)
```

## Commandes à retenir

| Commande | Effet |
|---|---|
| `git branch` | liste les branches locales |
| `git branch <nom>` | crée une branche sans basculer dessus |
| `git switch <nom>` | bascule sur une branche existante |
| `git switch -c <nom>` | crée **et** bascule en une commande |
| `git merge <nom>` | fusionne `<nom>` dans la branche courante |
| `git branch -d <nom>` | supprime une branche (refuse si non fusionnée) |
| `git branch -D <nom>` | supprime une branche même si non fusionnée (forcé) |

## Exercice réalisé (voir `git/exercices/02_branches_exercice.md`)

1. `git switch -c exercice/git-branches` depuis
   `claude/plan-de-formation-53pbfa` → branche créée + basculement en une
   commande.
2. Commit d'un fichier sur cette branche.
3. `git switch claude/plan-de-formation-53pbfa` → le fichier disparaît du
   dossier de travail et du `git log`, preuve que le commit est isolé sur
   l'autre branche.
4. `git merge exercice/git-branches` → message `Fast-forward` : comme la
   branche principale n'avait pas bougé entre-temps, Git a juste déplacé
   son pointeur, aucun commit de merge créé.
5. `git branch -d exercice/git-branches` → suppression acceptée car tous
   les commits de la branche sont déjà atteignables depuis la branche
   principale (donc rien à perdre).

## Piège à retenir

Après un `git switch -c`, les futurs commits partent sur la nouvelle
branche, pas sur celle d'où on vient — même si visuellement le dossier de
travail ne change pas forcément beaucoup. D'où l'importance de vérifier
la branche courante (`git status` ou invite du shell) avant de commiter.

## Fast-forward vs merge à 3 points (three-way)

- **Fast-forward** : la branche cible n'a pas évolué depuis la création
  de la branche de feature → le pointeur est simplement déplacé en
  avant, pas de commit de merge, historique linéaire.
- **Three-way merge** : la branche cible a évolué en parallèle (d'autres
  commits ajoutés) → Git crée un commit de merge avec deux parents pour
  réconcilier les deux historiques. Pas testé dans cette session — à
  faire dans un prochain exercice (avec un vrai conflit ou une
  divergence simple).

## À venir

- [ ] Merge à 3 points avec divergence réelle (et éventuellement un
      conflit à résoudre)
- [ ] Remotes : clone, push, pull, fetch
- [ ] Rebase vs merge
