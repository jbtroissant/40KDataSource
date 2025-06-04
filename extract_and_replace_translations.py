import json
import re
import os
import sys
import shutil
from collections import defaultdict

# Utilisation : python extract_and_replace_translations.py fichier.json
if len(sys.argv) < 2:
    print("Usage : python extract_and_replace_translations.py <fichier.json>")
    sys.exit(1)

INPUT_FILE = sys.argv[1]
BASENAME = os.path.splitext(os.path.basename(INPUT_FILE))[0]

# --- NOUVEAU : Charger le JSON pour récupérer l'id, sauf pour core ---
with open(INPUT_FILE, encoding='utf-8') as f:
    data = json.load(f)

if BASENAME == "core":
    data_id = BASENAME
else:
    data_id = data.get("id", BASENAME)
# --- FIN NOUVEAU ---

FR_DIR = 'fr'
EN_DIR = 'en'
TRANSLATION_FILE_FR = os.path.join(FR_DIR, f'{data_id}.json')
TRANSLATION_FILE_EN = os.path.join(EN_DIR, f'{data_id}.json')
OUTPUT_FILE = os.path.join(EN_DIR, f'{data_id}.translated.json')

ARCHIVE_DIR = 'archive'
os.makedirs(ARCHIVE_DIR, exist_ok=True)
ARCHIVE_FILE = os.path.join(ARCHIVE_DIR, os.path.basename(INPUT_FILE))

# Archive le fichier source avant toute modification
if not os.path.exists(ARCHIVE_FILE):
    shutil.copy2(INPUT_FILE, ARCHIVE_FILE)

os.makedirs(FR_DIR, exist_ok=True)
os.makedirs(EN_DIR, exist_ok=True)

# Types considérés comme textuels
TEXT_TYPES = (str,)

# Champs à ignorer (numériques, booléens, techniques)
IGNORED_FIELDS = {"id", "faction_id", "active", "imperialArmour", "showAbility", "showDescription", "showDamagedAbility", "showDamagedMarker", "showName", "models", "cost", "turn", "phase", "cardType", "source", "updated", "keyword", "keywords", "factions", "faction_id", "parent_id", "is_subfaction", "link", "points"}

# Champs à ignorer dans les profils d'armes
PROFILE_FIELDS = {"ap", "attacks", "damage", "name", "range", "skill", "strength"}
# Champs à ignorer dans stats (sauf name)
STATS_FIELDS = {"active", "ld", "m", "oc", "showDamagedMarker", "showName", "sv", "t", "w"}

# Ajoute une liste de champs à ne jamais traduire dans certains contextes (ex: invul)
NEVER_TRANSLATE_FIELDS = {"value", "showInfo", "showInvulnerableSave", "showAtTop", "banner", "header", "allied_factions", "id", "turn", "faction_id", "type", "invul"}

# Fonction utilitaire pour savoir si on est dans un profil d'arme
PROFILE_PATHS = [
    ["meleeWeapons", "profiles"],
    ["rangedWeapons", "profiles"]
]
# Fonction utilitaire pour savoir si on est dans stats
STATS_PATH = ["stats"]

def is_profile_path(path):
    # Ignore les indices numériques dans le chemin
    filtered_path = [p for p in path if not p.isdigit()]
    for profile_path in PROFILE_PATHS:
        for i in range(len(filtered_path) - len(profile_path) + 1):
            if filtered_path[i:i+len(profile_path)] == profile_path:
                return True
    return False

def is_stats_path(path):
    # On est dans stats si le chemin contient 'stats' suivi d'un index
    for i in range(len(path)-1):
        if path[i] == "stats" and path[i+1].isdigit():
            return True
    return False

def is_enhancement_path(path):
    # On est dans enhancements si le chemin contient 'enhancements' suivi d'un index
    for i in range(len(path)-1):
        if path[i] == "enhancements" and path[i+1].isdigit():
            return True
    return False

