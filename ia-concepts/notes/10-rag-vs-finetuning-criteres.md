# IA — RAG vs fine-tuning : critères de décision

## Rappel de base

- **RAG** = données externes récupérées à la demande, injectées dans le
  contexte au moment de la requête.
- **Fine-tuning** = ré-entraînement (partiel) qui modifie durablement les
  poids du modèle.

## Les 3 critères de décision

### Critère 1 — Fréquence de changement

RAG si l'information évolue souvent et doit rester exacte/à jour (ex :
doc interne d'infra mise à jour chaque semaine). Faire du fine-tuning
dans ce cas obligerait à ré-entraîner en permanence — lourd, coûteux, et
toujours un peu en retard sur la réalité.

### Critère 2 — Nature (contenu vs comportement)

Fine-tuning envisageable si c'est un **comportement/style/format**
systématique voulu sur n'importe quel sujet (pas juste du contenu
factuel à lister).

⚠️ Nuance importante (renforcée dans cette session) : "comportement" ne
veut **pas** dire automatiquement fine-tuning. Il y a une vraie
hiérarchie à respecter, du moins cher au plus cher :
1. **Prompt/system prompt** d'abord — suffit pour la plupart des
   styles/tons/formats simples (ex : "réponds toujours sur un ton neutre
   et rassurant").
2. **RAG** si le comportement dépend de données/exemples trop nombreux
   pour tenir dans un prompt.
3. **Fine-tuning** en dernier recours seulement — quand le prompting ne
   suffit vraiment plus (comportement trop subtil, trop de contraintes à
   faire tenir dans un prompt, besoin de fiabilité sur des milliers de
   variations que le prompting ne couvre pas fiablement).

### Critère 3 — Volume et coût

RAG/prompt tant que le contenu tient raisonnablement (quelques milliers
de tokens, ex : un glossaire d'acronymes internes) — même si ce contenu
est **permanent et ne change jamais**. Le fine-tuning n'est justifié que
quand le volume dépasse ce qui est gérable autrement (le coût
d'infrastructure et de ré-entraînement dépasse la lourdeur de
gérer/récupérer le contenu via RAG).

Piège à retenir : une connaissance figée et permanente ne justifie pas à
elle seule le fine-tuning (critère 1 seul ne suffit pas) — c'est souvent
le **critère 3** (volume trop grand pour un prompt direct) qui tranche,
même sur du contenu qui ne change jamais.

## Exercice de renforcement — scénario combiné

Base de 50 000 tickets de support historiques (figée, ne change jamais) +
besoin d'un ton "neutre et rassurant" systématique dans les réponses.

- **Retrouver des cas similaires parmi 50 000 tickets** → **RAG**, justifié
  par le critère 3 (volume), pas le critère 1 (la base ne change pourtant
  jamais — preuve que les 3 critères sont indépendants et doivent être
  vérifiés séparément, pas se fier au premier qui semble s'appliquer).
- **Ton "neutre et rassurant" systématique** → **simple system prompt**
  suffit dans l'immense majorité des cas, pas besoin de fine-tuning. Le
  fine-tuning aurait été disproportionné pour un besoin déjà bien résolu
  par le prompting.

## Résumé — ordre de décision pratique

1. Un system prompt peut-il suffire ? (comportement/ton/format simple)
2. Si le besoin dépend de données trop nombreuses pour un prompt → RAG
3. Fine-tuning seulement si ni le prompt ni le RAG ne suffisent (volume +
   comportement trop complexe/subtil pour être couvert autrement)

## À venir

- [ ] Limites et biais — hallucinations, sur-confiance, quand ne pas
      faire confiance au modèle
