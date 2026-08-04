## Annexe — Petite PKI de lab (généré hors Ansible, via `openssl`)

Réalisé et vérifié avant le début de la partie Ansible de ce TP.
À compléter avec le détail exact des commandes utilisées (CA, CSR,
signature, EKU, conversion PKCS#8, génération des certs expirés) —
squelette ci-dessous, pas encore rempli.

Les fichiers/dossiers présents à côté de ce README a titre indicatif, pas représentatif de l'état de la CA après signature.

**1. Autorité de certification (CA) locale**

Création Clé + cert de la CA

```
CANAME=vinz-lab
openssl genrsa -aes256 -out $CANAME.key 4096
openssl req -x509 -new -nodes -key $CANAME.key -sha256 -days 1826 -out $CANAME.crt
```

Initialisation, voir également dossiers/fichiers existants (vides) à côté de ce fichier README
```
echo "1000" > ca.db.serial
```

**2. CSR + signature — cert serveur (Rocky, EKU serverAuth)**

Création key + csr avec SAN - modifier IP par ce qui correspond, se créer un dossier par host
```
openssl req -new -newkey rsa:4096   -keyout rocky/rocky.key -nodes   -out rocky/rocky.csr   -subj "/CN=rocky.localdomain"   -addext "subjectAltName = DNS:rocky.localdomain,IP:192.168.1.XX"
```

Signature et ajout EKU défini dans le profil server (ca.conf)
```
openssl ca -config ca.conf -extensions server -in rocky/rocky.csr -out rocky/rocky.crt
```


**3. CSR + signature — cert client (RH8103, EKU clientAuth)**

Création key + csr avec SAN - modifier IP par ce qui correspond, se créer un dossier par host
```
openssl req -new -newkey rsa:4096 -keyout rh8103/rh8103.key -nodes -out rh8103/rh8103.csr -subj "/CN=rh8103.localdomain" -addext "subjectAltName = DNS:rh8103.localdomain,IP:192.168.1.XX"
```

Signature et ajout EKU défini dans le profil client (ca.conf)
```
 openssl ca -config ca.conf -extensions client -in rh8103/rh8103.csr -out rh8103/rh8103.crt
```

**4. Conversion des clés en PKCS#8 chiffré**
```
openssl pkey -in rocky.key -out rocky_pkcs8.key -aes256
openssl pkey -in rh8103.key -out rh8103_pkcs8.key -aes256
```

**5. Vérifications **
- En-tête `-----BEGIN ENCRYPTED PRIVATE KEY-----` confirmé sur les
  deux clés (`head -n 1`)
- Correspondance modulus clé privée / certificat confirmée par host
  (`openssl pkey ... -pubout | md5` vs `openssl x509 ... -pubkey | md5`)
- SAN vérifié sur chaque certificat (hostname + IP corrects )

**6. Certificats expirés (pour l'Étape 6, "prod ready")**

Génération de certificat déjà expirés
```
openssl ca -config ca.conf -extensions server -in rocky/rocky.csr -out rocky/rocky-expired.crt  -startdate 20240101000000Z -enddate 20240102000000Z
openssl ca -config ca.conf -extensions client -in rh8103/rh8103.csr -out rh8103/rh8103-expired.crt  -startdate 20240101000000Z -enddate 20240102000000Z
```

Vérification
```
openssl x509 -in rocky/rocky-expired.crt -noout -dates
```
