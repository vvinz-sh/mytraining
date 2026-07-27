# generer_dataset_entrainement.py
import anthropic
import json
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

client = anthropic.Anthropic(timeout=120.0)  # 120 secondes au lieu du défaut

SCHEMA = {
    "type": "object",
    "properties": {
        "log_brut": {
            "type": "string",
            "description": "Un log système réaliste (syslog/journalctl), 30-80 lignes, avec du bruit normal mélangé à l'incident"
        },
        "resume_reference": {
            "type": "object",
            "properties": {
                "type_incident": {"type": "string"},
                "cause_racine": {"type": "string"},
                "symptome_observe": {"type": "string"},
                "service_affecte": {"type": "string"},
                "action_recommandee": {"type": "string"}
            },
            "required": ["type_incident", "cause_racine", "symptome_observe", "service_affecte", "action_recommandee"],
            "additionalProperties": False
        }
    },
    "required": ["log_brut", "resume_reference"],
    "additionalProperties": False
}

TYPES_INCIDENTS = [
    "certificat TLS expiré causant une coupure de service",
    "quota disque utilisateur dépassé (pas un disque plein système)",
    "kernel panic ou redémarrage inattendu",
    "unité systemd en échec par dépendance manquante",
    "cron job en échec par permission refusée",
    "denial SELinux bloquant un service",
    "pare-feu mal configuré bloquant un service interne (hors DNS)",
    "échec de boot PXE par timeout TFTP",
    "authentification RADIUS rejetée par shared secret incorrect",
    "montage NFS bloqué ou stale",
    "conflit de dépendances lors d'une mise à jour de paquets",
    "rotation de logs défaillante remplissant le disque progressivement",
    "dérive NTP/chrony causant des échecs d'authentification Kerberos",
    "playbook Ansible en échec, hôte injoignable",
    "épuisement du pool de connexions base de données",
    "charge CPU excessive par un processus qui s'emballe (hors OOM)",
    "array RAID dégradé",
    "thrashing mémoire/swap dégradant les performances"
]

REPETITIONS_PAR_TYPE = 28
TOTAL_PREVU = len(TYPES_INCIDENTS) * REPETITIONS_PAR_TYPE

CONCURRENCE = 5  # nombre d'appels simultanés
lock = threading.Lock()
dataset = []
erreurs = []
debut = datetime.now()

def generer_un_exemple(type_incident, i):
    message = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=6000,
        thinking={"type": "disabled"},
        messages=[{
            "role": "user",
            "content": f"Génère un log système Linux réaliste illustrant : {type_incident}. Varie les noms de service, hostnames, timestamps et détails à chaque génération pour éviter la répétition. Le log doit contenir du bruit normal (cron, sessions, autres services) mélangé aux lignes pertinentes de l'incident."
        }],
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}}
    )
    texte = next(bloc.text for bloc in message.content if bloc.type == "text")
    exemple = json.loads(texte)
    exemple["type_source"] = type_incident
    return exemple

taches = [(t, i) for t in TYPES_INCIDENTS for i in range(REPETITIONS_PAR_TYPE)]
print(f"=== Génération de {len(taches)} exemples, concurrence={CONCURRENCE} ===\n")

with ThreadPoolExecutor(max_workers=CONCURRENCE) as executor:
    futures = {executor.submit(generer_un_exemple, t, i): (t, i) for t, i in taches}

    for future in as_completed(futures):
        type_incident, i = futures[future]
        try:
            exemple = future.result()
            with lock:
                dataset.append(exemple)
                total_fait = len(dataset)
                if total_fait % 10 == 0 or total_fait == len(taches):
                    ecoule = datetime.now() - debut
                    vitesse = total_fait / ecoule.total_seconds()  # exemples par seconde
                    restant = (len(taches) - total_fait) / vitesse if vitesse > 0 else 0
                    eta = datetime.now() + timedelta(seconds=restant)
                    print(f"[{total_fait}/{len(taches)}] ({100*total_fait/len(taches):.1f}%) — écoulé {str(ecoule).split('.')[0]}, vitesse {vitesse:.2f} ex/s, ETA {eta.strftime('%H:%M:%S')}")
                if total_fait % 50 == 0:
                    with open("dataset_entrainement.json", "w", encoding="utf-8") as f:
                        json.dump(dataset, f, ensure_ascii=False, indent=2)
        except Exception as e:
            with lock:
                erreurs.append({"type": type_incident, "iteration": i, "erreur": str(e)})
                print(f"ERREUR sur {type_incident} (#{i}): {e}")

with open("dataset_entrainement.json", "w", encoding="utf-8") as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

print(f"\n=== Terminé en {str(datetime.now() - debut).split('.')[0]} ===")
print(f"{len(dataset)} exemples générés, {len(erreurs)} erreurs")