def is_stratagem_path(path):
    # On est dans stratagems si le chemin contient 'stratagems' suivi d'un index
    for i in range(len(path)-1):
        if path[i] == "stratagems" and path[i+1].isdigit():
            return True
    return False

ENHANCEMENT_TRANSLATE_FIELDS = {"name", "description", "detachment"}

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

def extract_texts(obj, path=None, translations=None, replaced=None, value_to_key=None):
    if path is None:
        path = []
    if translations is None:
        translations = {}
    if replaced is None:
        replaced = obj
    if value_to_key is None:
        value_to_key = {}

    def make_key(path, k):
        if not path:
            return 'root.' + clean_key(str(k))
        return '.'.join(path + [clean_key(str(k))])

    if isinstance(obj, dict):
        temp = {}
        for k, v in obj.items():
            if k == "link":
                continue  # On supprime le champ 'link' du JSON traduit
            if k in IGNORED_FIELDS:
                temp[k] = v
                continue
            if k in NEVER_TRANSLATE_FIELDS:
                temp[k] = v
                continue
            if k in ["keywords", "keyword"] and isinstance(v, list) and all(isinstance(i, TEXT_TYPES) and i.strip() != "" for i in v):
                temp[k] = []
                for item in v:
                    translations[item] = item
                    temp[k].append(item)
                continue
            if is_enhancement_path(path):
                if k in ENHANCEMENT_TRANSLATE_FIELDS and isinstance(v, TEXT_TYPES) and v.strip() != "" and not v.strip().startswith("http"):
                    if v in value_to_key:
                        key = value_to_key[v]
                    else:
                        key = make_key(path, k)
                        value_to_key[v] = key
                    translations[key] = v
                    temp[k] = key
                    continue
                else:
                    temp[k] = v
                    continue
            if is_stratagem_path(path):
                if isinstance(v, TEXT_TYPES) and v.strip() != "" and not v.strip().startswith("http"):
                    if v in value_to_key:
                        key = value_to_key[v]
                    else:
                        key = make_key(path, k)
                        value_to_key[v] = key
                    translations[key] = v
                    temp[k] = key
                    continue
                else:
                    temp[k] = v
                    continue
            new_path = path + [clean_key(str(k))]
            if is_profile_path(path):
                if k == "name" and isinstance(v, TEXT_TYPES) and v.strip() != "" and not v.strip().startswith("http"):
                    if v in value_to_key:
                        key = value_to_key[v]
                    else:
                        key = make_key(path, k)
                        value_to_key[v] = key
                    translations[key] = v
                    temp[k] = key
                    continue
                elif k in PROFILE_FIELDS:
                    temp[k] = v
                    continue
            if is_stats_path(path) and k in STATS_FIELDS:
                temp[k] = v
                continue
            if isinstance(v, TEXT_TYPES) and v.strip() != "" and not v.strip().startswith("http"):
                if v in value_to_key:
                    key = value_to_key[v]
                else:
                    key = make_key(path, k)
                    value_to_key[v] = key
                translations[key] = v
                temp[k] = key
            elif isinstance(v, list):
                if v and all(isinstance(i, TEXT_TYPES) and i.strip() != "" for i in v):
                    temp[k] = []
                    for idx, item in enumerate(v):
                        if item in value_to_key:
                            key = value_to_key[item]
                        else:
                            key = make_key(new_path, str(idx))
                            value_to_key[item] = key
                        translations[key] = item
                        temp[k].append(key)
                else:
                    sublist = []
                    for idx, item in enumerate(v):
                        if isinstance(item, (dict, list)):
                            if isinstance(item, dict):
                                sub = {}
                            else:
                                sub = []
                            extract_texts(item, new_path + [str(idx)], translations, sub, value_to_key)
                            if (isinstance(sub, dict) and not sub) or (isinstance(sub, list) and not sub):
                                sublist.append(item)
                            else:
                                sublist.append(sub)
                        elif isinstance(item, TEXT_TYPES) and item.strip() != "" and not item.strip().startswith("http"):
                            if item in value_to_key:
                                key = value_to_key[item]
                            else:
                                key = make_key(new_path, str(idx))
                                value_to_key[item] = key
                            translations[key] = item
                            sublist.append(key)
                        else:
                            sublist.append(item)
                    temp[k] = sublist
            elif isinstance(v, dict):
                sub = {}
                extract_texts(v, new_path, translations, sub, value_to_key)
                if not sub:
                    temp[k] = v
                else:
                    temp[k] = sub
            else:
                temp[k] = v
        replaced.clear()
        replaced.update(temp)
    elif isinstance(obj, list):
        sublist = []
        for idx, item in enumerate(obj):
            if isinstance(item, (dict, list)):
                if isinstance(item, dict):
                    sub = {}
                else:
                    sub = []
                extract_texts(item, path + [str(idx)], translations, sub, value_to_key)
                if (isinstance(sub, dict) and not sub) or (isinstance(sub, list) and not sub):
                    sublist.append(item)
                else:
                    sublist.append(sub)
            elif isinstance(item, TEXT_TYPES) and item.strip() != "" and not item.strip().startswith("http"):
                if item in value_to_key:
                    key = value_to_key[item]
                else:
                    key = make_key(path, str(idx))
                    value_to_key[item] = key
                translations[key] = item
                sublist.append(key)
            else:
                sublist.append(item)
        replaced.clear()
        replaced.extend(sublist)
    return translations, replaced

