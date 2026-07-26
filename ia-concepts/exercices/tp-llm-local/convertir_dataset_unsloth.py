# convertir_dataset_unsloth.py
import json

with open("dataset_entrainement.json") as f:
    dataset = json.load(f)

CONSIGNE = "Analyse ce log système et produis un résumé structuré avec exactement les champs : type_incident, cause_racine, symptome_observe, service_affecte, action_recommandee. Réponds uniquement avec un JSON contenant ces 5 champs."

dataset_converti = []

for exemple in dataset:
    log = exemple["log_brut"]
    resume = exemple["resume_reference"]

    # Consigne à la fin du prompt utilisateur, log en premier
    # (même leçon apprise avec la baseline sur le log 520 lignes)
    contenu_user = f"{log}\n\n{CONSIGNE}"
    contenu_assistant = json.dumps(resume, ensure_ascii=False)

    dataset_converti.append({
        "conversations": [
            {"role": "user", "content": contenu_user},
            {"role": "assistant", "content": contenu_assistant}
        ]
    })

with open("dataset_entrainement_chatml.json", "w", encoding="utf-8") as f:
    json.dump(dataset_converti, f, ensure_ascii=False, indent=2)

print(f"{len(dataset_converti)} exemples convertis au format conversationnel")
