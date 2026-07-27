# generer_reference_disque_plein.py
import anthropic, json

client = anthropic.Anthropic()

with open("/var/log/messages-incident") as f:
    log_brut = f.read()

SCHEMA = {
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

message = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=6000,
    thinking={"type": "disabled"},
    messages=[{"role": "user", "content": f"Analyse ce log et résume-le selon le schéma demandé:\n\n{log_brut}"}],
    output_config={"format": {"type": "json_schema", "schema": SCHEMA}}
)

texte = next(bloc.text for bloc in message.content if bloc.type == "text")
resume = json.loads(texte)

# Ajoute ce 4e cas au dataset de test existant
with open("dataset_test.json") as f:
    cas_existants = json.load(f)

cas_existants.append({"log_brut": log_brut, "resume_reference": resume})

with open("dataset_test.json", "w", encoding="utf-8") as f:
    json.dump(cas_existants, f, ensure_ascii=False, indent=2)

print("4e cas (disque plein) ajouté à dataset_test.json")
