# Logstash — Plugin exec : quand Logstash agit sur le système

Complète la note 01 (filtre `ruby`, exécution de code) — un second
plugin qui fait sortir Logstash de son rôle "transporter/transformer
des logs" pour lui donner la capacité d'**agir** sur le système.

## Ce que fait le plugin

**`input { exec {...} }`** — exécute périodiquement une commande
shell, capture toute sa sortie standard comme un event.

**`output { exec {...} }`** — exécute une commande **pour chaque
event reçu**, via `Ruby's system()` (donc la commande passe par un
shell).

## Cas d'usage réel trouvé dans la doc officielle

```
output {
  if [type] == "abuse" {
    exec { command => "iptables -A INPUT -s %{clientip} -j DROP" }
  }
}
```
Un vrai cas SIEM : bannir automatiquement une IP détectée comme
abusive, directement depuis le pipeline — Logstash devient un
**acteur**, pas seulement un observateur.

## Le vrai risque : injection de commande via les placeholders `%{name}`

Mise en garde explicite de la doc officielle : *"The contents of the
field will be included verbatim without any sanitization, i.e. any
shell metacharacters from the field values will be passed straight to
the shell."*

Si `%{clientip}` provient d'un champ extrait automatiquement (via
Grok, par exemple) et qu'un attaquant parvient à y injecter une
valeur malveillante plutôt qu'une vraie IP (ex : `1.2.3.4; commande
arbitraire`), cette commande s'exécute **telle quelle** — un vrai
risque d'injection de commande, pas hypothétique. Confirmé par un fil
de discussion communautaire nommé explicitement *"Logstash Input
Plugins remote code execution concerns"*.

## Autres points de vigilance techniques

- **Aucun timeout** : *"there is no timeout for the commands being
  run so misbehaving commands could otherwise stall the Logstash
  pipeline indefinitely"* — une commande qui bloque peut geler tout
  le pipeline (écho direct au comportement `output` bloquant déjà vu
  en note 22, pipeline-to-pipeline)
- **Coût mémoire du `fork()`** (input `exec`) : duplique l'espace
  d'adressage du process parent (Logstash + JVM) — atténué par le
  copy-on-write de l'OS, mais peut provoquer des erreurs
  `ENOMEM: Cannot allocate memory` si la mémoire physique
  hors-JVM-heap est insuffisante

## Rareté en pratique : un vrai signal, pas juste une intuition

Recherche menée pour vérifier si ce plugin est réellement utilisé en
production, au-delà des exemples de doc :

- **Le plugin n'est plus bundlé par défaut** dans Logstash — installation
  explicite requise (`bin/logstash-plugin install logstash-output-exec`),
  contrairement à `grok`/`mutate`/`elasticsearch` inclus d'office. Un
  signal qu'Elastic lui-même ne le traite pas comme un plugin du
  quotidien.
- **Très peu de retours d'usage réels trouvés** — un cas niche
  (transformation CSV puis script de post-traitement), et l'exemple
  `iptables` qui revient **identique** dans presque toutes les
  versions de la doc depuis des années, suggérant un exemple
  pédagogique plus qu'un pattern massivement déployé.

**Conclusion** : en vrai contexte de sécurité/SIEM, la pratique
courante privilégie un **outil dédié** (plateforme SOAR, `fail2ban`,
un gestionnaire de pare-feu à part entière) plutôt que d'exécuter des
commandes système directement depuis le pipeline de logs — séparation
des responsabilités, meilleure traçabilité, mode d'échec plus sûr
qu'un pipeline qui se met à exécuter du shell.

## Résumé

1. `exec` (input/output) fait sortir Logstash de son rôle
   d'observateur pour lui donner une capacité d'action réelle sur le
   système
2. Le vrai risque n'est pas l'exemple `iptables` en lui-même, mais
   l'injection de commande via des champs non sanitizés
   (`%{clientip}` pouvant contenir des métacaractères shell)
3. Absence de timeout et coût mémoire du `fork()` sont deux points
   techniques supplémentaires à connaître avant usage
4. Plugin non bundlé par défaut + peu de retours d'usage réels =
   signal cohérent que la pratique courante préfère des outils dédiés
   plutôt que `exec` directement dans le pipeline

## Lien avec les notes existantes

`01-panorama-alternatives-interfacage-securite.md` (filtre `ruby`,
même famille de risque d'exécution de code), `22-pipeline-to-pipeline.md`
(comportement bloquant d'un `output`, même préoccupation ici sans
timeout).

## Sources

- [Exec output plugin (Elastic Docs)](https://www.elastic.co/guide/en/logstash/current/plugins-outputs-exec.html)
- [Exec input plugin (Elastic Docs)](https://www.elastic.co/guide/en/logstash/8.19/plugins-inputs-exec.html)
- [Logstash Input Plugins remote code execution concerns (Elastic Discuss)](https://discuss.elastic.co/t/logstash-input-plugins-remote-code-execution-code-execution-concerns/166143)
- [Exec output plugin — community example (Elastic Discuss)](https://discuss.elastic.co/t/exec-output-plugin/348869)
