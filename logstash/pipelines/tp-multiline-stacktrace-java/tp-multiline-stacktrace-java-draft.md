# TP — Recoller une stack trace Java multiligne (mini-draft)

Statut : **amorce seulement, pas encore designé en détail**. Palier 3
(renforcement, multiligne, intégration) — complète le TP `multiline`
déjà fait sur la sortie `ansible-playbook -v` (notes 25/26), cette
fois sur un cas plus classique/représentatif.

## Matériel déjà disponible, à réutiliser plutôt qu'à fabriquer

De vraies stack traces Java multilignes, avec plusieurs niveaux
`Caused by:` imbriqués, déjà capturées pendant les tests de
certificat expiré du TP `tp-filebeat-rh8103` (Étape 6, point 1,
phase 4) :
- `test2-cer-srv-rocky.log` / `rocky_certclientexpired.log` — chaîne
  complète `DecoderException` → `SSLHandshakeException` →
  `CertPathValidatorException` → `CertificateExpiredException`

Pas besoin de générer un exemple artificiel — ce matériel est réel,
déjà produit par le lab lui-même, et suffisamment riche (plusieurs
niveaux d'imbrication `Caused by:`) pour un cas d'école solide.

## À designer plus tard

- Pattern de déclenchement `multiline` adapté à une stack trace Java
  (typiquement : une ligne qui ne commence *pas* par un timestamp
  rejoint la précédente — logique inverse de celle utilisée sur le
  cas ansible, où l'en-tête déclenchait un nouveau départ)
- Est-ce que `codec` suffit, ou une comparaison avec le filtre
  `multiline` (déprécié, note 25) reste pertinente pour illustrer la
  dépréciation sur un vrai cas
- Grok éventuel derrière, pour extraire la chaîne des `Caused by:`
  plutôt que garder toute la trace en un seul champ texte

## Lien avec les notes existantes

`25-multiline-codec-concept.md`, `26-multiline-implementation-ansible-v.md`
(TP `multiline` déjà fait, cas ansible), `tp-filebeat-rh8103-resultat-phase4.md`
(origine des logs Java réels à réutiliser).
