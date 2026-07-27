import json
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("unsloth/Qwen3-8B")

with open("dataset_entrainement_chatml.json") as f:
    dataset = json.load(f)

longueurs = []
for exemple in dataset:
    texte = tokenizer.apply_chat_template(exemple["conversations"], tokenize=False)
    longueurs.append(len(tokenizer.encode(texte)))

print(f"Min: {min(longueurs)}, Max: {max(longueurs)}, Moyenne: {sum(longueurs)/len(longueurs):.0f}")

import numpy as np
longueurs = np.array(longueurs)
for seuil in [2048, 2560, 3072, 3584, 4096]:
    depassent = (longueurs > seuil).sum()
    print(f"Seuil {seuil}: {depassent}/{len(longueurs)} exemples dépasseraient ({100*depassent/len(longueurs):.1f}%)")
