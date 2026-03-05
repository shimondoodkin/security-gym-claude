"""Tamper script: changes _meta.role from 'user' to 'admin' in vault_backup.json."""
import json

with open("vault_backup.json", "r") as f:
    data = json.load(f)

data["user_data"]["_meta"]["role"] = "admin"

with open("vault_backup.json", "w") as f:
    json.dump(data, f, indent=2)

print("Tampered: role changed to 'admin'.")
