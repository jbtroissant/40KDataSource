import os
import re
import sys
import json
from glob import glob

def to_snake_case(name):
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip('_')

# Regex pour trouver les clés d'armes
KEY_PATTERN = re.compile(r'datasheets\.([A-Za-z0-9_]+)\.(meleeWeapons|rangedWeapons)\.(\d+)\.profiles\.(\d+)\.name')

# Cherche le nom d'arme dans le flat anglais
def get_weapon_name(flat_dict, key):
    return flat_dict.get(key, None)

def update_file(filepath, flat_en_dict):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = f.read()
    def replacer(match):
        key = match.group(0)
        weapon_name = get_weapon_name(flat_en_dict, key)
        if weapon_name:
            return to_snake_case(weapon_name)
        else:
            return key # si pas trouvé, on laisse la clé d'origine
    new_data = KEY_PATTERN.sub(replacer, data)
    if new_data != data:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_data)
        print(f"Fichier modifié : {filepath}")
    else:
        print(f"Aucun changement : {filepath}")

def process_faction(faction):
    base = faction.upper()
    files = [
        f"{base}.translated.json",
        f"en/{base}.flat.json",
        f"fr/{base}.flat.json"
    ]
    # Charger le flat anglais pour la correspondance
    flat_en_path = f"en/{base}.flat.json"
    if not os.path.exists(flat_en_path):
        print(f"Flat anglais introuvable pour {base}")
        return
    with open(flat_en_path, 'r', encoding='utf-8') as f:
        flat_en_dict = json.load(f)
    for file in files:
        if os.path.exists(file):
            update_file(file, flat_en_dict)
        else:
            print(f"Fichier introuvable : {file}")

def main():
    if len(sys.argv) > 1:
        # Faction passée en argument
        process_faction(sys.argv[1])
    else:
        # Toutes les factions présentes
        for translated in glob("*.translated.json"):
            faction = translated.split('.')[0]
            process_faction(faction)

if __name__ == '__main__':
    main() 