# --- NOUVEAU : Fonction pour réorganiser les enhancements ---
def reorganize_enhancements(data):
    if BASENAME == "core":
        return data
        
    if "enhancements" not in data:
        return data

    enhancements = data.pop("enhancements")
    
    # Si pas de détachements, on les crée
    if "detachments" not in data:
        data["detachments"] = []

    # Pour chaque enhancement
    for enhancement in enhancements:
        detachment_name = enhancement.get("detachment", "")
        if not detachment_name:
            continue

        # Supprime la clé 'detachment' de l'enhancement
        enhancement.pop("detachment", None)

        # Cherche le détachement correspondant
        found = False
        for i, detachment in enumerate(data["detachments"]):
            # Si le détachement est une chaîne, on le compare directement
            if isinstance(detachment, str) and detachment == detachment_name:
                # Convertit le détachement en objet
                data["detachments"][i] = {
                    "name": detachment_name,
                    "enhancements": [enhancement]
                }
                found = True
                break
            # Si le détachement est un objet, on compare son nom
            elif isinstance(detachment, dict) and detachment.get("name") == detachment_name:
                if "enhancements" not in detachment:
                    detachment["enhancements"] = []
                detachment["enhancements"].append(enhancement)
                found = True
                break

        # Si le détachement n'existe pas, on le crée
        if not found:
            new_detachment = {
                "name": detachment_name,
                "enhancements": [enhancement]
            }
            data["detachments"].append(new_detachment)

    return data

# --- NOUVEAU : Fonction pour réorganiser les règles de détachement ---
def reorganize_detachment_rules(data):
    if BASENAME == "core":
        return data
        
    if "rules" not in data or "detachment" not in data["rules"]:
        return data

    detachment_rules = data["rules"].pop("detachment")
    
    # Si pas de détachements, on les crée
    if "detachments" not in data:
        data["detachments"] = []

    # Pour chaque règle de détachement
    for rule in detachment_rules:
        detachment_name = rule.get("detachment", "")
        if not detachment_name:
            continue

        # Supprime la clé 'detachment' de la règle
        rule.pop("detachment", None)

        # Cherche le détachement correspondant
        found = False
        for i, detachment in enumerate(data["detachments"]):
            # Si le détachement est une chaîne, on le compare directement
            if isinstance(detachment, str) and detachment == detachment_name:
                # Convertit le détachement en objet
                data["detachments"][i] = {
                    "name": detachment_name,
                    "rules": [rule]
                }
                found = True
                break
            # Si le détachement est un objet, on compare son nom
            elif isinstance(detachment, dict) and detachment.get("name") == detachment_name:
                if "rules" not in detachment:
                    detachment["rules"] = []
                detachment["rules"].append(rule)
                found = True
                break

        # Si le détachement n'existe pas, on le crée
        if not found:
            new_detachment = {
                "name": detachment_name,
                "rules": [rule]
            }
            data["detachments"].append(new_detachment)

    return data

