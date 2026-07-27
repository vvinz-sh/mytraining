# generer_test_logs.py
import anthropic
import json

client = anthropic.Anthropic()  # clé API lue depuis ANTHROPIC_API_KEY

SCHEMA = {
    "type": "object",
    "properties": {
        "log_brut": {
            "type": "string",
            "description": "Un log système réaliste (syslog/journalctl), 40-80 lignes, avec du bruit normal mélangé à l'incident"
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

INCIDENTS_TEST = [
    "un service applicatif qui crash en boucle suite à un OOM kill (out of memory), avec redémarrages répétés par systemd",
    "une erreur réseau : le serveur ne peut plus résoudre les noms DNS, ou les connexions sortantes sont refusées",
    "un problème d'authentification : le cache SSSD renvoie des utilisateurs introuvables alors qu'ils existent bien dans LDAP, potentiellement lié à un LDAP down ou une désynchronisation de cache"
]

resultats = []
for description in INCIDENTS_TEST:
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=6000,
        thinking={"type": "disabled"},
        messages=[{
            "role": "user",
            "content": f"Génère un log système Linux réaliste illustrant {description}. Le log doit contenir du bruit normal (cron, sessions, autres services) mélangé aux lignes pertinentes de l'incident, pour qu'un modèle doive vraiment distinguer le signal du bruit."
        }],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": SCHEMA
            }
        }
    )
    texte = next(bloc.text for bloc in message.content if bloc.type == "text")
    resultats.append(json.loads(texte))

with open("dataset_test.json", "w", encoding="utf-8") as f:
    json.dump(resultats, f, ensure_ascii=False, indent=2)

print(f"{len(resultats)} cas de test générés dans dataset_test.json")
