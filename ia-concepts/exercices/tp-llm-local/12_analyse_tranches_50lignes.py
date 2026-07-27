from unsloth import FastLanguageModel
import json

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="qwen3-4b-logs-lora-final",
    max_seq_length=8192,
    dtype=None,
    load_in_4bit=True,
)

with open("dataset_test.json") as f:
    data = json.load(f)

lignes = data[3]["log_brut"].split("\n")
print(f"Total lignes : {len(lignes)}")

# Teste chaque tranche de 50 lignes séparément
for i in range(0, len(lignes), 50):
    tranche = "\n".join(lignes[i:i+50])
    n_tokens = len(tokenizer.encode(tranche))
    print(f"Lignes {i}-{i+50} : {n_tokens} tokens")
