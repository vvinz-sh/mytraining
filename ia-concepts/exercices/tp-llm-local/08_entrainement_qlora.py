# entrainement_qlora.py
import os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig

max_seq_length = 3072

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit",
    max_seq_length=max_seq_length,
    dtype=None,
    load_in_4bit=True,
    device_map={"": 0},
)

print(f"Empreinte mémoire du modèle : {model.get_memory_footprint() / 1e9:.2f} Go")

tokenizer = get_chat_template(tokenizer, chat_template="qwen3")

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                     "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)

dataset_complet = load_dataset("json", data_files="dataset_entrainement_chatml.json", split="train")

def longueur_ok(exemple):
    texte = tokenizer.apply_chat_template(exemple["conversations"], tokenize=False)
    return len(tokenizer.encode(texte)) <= max_seq_length

dataset_complet = dataset_complet.filter(longueur_ok)
print(f"Dataset après filtrage : {len(dataset_complet)} exemples")

def formatter(examples):
    textes = [tokenizer.apply_chat_template(conv, tokenize=False, add_generation_prompt=False)
              for conv in examples["conversations"]]
    return {"text": textes}

dataset_complet = dataset_complet.map(formatter, batched=True)

dataset_split = dataset_complet.train_test_split(test_size=0.1, seed=3407)
dataset_train = dataset_split["train"]
dataset_eval = dataset_split["test"]

print(f"Entraînement : {len(dataset_train)} exemples — Validation : {len(dataset_eval)} exemples")

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset_train,
    eval_dataset=dataset_eval,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    args=SFTConfig(
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,
        warmup_steps=10,
        num_train_epochs=3,
        learning_rate=2e-4,
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=20,
        optim="adamw_8bit",
        output_dir="qwen3-4b-logs-lora",
        report_to="tensorboard",
        logging_dir="qwen3-4b-logs-lora/runs",
    ),
)

trainer.train()

model.save_pretrained("qwen3-4b-logs-lora-final")
tokenizer.save_pretrained("qwen3-4b-logs-lora-final")

print("Entraînement terminé, adaptateur sauvegardé dans qwen3-4b-logs-lora-final/")
