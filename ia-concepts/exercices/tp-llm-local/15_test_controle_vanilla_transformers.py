# test_controle_vanilla_transformers.py
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
import json

max_seq_length = 24576

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit",  # modèle VANILLA, pas l'adaptateur
    max_seq_length=max_seq_length,
    dtype=None,
    load_in_4bit=True,
)
tokenizer = get_chat_template(tokenizer, chat_template="qwen3")

with open("dataset_test.json") as f:
    cas_test = json.load(f)

CHAMPS = ["type_incident", "cause_racine", "symptome_observe", "service_affecte", "action_recommandee"]
CONSIGNE = f"Analyse ce log système et produis un résumé structuré avec exactement les champs : {', '.join(CHAMPS)}. Réponds uniquement avec un JSON contenant ces 5 champs."

# Cas 0 uniquement, suffisant pour ce test de contrôle
exemple = cas_test[0]
messages = [{"role": "user", "content": f"{exemple['log_brut']}\n\n{CONSIGNE}"}]
texte = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
# PAS de prefill "{" cette fois, pour voir le comportement naturel

inputs = tokenizer(texte, return_tensors="pt").to("cuda")
sortie = model.generate(**inputs, max_new_tokens=500, do_sample=False)
reponse = tokenizer.decode(sortie[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

print("--- Réponse VANILLA, transformers/Unsloth, do_sample=False, sans prefill ---")
print(reponse)
