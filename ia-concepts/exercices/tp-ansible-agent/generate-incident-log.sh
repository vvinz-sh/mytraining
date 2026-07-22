#!/bin/bash
# Génère /var/log/messages-incident avec un incident "espace disque en cascade"
# structuré pour matcher les 3 fenêtres du TP agent : tail -20 / -100 / -500
#
# À exécuter directement sur rh8102 (target VM), via sudo si besoin
# d'écrire dans /var/log/

OUT=/var/log/messages-incident
> "$OUT"

# --- Lignes 1-20 : bruit initial, jamais visible (au-delà de tail -500) ---
for i in $(seq 1 20); do
  echo "Jul 21 07:$((i)):00 rh8102 systemd[1]: Started Session $i of user root." >> "$OUT"
done

# --- Lignes 21-30 : LA CAUSE RACINE (visible seulement avec tail -500) ---
cat >> "$OUT" << 'EOF'
Jul 21 08:00:01 rh8102 backup-job[1234]: Starting full backup to /var/backups
Jul 21 08:15:33 rh8102 backup-job[1234]: Writing archive... 45GB written
Jul 21 08:22:10 rh8102 kernel: EXT4-fs warning: /var running low on free space (2% remaining)
Jul 21 08:22:45 rh8102 backup-job[1234]: Writing archive... 62GB written
Jul 21 08:23:01 rh8102 kernel: EXT4-fs error: No space left on device
Jul 21 08:23:02 rh8102 backup-job[1234]: Backup failed: write error
Jul 21 08:23:03 rh8102 backup-job[1234]: Cleanup incomplete, archive left in /var/backups
Jul 21 08:23:04 rh8102 systemd[1]: backup-job.service: Failed with result 'exit-code'.
Jul 21 08:23:05 rh8102 systemd[1]: Failed to start Nightly Backup Job.
Jul 21 08:25:00 rh8102 kernel: EXT4-fs error: /var: filesystem full
EOF

# --- Lignes 31-420 : bruit générique de remplissage (~390 lignes) ---
for i in $(seq 1 390); do
  echo "Jul 21 08:$((30 + i / 20)):$((i % 60)) rh8102 cron[$((2000+i))]: (root) CMD (run-parts /etc/cron.hourly)" >> "$OUT"
done

# --- Lignes 421-430 : LE SYMPTÔME visible (tail -100 ET -500, pas -20) ---
cat >> "$OUT" << 'EOF'
Jul 21 09:45:10 rh8102 httpd[5678]: AH00526: Syntax error, /etc/httpd/conf.d/ssl.conf skipped
Jul 21 09:45:12 rh8102 httpd[5678]: (28)No space left on device: AH00023: could not bind to port 443
Jul 21 09:45:13 rh8102 httpd[5678]: (28)No space left on device: AH00023: could not bind to port 80
Jul 21 09:45:14 rh8102 systemd[1]: httpd.service: Failed with result 'exit-code'.
Jul 21 09:45:15 rh8102 systemd[1]: Failed to start The Apache HTTP Server.
Jul 21 09:45:20 rh8102 systemd[1]: httpd.service: Scheduled restart job, restart counter is at 3.
Jul 21 09:45:25 rh8102 httpd[5679]: (28)No space left on device: AH00023: could not bind to port 443
Jul 21 09:45:30 rh8102 systemd[1]: httpd.service: Start request repeated too quickly.
Jul 21 09:45:31 rh8102 systemd[1]: httpd.service: Failed with result 'exit-code'.
Jul 21 09:45:32 rh8102 systemd[1]: Failed to start The Apache HTTP Server.
EOF

# --- Lignes 431-500 : bruit générique intermédiaire (~70 lignes) ---
for i in $(seq 1 70); do
  echo "Jul 21 09:$((46 + i / 30)):$((i % 60)) rh8102 sshd[$((3000+i))]: Accepted publickey for vinz from 192.168.56.1" >> "$OUT"
done

# --- Lignes 501-520 : bruit final, seul visible avec tail -20 (ambigu) ---
cat >> "$OUT" << 'EOF'
Jul 21 09:50:01 rh8102 crond[9012]: (root) MAIL (mailed 3 bytes of output but got status 0x0100)
Jul 21 09:50:02 rh8102 postfix/qmgr[3456]: warning: connect to transport private/error: No such file or directory
Jul 21 09:50:03 rh8102 postfix/error[3457]: warning: could not open queue file
Jul 21 09:50:05 rh8102 crond[9013]: (root) MAIL (mailed 3 bytes of output but got status 0x0100)
Jul 21 09:50:10 rh8102 systemd[1]: Started Session 45 of user root.
Jul 21 09:50:15 rh8102 crond[9014]: (root) CMD (run-parts /etc/cron.hourly)
Jul 21 09:50:20 rh8102 postfix/pickup[3458]: warning: connect to transport private/error: No such file or directory
Jul 21 09:50:25 rh8102 systemd[1]: Started Session 46 of user root.
Jul 21 09:50:30 rh8102 crond[9015]: (root) MAIL (mailed 3 bytes of output but got status 0x0100)
Jul 21 09:50:35 rh8102 postfix/qmgr[3459]: warning: connect to transport private/error: No such file or directory
Jul 21 09:50:40 rh8102 systemd[1]: Started Session 47 of user root.
Jul 21 09:50:45 rh8102 crond[9016]: (root) CMD (run-parts /etc/cron.hourly)
Jul 21 09:50:50 rh8102 postfix/error[3460]: warning: could not open queue file
Jul 21 09:50:55 rh8102 systemd[1]: Started Session 48 of user root.
Jul 21 09:51:00 rh8102 crond[9017]: (root) MAIL (mailed 3 bytes of output but got status 0x0100)
Jul 21 09:51:05 rh8102 postfix/pickup[3461]: warning: connect to transport private/error: No such file or directory
Jul 21 09:51:10 rh8102 systemd[1]: Started Session 49 of user root.
Jul 21 09:51:15 rh8102 crond[9018]: (root) CMD (run-parts /etc/cron.hourly)
Jul 21 09:51:20 rh8102 postfix/qmgr[3462]: warning: connect to transport private/error: No such file or directory
Jul 21 09:51:25 rh8102 systemd[1]: Started Session 50 of user root.
EOF

echo "Généré : $OUT ($(wc -l < "$OUT") lignes)"
echo "--- Aperçu tail -20 (devrait être ambigu, bruit générique) ---"
tail -n 20 "$OUT"
