import json
import re
import os
import sys
from collections import defaultdict

# Utilisation : python extract_and_replace_translations.py fichier.json
if len(sys.argv) < 2:
    print("Usage : python extract_and_replace_translations.py <fichier.json>")
    sys.exit(1)

INPUT_FILE = sys.argv[1]
BASENAME = os.path.splitext(os.path.basename(INPUT_FILE))[0]
FR_DIR = 'fr'
EN_DIR = 'en'
TRANSLATION_FILE_FR = os.path.join(FR_DIR, f'{BASENAME}.json')
TRANSLATION_FILE_EN = os.path.join(EN_DIR, f'{BASENAME}.json')
OUTPUT_FILE = os.path.join(EN_DIR, f'{BASENAME}.translated.json')

os.makedirs(FR_DIR, exist_ok=True)
os.makedirs(EN_DIR, exist_ok=True)

# Types considérés comme textuels
TEXT_TYPES = (str,)

# Champs à ignorer (numériques, booléens, techniques)
IGNORED_FIELDS = {"id", "faction_id", "active", "imperialArmour", "showAbility", "showDescription", "showDamagedAbility", "showInfo", "showInvulnerableSave", "showDamagedMarker", "showName", "models", "cost", "value", "order", "turn", "phase", "detachment", "cardType", "source", "updated", "keyword", "keywords", "factions", "faction_id", "parent_id", "is_subfaction", "link"}

# Nettoyage pour générer des clés valides
def clean_key(key):
    key = key.replace(' ', '_').replace('-', '_').replace('’', '').replace("'", "").replace('"', '').replace('.', '').replace(',', '').replace('(', '').replace(')', '').replace('/', '_').replace('?', '').replace(':', '').replace('–', '_').replace('—', '_')
    key = re.sub(r'[^a-zA-Z0-9_]', '', key)
    return key

def extract_texts_nested(obj):
    """
    Retourne un objet imbriqué ne contenant que les champs textuels à traduire, avec la même structure que le JSON d'origine.
    """
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if k in IGNORED_FIELDS:
                continue
            if isinstance(v, TEXT_TYPES) and v.strip() != "" and not v.strip().startswith("http"):
                result[k] = v
            elif isinstance(v, list):
                if v and all(isinstance(i, TEXT_TYPES) and i.strip() != "" for i in v):
                    result[k] = v
                else:
                    nested_list = []
                    for item in v:
                        nested = extract_texts_nested(item)
                        if nested:
                            nested_list.append(nested)
                        else:
                            nested_list.append(None)
                    result[k] = nested_list
            elif isinstance(v, dict):
                nested = extract_texts_nested(v)
                if nested:
                    result[k] = nested
            # sinon, on ignore
        return result if result else None
    elif isinstance(obj, list):
        nested_list = []
        for item in obj:
            nested = extract_texts_nested(item)
            if nested:
                nested_list.append(nested)
            else:
                nested_list.append(None)
        return nested_list if any(nested_list) else None
    else:
        return None

def extract_texts(obj, path=None, translations=None, replaced=None):
    if path is None:
        path = []
    if translations is None:
        translations = {}
    if replaced is None:
        replaced = obj

    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in IGNORED_FIELDS:
                continue
            new_path = path + [clean_key(str(k))]
            if isinstance(v, TEXT_TYPES) and v.strip() != "" and not v.strip().startswith("http"):
                key = '.'.join(new_path)
                translations[key] = v
                replaced[k] = key
            elif isinstance(v, list):
                if v and all(isinstance(i, TEXT_TYPES) and i.strip() != "" for i in v):
                    key = '.'.join(new_path)
                    translations[key] = v
                    replaced[k] = key
                else:
                    replaced[k] = []
                    for idx, item in enumerate(v):
                        if isinstance(item, (dict, list)):
                            if isinstance(item, dict):
                                replaced[k].append({})
                            else:
                                replaced[k].append([])
                            extract_texts(item, new_path + [str(idx)], translations, replaced[k][idx])
                        elif isinstance(item, TEXT_TYPES) and item.strip() != "" and not item.strip().startswith("http"):
                            key = '.'.join(new_path + [str(idx)])
                            translations[key] = item
                            replaced[k].append(key)
                        else:
                            replaced[k].append(item)
            elif isinstance(v, dict):
                replaced[k] = {}
                extract_texts(v, new_path, translations, replaced[k])
            else:
                replaced[k] = v
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            if isinstance(item, (dict, list)):
                if isinstance(item, dict):
                    replaced[idx] = {}
                else:
                    replaced[idx] = []
                extract_texts(item, path + [str(idx)], translations, replaced[idx])
            elif isinstance(item, TEXT_TYPES) and item.strip() != "" and not item.strip().startswith("http"):
                key = '.'.join(path + [str(idx)])
                translations[key] = item
                replaced[idx] = key
            else:
                replaced[idx] = item
    return translations, replaced

# Lecture du fichier d'entrée
with open(INPUT_FILE, encoding='utf-8') as f:
    data = json.load(f)

# Extraction et remplacement
translations, replaced = extract_texts(data)

# Fichiers de traduction imbriqués
fr_nested = extract_texts_nested(data)
en_nested = extract_texts_nested(data)

# Fichiers de traduction FR (à traduire)
with open(TRANSLATION_FILE_FR, 'w', encoding='utf-8') as f:
    json.dump(fr_nested, f, ensure_ascii=False, indent=2)

# Fichiers de traduction EN (texte source, identique à FR ici)
with open(TRANSLATION_FILE_EN, 'w', encoding='utf-8') as f:
    json.dump(en_nested, f, ensure_ascii=False, indent=2)

# Fichier JSON modifié (clé à la place du texte)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(replaced, f, ensure_ascii=False, indent=2)

print(f"Extraction terminée. Traductions imbriquées dans {TRANSLATION_FILE_FR} et {TRANSLATION_FILE_EN}, JSON modifié dans {OUTPUT_FILE}.") 