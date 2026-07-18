# Domaine 1 — Comprendre et utiliser les outils essentiels

Statut : **acquis**, quelques points annexes à revoir (voir en bas).

## Exercice fait — filtrage de logs + archivage + lien

Scénario : filtrer `ERROR` sans `ERROR_IGNORED` dans un log, rediriger vers un
nouveau fichier, archiver l'original avec la date du jour, créer un lien
symbolique vers le fichier filtré.

```bash
grep 'ERROR' /var/log/appli.log | grep -v 'ERROR_IGNORED' > appli_errors.log
tar czf "appli-log-$(date +%Y-%m-%d).tgz" /var/log/appli.log
ln -s "$(pwd)/appli_errors.log" dernier_rapport
```

Points à retenir :
- Éviter `cat fichier | grep` (Useless Use of Cat) → `grep motif fichier` directement.
- Un lien symbolique relatif dépend du dossier courant au moment de la
  résolution ; préférer un chemin absolu si l'emplacement final du lien
  n'est pas garanti.

## Lien dur vs lien symbolique

- **Lien dur** : pointe directement sur le numéro d'**inode**. Ne peut pas
  traverser un système de fichiers différent (les inodes sont numérotés par
  filesystem, donc ambigus d'une partition à l'autre). Ne peut pas non plus
  pointer vers un répertoire (risque de boucle dans l'arborescence).
- **Lien symbolique** : stocke un chemin texte vers la cible. Traverse les
  systèmes de fichiers sans problème, peut pointer vers un répertoire, mais
  devient "cassé" si la cible est déplacée ou supprimée.

## À revoir (non testé en session)

- [ ] Permissions ugo en notation octale (`chmod 750`, etc.)
- [ ] `su -` vs `sudo -i` vs `sudo -u` (différences d'environnement chargé)
- [ ] ACL (`setfacl` / `getfacl`) — recoupe aussi le Domaine 9 (sécurité)
