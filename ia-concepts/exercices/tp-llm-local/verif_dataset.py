import json
from collections import Counter

with open("dataset_entrainement.json") as f:
    dataset = json.load(f)

repartition = Counter(ex["type_source"] for ex in dataset)
for type_incident, count in repartition.items():
    print(f"{count:3d} — {type_incident}")

print(f"\nTotal : {len(dataset)}")
