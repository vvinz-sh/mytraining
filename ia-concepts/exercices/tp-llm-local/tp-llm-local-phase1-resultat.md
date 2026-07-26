# TP — LLM local, Phase 1 (inférence Ollama) : réalisée ✅

Complète `tp-llm-local-ollama-qlora-draft.md`, Phase 1 uniquement.
Modèle testé : `llama3.1:8b` (Llama 3.3 n'existe qu'en 70B — pas de
version 8B pour cette génération, correction faite en cours de route).

## Installation et validation GPU

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Vérification dans les logs du service (`journalctl -u ollama -f` ou
équivalent) :
- `library=CUDA compute=8.6 name=CUDA0 description="NVIDIA GeForce
  RTX 3070"` — détection GPU confirmée, pas de fallback CPU
- `vram-based default context` : `total_vram="8.0 GiB"
  default_num_ctx=4096` — Ollama ajuste seul le contexte par défaut
  selon la VRAM disponible

```bash
ollama pull llama3.1:8b
ollama run llama3.1:8b
```

En parallèle, dans un second terminal :

```bash
watch -n 1 nvidia-smi
```

VRAM observée au chargement : ~6.2/8 Go (poids du modèle ~4.9 Go +
KV cache pour le contexte). `Volatile GPU-Util` monté en flèche
pendant la génération — vitesse ressentie très rapide, cohérente avec
les ~40 tokens/seconde attendus pour un 7-8B en Q4_K_M sur RTX 3070.

## Test de la limite de contexte (4096 tokens)

**Méthode** : marqueur test ("mon chat s'appelle Carapuce") placé en
tout début d'un texte de remplissage, question posée à la fin du même
prompt, envoyé en une seule commande via pipe/redirection stdin.

**Premier essai (raté, mais informatif)** — texte de remplissage
composé d'une phrase répétée ~400 fois, contenant du vocabulaire sur
le "dépassement de limite" :

```bash
for i in $(seq 1 400); do echo "Ceci est la ligne numero $i du test de contexte, elle sert uniquement a remplir de l'espace pour depasser la limite de 4096 tokens et observer le comportement d'Ollama face a un depassement de contexte."; done > /tmp/texte_long.txt
echo "Quel est le nom de mon chat ?" >> /tmp/texte_long.txt
ollama run llama3.1:8b < /tmp/texte_long.txt
```

→ Le modèle a **refusé de répondre**, interprétant le pattern comme
une tentative de manipulation. Ce n'est **pas** du prompt overriding
(aucune instruction cachée ne détournait son comportement) — c'est un
réflexe de sécurité appris à l'entraînement (alignement), déclenché à
l'inférence sans intention malveillante réelle.

**Deuxième essai (texte cohérent, 50 paragraphes, ~3400 mots)** :

```bash
{
  echo "Le nom de mon chat est Carapuce."
  for i in $(seq 1 50); do
    echo "Paragraphe $i : Aujourd'hui il fait beau à Albi. Je suis allé me promener au bord du Tarn en fin d'après-midi, le soleil se couchait doucement sur les toits de brique rose de la ville. J'ai croisé plusieurs personnes qui promenaient leur chien le long de la rivière, et quelques pêcheurs installés sur la berge. La météo était clémente cette semaine, avec des températures agréables pour la saison."
  done
  echo "Quel est le nom de mon chat ?"
} > /tmp/texte_long2.txt

wc -w /tmp/texte_long2.txt   # 3415 mots
ollama run llama3.1:8b < /tmp/texte_long2.txt
```

→ Le marqueur "Carapuce" n'a **pas** été retrouvé — le modèle a
répondu qu'il ne le trouvait pas dans le texte.

**Troisième essai (10 paragraphes, texte identique réduit)** :

```bash
{
  echo "Le nom de mon chat est Carapuce."
  for i in $(seq 1 10); do
    echo "Paragraphe $i : Aujourd'hui il fait beau à Albi. Je suis allé me promener au bord du Tarn en fin d'après-midi, le soleil se couchait doucement sur les toits de brique rose de la ville. J'ai croisé plusieurs personnes qui promenaient leur chien le long de la rivière, et quelques pêcheurs installés sur la berge. La météo était clémente cette semaine, avec des températures agréables pour la saison."
  done
  echo "Quel est le nom de mon chat ?"
} > /tmp/texte_court.txt
ollama run llama3.1:8b < /tmp/texte_court.txt
```

→ Le marqueur a été retrouvé correctement, avec en bonus une remarque
spontanée du modèle sur le caractère répétitif du texte.

**Conclusion** : le deuxième essai confirme une vraie **troncature
silencieuse** liée au dépassement de `num_ctx` (probablement en
tronquant le début, cohérent avec la question de fin de texte restée
traitée). Le troisième essai écarte l'hypothèse alternative
("lost in the middle" — info présente mais mal exploitée sur un texte
trop long), puisque le même contenu, en dessous de la limite,
fonctionne. Ollama ne remonte **aucune erreur explicite** en cas de
dépassement — juste une perte d'info silencieuse.

## Test sur contenu réel (syslog)

```bash
{ tail -n 200 /var/log/syslog; echo "Peux-tu résumer ce qui se passe dans ces logs et signaler si tu vois quelque chose d'anormal ?"; } | ollama run llama3.1:8b
```

Résultat :
- Extraction de faits précis et exacts (durée d'inférence, tokens
  générés, taille de cache) — pas d'hallucination visible sur ces
  chiffres
- Identification correcte d'une vraie anomalie : `wsl-pro-service`
  échouant à se connecter à l'agent Windows (fichier `.address`
  manquant), en boucle de reconnexion toutes les 60 secondes
- Découverte confirmée après coup par recherche externe : problème
  connu et documenté (intégration Ubuntu Pro for WSL, non configurée,
  inoffensif) — décision prise de laisser tel quel plutôt que de
  désactiver le service (commande identifiée si besoin plus tard :
  `sudo systemctl disable --now wsl-pro-service`)

## Ce que ça a démontré concrètement

- Détection GPU et calcul du contexte par défaut : automatique et
  fiable, mais nécessite quand même une vérification active dans les
  logs (pas juste supposer que ça marche)
- Un modèle 8B en Q4_K_M reste utilisable pour du résumé/diagnostic
  sur du contenu technique réel (syslog), avec une précision correcte
  sur les faits chiffrés
- Distinction pratique confirmée entre refus d'alignement (réflexe
  appris, sans instruction externe) et prompt overriding (instruction
  cachée cherchant à détourner le comportement) — les deux peuvent
  sembler similaires en surface ("le modèle ne fait pas ce qu'on
  attend"), mais n'ont ni la même cause ni la même portée
- Dépassement de contexte = troncature silencieuse, pas d'erreur
  explicite — point de vigilance à garder pour la Phase 2 (QLoRA),
  où la longueur des séquences d'entraînement devra être calibrée en
  conséquence

## Compétences pratiquées

- Diagnostic GPU vs CPU à partir de logs applicatifs, pas juste
  `nvidia-smi` isolé
- Conception d'un protocole de test isolant une seule variable à la
  fois (marqueur fixe, longueur variable) pour trancher entre deux
  hypothèses concurrentes
- Distinction conceptuelle appliquée en conditions réelles (alignement
  vs prompt injection)
- Usage d'un LLM local sur une tâche sysadmin concrète (analyse de log
  système), avec esprit critique sur la fiabilité du diagnostic proposé

## Prochaine étape

Phase 2 — fine-tuning QLoRA avec Unsloth sur `qwen3:8b`, dataset
"log brut → résumé structuré" prolongeant le TP Ansible+API.