# --- NOUVEAU : Fonction pour réorganiser les stratagèmes ---
def reorganize_stratagems(data):
    if BASENAME == "core":
        return data
        
    if "stratagems" not in data:
        return data

    stratagems = data.pop("stratagems")
    
    # Si pas de détachements, on les crée
    if "detachments" not in data:
        data["detachments"] = []

    # Pour chaque stratagème
    for stratagem in stratagems:
        detachment_name = stratagem.get("detachment", "")
        if not detachment_name:
            continue

        # Supprime la clé 'detachment' du stratagème
        stratagem.pop("detachment", None)

        # Cherche le détachement correspondant
        found = False
        for i, detachment in enumerate(data["detachments"]):
            # Si le détachement est une chaîne, on le compare directement
            if isinstance(detachment, str) and detachment == detachment_name:
                # Convertit le détachement en objet
                data["detachments"][i] = {
                    "name": detachment_name,
                    "stratagems": [stratagem]
                }
                found = True
                break
            # Si le détachement est un objet, on compare son nom
            elif isinstance(detachment, dict) and detachment.get("name") == detachment_name:
                if "stratagems" not in detachment:
                    detachment["stratagems"] = []
                detachment["stratagems"].append(stratagem)
                found = True
                break

        # Si le détachement n'existe pas, on le crée
        if not found:
            new_detachment = {
                "name": detachment_name,
                "stratagems": [stratagem]
            }
            data["detachments"].append(new_detachment)

    return data

# --- NOUVEAU : Fonction pour ajouter l'invul dans les stats ---
def add_invul_to_stats(data):
    if "datasheets" not in data:
        return data

    for datasheet in data["datasheets"]:
        if "abilities" in datasheet and "invul" in datasheet["abilities"]:
            invul_value = datasheet["abilities"]["invul"].get("value", "")
            if invul_value and "stats" in datasheet:
                for stat in datasheet["stats"]:
                    stat["invul"] = invul_value
            # Supprime la section invul des abilities
            datasheet["abilities"].pop("invul", None)

    return data

# Réorganisation des enhancements, des règles et des stratagèmes avant l'extraction
data = reorganize_enhancements(data)
data = reorganize_detachment_rules(data)
data = reorganize_stratagems(data)
data = add_invul_to_stats(data)

# Extraction et remplacement
translations, replaced = extract_texts(data)

# Fichiers à plat uniquement
FLAT_FILE_FR = os.path.join(FR_DIR, f'{data_id}.flat.json')
FLAT_FILE_EN = os.path.join(EN_DIR, f'{data_id}.flat.json')

with open(FLAT_FILE_FR, 'w', encoding='utf-8') as f:
    json.dump(translations, f, ensure_ascii=False, indent=2)
with open(FLAT_FILE_EN, 'w', encoding='utf-8') as f:
    json.dump(translations, f, ensure_ascii=False, indent=2)

# Fichier JSON modifié (clé à la place du texte) à la racine
OUTPUT_FILE = f'{data_id}.translated.json'
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(replaced, f, ensure_ascii=False, indent=2)

print(f"Extraction terminée. Fichiers à plat dans {FLAT_FILE_FR} et {FLAT_FILE_EN}, JSON modifié dans {OUTPUT_FILE}.") 