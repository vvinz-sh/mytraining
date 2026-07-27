# evaluer_post_finetuning.py
import json
from unsloth import FastLanguageModel

#max_seq_length = 8192
max_seq_length = 24576

# Charge directement le modèle de base + l'adaptateur LoRA
# (Unsloth détecte automatiquement l'adaptateur dans ce dossier)
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="qwen3-4b-logs-lora-final",
    max_seq_length=max_seq_length,
    dtype=None,
    load_in_4bit=True,
)
from unsloth.chat_templates import get_chat_template
tokenizer = get_chat_template(tokenizer, chat_template="qwen3")
print(tokenizer.eos_token, tokenizer.eos_token_id)
print(model.generation_config.eos_token_id)

FastLanguageModel.for_inference(model)  # bascule en mode inférence (2x plus rapide)

with open("dataset_test.json") as f:
    cas_test = json.load(f)

CHAMPS = ["type_incident", "cause_racine", "symptome_observe", "service_affecte", "action_recommandee"]
CONSIGNE = f"Analyse ce log système et produis un résumé structuré avec exactement les champs : {', '.join(CHAMPS)}. Réponds uniquement avec un JSON contenant ces 5 champs."

resultats = []

for i, exemple in enumerate(cas_test):
    # Même ordre que la baseline : log d'abord, consigne à la fin
    messages = [{"role": "user", "content": f"{exemple['log_brut']}\n\n{CONSIGNE}"}]
    texte = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    texte += "{"  # force le début de la réponse à être un JSON, jamais <tool_call>
    
    inputs = tokenizer(texte, return_tensors="pt").to("cuda")
    #sortie = model.generate(**inputs, max_new_tokens=500, do_sample=False, no_repeat_ngram_size=3)
    sortie = model.generate(**inputs, max_new_tokens=500, do_sample=False)
    reponse = "{" + tokenizer.decode(sortie[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    resultats.append({
        "cas": i,
        "reference": exemple["resume_reference"],
        "reponse_apres_finetuning": reponse
    })

    print(f"=== Cas {i} ===")
    print("--- Référence ---")
    print(json.dumps(exemple["resume_reference"], ensure_ascii=False, indent=2))
    print("--- Réponse (après fine-tuning) ---")
    print(reponse)
    print()

with open("resultats_apres_finetuning.json", "w", encoding="utf-8") as f:
    json.dump(resultats, f, ensure_ascii=False, indent=2)
