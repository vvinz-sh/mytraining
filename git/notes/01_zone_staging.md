# Git — Les trois zones (commit / index / working directory)

Statut : **acquis** pour le concept de staging. À voir ensuite : branches,
remotes, résolution de conflits, rebase.

## Le schéma à trois états

```
dernier commit  →  git diff --staged  →  index (staging)  →  git diff  →  dossier de travail
```

- **`git add`** ne signifie pas juste "commencer à tracker un fichier" — à
  chaque modification, même sur un fichier déjà suivi, il faut re-`add` pour
  faire entrer *ces* changements précis dans l'index.
- **`git commit`** ne prend que ce qui est dans l'index à l'instant T, pas
  l'état courant du fichier sur disque.
- **`git diff`** compare le dossier de travail à l'index (pas au dernier
  commit).
- **`git diff --staged`** compare l'index au dernier commit.

## Piège classique à retenir

Scénario : je modifie `config.yml` une 1ère fois, je fais `git add
config.yml`, puis je modifie `config.yml` une 2ème fois sans re-`add`.

- Si je fais `git commit` maintenant → seule la **1ère modification** part
  dans le commit (celle qui était indexée).
- La 2ème modification reste dans le dossier de travail, non indexée. Elle
  attend un nouveau `git add` + commit — ou risque d'être perdue avec un
  `git checkout -- config.yml` fait par erreur.

## Commandes à retenir de cette session

- `git status` — état des fichiers (modifiés / stagés / non suivis)
- `git diff` — diff dossier de travail ↔ index
- `git diff --staged` — diff index ↔ dernier commit
- `git add <fichier>` — staging sélectif (permet de commiter uniquement
  certains fichiers/modifs, même en travaillant sur plusieurs choses en
  parallèle)

## À venir

- [ ] Branches : create, switch, merge
- [ ] Remotes : clone, push, pull, fetch
- [ ] Résolution de conflits
- [ ] Rebase vs merge
