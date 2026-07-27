# test_controle_vanilla_cas3_meme_pipeline.py
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
import json

max_seq_length = 24576  # même valeur que l'éval post-fine-tuning

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit",  # modèle VANILLA
    max_seq_length=max_seq_length,
    dtype=None,
    load_in_4bit=True,
)
tokenizer = get_chat_template(tokenizer, chat_template="qwen3")

with open("dataset_test.json") as f:
    cas_test = json.load(f)

CHAMPS = ["type_incident", "cause_racine", "symptome_observe", "service_affecte", "action_recommandee"]
CONSIGNE = f"Analyse ce log système et produis un résumé structuré avec exactement les champs : {', '.join(CHAMPS)}. Réponds uniquement avec un JSON contenant ces 5 champs."

exemple = cas_test[3]  # cas disque plein, celui qui nous intéresse
messages = [{"role": "user", "content": f"{exemple['log_brut']}\n\n{CONSIGNE}"}]
texte = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
texte += "{"  # même prefill que la version finale post-fine-tuning, pour comparer à conditions égales

inputs = tokenizer(texte, return_tensors="pt").to("cuda")
sortie = model.generate(**inputs, max_new_tokens=500, do_sample=False)
reponse = "{" + tokenizer.decode(sortie[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

print("--- VANILLA, même pipeline (transformers/Unsloth, max_seq_length=24576, prefill) ---")
print(reponse)
