from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
import json

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="qwen3-4b-logs-lora-final",
    max_seq_length=8192,
    dtype=None,
    load_in_4bit=True,
)
tokenizer = get_chat_template(tokenizer, chat_template="qwen3")

with open("dataset_test.json") as f:
    data = json.load(f)

log = data[3]["log_brut"]

# Le log brut seul, sans template
tokens_log_seul = tokenizer.encode(log)
print(f"Log brut seul : {len(tokens_log_seul)} tokens")

# Avec le template complet (comme dans l'évaluation)
messages = [{"role": "user", "content": log + "\n\nConsigne de test"}]
texte_template = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
tokens_avec_template = tokenizer.encode(texte_template)
print(f"Avec template complet : {len(tokens_avec_template)} tokens")
