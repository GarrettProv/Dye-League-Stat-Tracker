import json
import os

def save_json(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def load_json(path: str):
    with open(path, "r") as f:
        return json.load(f)

def save_text(path: str, text: str):
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", errors="replace") as f:
        f.write(text)
