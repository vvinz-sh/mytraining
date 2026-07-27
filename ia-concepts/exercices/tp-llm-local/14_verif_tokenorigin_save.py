from transformers import AutoTokenizer

tok_original = AutoTokenizer.from_pretrained("unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit")
tok_sauvegarde = AutoTokenizer.from_pretrained("qwen3-4b-logs-lora-final")

texte_test = "Jul 21 07:1:00 rh8102 systemd[1]: Started Session 1 of user root."

print(f"Tokenizer original : {len(tok_original.encode(texte_test))} tokens")
print(f"Tokenizer sauvegardé : {len(tok_sauvegarde.encode(texte_test))} tokens")
