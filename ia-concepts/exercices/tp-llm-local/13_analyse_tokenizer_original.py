from unsloth import FastLanguageModel
import json
from transformers import AutoTokenizer

tok_original = AutoTokenizer.from_pretrained("unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit")

with open("dataset_test.json") as f:
    data = json.load(f)

lignes = data[3]["log_brut"].split("\n")
tranche = "\n".join(lignes[0:50])
print(f"Tokenizer original sur lignes 0-50 : {len(tok_original.encode(tranche))} tokens")
