# Logstash — Ressources externes recommandées

Suivi des ressources externes conseillées en complément des notes
prises ici, à mesure que le module Logstash avance.

## Documentation officielle

- **Elastic — Logstash Reference (8.19)** — référence officielle,
  version alignée sur celle installée en lab.
  [https://www.elastic.co/guide/en/logstash/8.19/index.html](https://www.elastic.co/guide/en/logstash/8.19/index.html)
  - [ ] Pas encore consultée en détail

- **endoflife.date/logstash** — suivi des dates de support par
  version, utile pour vérifier la pertinence d'une version dans le
  temps sans devoir rechercher à chaque fois.
  [https://endoflife.date/logstash](https://endoflife.date/logstash)
  - [x] Consultée pour choisir la ligne 8.19 (support jusqu'à juillet 2027)

## Sécurité

- **ESA-2026-29** — avis de sécurité Elastic (avril 2026), traversée de
  chemin dans l'extraction d'archives menant à une écriture de fichier
  arbitraire.
  [https://discuss.elastic.co/t/logstash-8-19-14-9-2-8-9-3-3-security-update-esa-2026-29/385816](https://discuss.elastic.co/t/logstash-8-19-14-9-2-8-9-3-3-security-update-esa-2026-29/385816)
  - [x] Consultée pour le panorama sécurité du Palier 0

- **NXLog — Logstash alternatives et concurrents pour la sécurité
  (2026)** — comparatif orienté SIEM/SOC, utile pour situer Logstash
  face à Vector/Fluent Bit/NXLog dans un contexte sécurité.
  [https://nxlog.co/news-and-blog/posts/logstash-alternatives-and-competitors](https://nxlog.co/news-and-blog/posts/logstash-alternatives-and-competitors)
  - [x] Consultée pour le panorama comparatif du Palier 0

## Comparatifs d'écosystème

- **Better Stack — Fluentd vs Logstash (2026)** — comparatif détaillé
  ressources/performance/écosystème de plugins.
  [https://betterstack.com/community/comparisons/fluentd-vs-logstash/](https://betterstack.com/community/comparisons/fluentd-vs-logstash/)
  - [x] Consultée pour le panorama du Palier 0

## Pourquoi ces ressources plutôt que d'autres

Contrairement au module IA (où la vidéo/l'animation aidait sur des
concepts visuels type attention/couches), Logstash est un outil de
configuration et d'opération — la documentation officielle et des
comparatifs à jour priment sur le contenu pédagogique type vidéo. À
réévaluer si un sujet dense (Grok, tuning JVM) s'avère difficile en
texte seul.
