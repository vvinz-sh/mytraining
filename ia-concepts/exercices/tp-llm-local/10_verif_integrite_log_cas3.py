import json
with open("dataset_test.json") as f:
    data = json.load(f)

log = data[3]["log_brut"]
print(f"Longueur en caractères : {len(log)}")
print(f"Nombre de lignes : {log.count(chr(10))}")
print("--- 200 premiers caractères ---")
print(log[:200])
print("--- 200 derniers caractères ---")
print(log[-200:])
