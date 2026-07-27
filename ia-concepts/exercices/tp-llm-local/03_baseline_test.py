# baseline_test.py
import json
import requests

with open("dataset_test.json") as f:
    cas = json.load(f)

CHAMPS = ["type_incident", "cause_racine", "symptome_observe", "service_affecte", "action_recommandee"]

resultats_baseline = []

for i, exemple in enumerate(cas):
#    prompt = f"""Analyse ce log système et produis un résumé structuré avec exactement ces 5 champs : {', '.join(CHAMPS)}.
#
#Log :
#{exemple['log_brut']}
#
#Réponds uniquement avec un JSON contenant ces 5 champs."""
    prompt = f"""Log :
    {exemple['log_brut']}
    
    Analyse ce log système ci-dessus et produis un résumé structuré avec exactement ces 5 champs : {', '.join(CHAMPS)}.
    
    Réponds uniquement avec un JSON contenant ces 5 champs."""

    reponse = requests.post("http://localhost:11434/api/generate", json={
        "model": "qwen3:4b",
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": 8192}
    })

    texte_genere = reponse.json()["response"]
    print(f"Tokens du prompt envoyé : {reponse.json()['prompt_eval_count']}")

    resultats_baseline.append({
        "cas": i,
        "reference": exemple["resume_reference"],
        "reponse_qwen_brute": texte_genere
    })

    print(f"=== Cas {i} ===")
    print("--- Référence ---")
    print(json.dumps(exemple["resume_reference"], ensure_ascii=False, indent=2))
    print("--- Réponse Qwen (avant fine-tuning) ---")
    print(texte_genere)
    print()

with open("baseline_avant_finetuning_4b.json", "w", encoding="utf-8") as f:
    json.dump(resultats_baseline, f, ensure_ascii=False, indent=2)
