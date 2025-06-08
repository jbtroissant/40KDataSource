import json
import re
import os
import sys
import shutil
from collections import defaultdict

def process_file(input_file):
    BASENAME = os.path.splitext(os.path.basename(input_file))[0]

    # --- NOUVEAU : Charger le JSON pour récupérer l'id, sauf pour core ---
    with open(input_file, encoding='utf-8') as f:
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
    ARCHIVE_FILE = os.path.join(ARCHIVE_DIR, os.path.basename(input_file))

    # Archive le fichier source avant toute modification
    if not os.path.exists(ARCHIVE_FILE):
        shutil.copy2(input_file, ARCHIVE_FILE)
        # Supprime le fichier d'origine après l'archivage
        os.remove(input_file)

    os.makedirs(FR_DIR, exist_ok=True)
    os.makedirs(EN_DIR, exist_ok=True)

    # Types considérés comme textuels
    TEXT_TYPES = (str,)

    # Champs à ignorer (numériques, booléens, techniques)
    IGNORED_FIELDS = {"id", "faction_id", "active", "imperialArmour", "showAbility", "showDescription", "showDamagedAbility", "showDamagedMarker", "showName", "models", "cost", "turn", "phase", "cardType", "source", "updated", "factions", "faction_id", "parent_id", "is_subfaction", "link", "points"}

    # Champs à ignorer dans les profils d'armes
    PROFILE_FIELDS = {"ap", "attacks", "damage", "name", "range", "skill", "strength"}
    # Champs à ignorer dans stats (sauf name)
    STATS_FIELDS = {"active", "ld", "m", "oc", "showDamagedMarker", "showName", "sv", "t", "w"}

    # Ajoute une liste de champs à ne jamais traduire dans certains contextes (ex: invul)
    NEVER_TRANSLATE_FIELDS = {"value", "showInfo", "showInvulnerableSave", "showAtTop", "banner", "header", "allied_factions", "id", "turn", "faction_id", "type", "invul"}

    # Liste des mots-clés prioritaires à traduire en premier
    KEYWORDS_PRIORITY = {"Epic Hero", "Character", "Battleline", "Infantry", "Mounted", "Swarm", "Vehicle", "Fortification", "Other", "Fly", "Aircraft"}

    # Liste des mots supplémentaires à traduire en premier
    ADDITIONAL_PRIORITY_WORDS = {"Hover", "Deep Strike", "Leader", "Infiltrators", "Lone Operative", "Fights First", "Stealth"}

    # Préfixes à traiter en priorité
    PRIORITY_PREFIXES = ["Feel No Pain ", "Scouts ", "Deadly Demise ", "Firing Deck "]

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

    # --- NOUVEAU : mapping index->nom pour datasheets, stratagems, enhancements, detachments, rules.army ---
    datasheet_index_to_name = {}
    if isinstance(data.get("datasheets"), list):
        for idx, ds in enumerate(data["datasheets"]):
            ds_name = ds.get("name")
            if ds_name:
                datasheet_index_to_name[str(idx)] = clean_key(ds_name)

    stratagem_index_to_name = {}
    if isinstance(data.get("stratagems"), list):
        for idx, strat in enumerate(data["stratagems"]):
            strat_name = strat.get("name")
            if strat_name:
                stratagem_index_to_name[str(idx)] = clean_key(strat_name)

    enhancement_index_to_name = {}
    if isinstance(data.get("enhancements"), list):
        for idx, enh in enumerate(data["enhancements"]):
            enh_name = enh.get("name")
            if enh_name:
                enhancement_index_to_name[str(idx)] = clean_key(enh_name)

    detachment_index_to_name = {}
    if isinstance(data.get("detachments"), list):
        for idx, det in enumerate(data["detachments"]):
            if isinstance(det, dict):
                det_name = det.get("name")
            elif isinstance(det, str):
                det_name = det
            else:
                continue
            if det_name:
                detachment_index_to_name[str(idx)] = clean_key(det_name)

    army_rule_index_to_name = {}
    if isinstance(data.get("rules"), dict) and isinstance(data["rules"].get("army"), list):
        for idx, rule in enumerate(data["rules"]["army"]):
            if isinstance(rule, dict):
                rule_name = rule.get("name")
            elif isinstance(rule, str):
                rule_name = rule
            else:
                continue
            if rule_name:
                army_rule_index_to_name[str(idx)] = clean_key(rule_name)

    def get_detachment_name_for_stratagem(data, stratagem):
        # Si le stratagème a directement un champ detachment
        if isinstance(stratagem, dict) and "detachment" in stratagem:
            return stratagem["detachment"]
        
        # Sinon, on cherche dans le chemin pour trouver le détachement
        if isinstance(data, dict) and "detachments" in data:
            for detachment in data["detachments"]:
                if isinstance(detachment, dict) and "stratagems" in detachment:
                    for s in detachment["stratagems"]:
                        if isinstance(s, dict) and s.get("id") == stratagem.get("id"):
                            return detachment.get("name", "Default Detachment")
                elif isinstance(detachment, str):
                    return detachment
        
        return "Default Detachment"

    def make_key(path, k):
        # --- NOUVEAU : remplace l'index de datasheet, stratagem, enhancement, detachment, rules.army par le nom ---
        new_path = []
        i = 0
        while i < len(path):
            if path[i] == "datasheets" and i+1 < len(path):
                idx = path[i+1]
                if idx in datasheet_index_to_name:
                    new_path.append("datasheets")
                    new_path.append(datasheet_index_to_name[idx])
                    i += 2
                    continue
            if path[i] == "stratagems" and i+1 < len(path):
                idx = path[i+1]
                if idx in stratagem_index_to_name:
                    new_path.append("stratagems")
                    new_path.append(stratagem_index_to_name[idx])
                    i += 2
                    continue
            if path[i] == "enhancements" and i+1 < len(path):
                idx = path[i+1]
                if idx in enhancement_index_to_name:
                    new_path.append("enhancements")
                    new_path.append(enhancement_index_to_name[idx])
                    i += 2
                    continue
            if path[i] == "detachments" and i+1 < len(path):
                idx = path[i+1]
                if idx in detachment_index_to_name:
                    new_path.append("detachments")
                    new_path.append(detachment_index_to_name[idx])
                    i += 2
                    continue
            if path[i] == "rules" and i+1 < len(path) and path[i+1] == "army" and i+2 < len(path):
                idx = path[i+2]
                if idx in army_rule_index_to_name:
                    new_path.append("rules")
                    new_path.append("army")
                    new_path.append(army_rule_index_to_name[idx])
                    i += 3
                    continue
            new_path.append(path[i])
            i += 1
        # Pour la clé courante
        if k == "datasheets" and len(path) > 0 and path[-1] in datasheet_index_to_name:
            new_path.append("datasheets")
            new_path.append(datasheet_index_to_name[path[-1]])
        elif k == "stratagems" and len(path) > 0 and path[-1] in stratagem_index_to_name:
            new_path.append("stratagems")
            new_path.append(stratagem_index_to_name[path[-1]])
        elif k == "enhancements" and len(path) > 0 and path[-1] in enhancement_index_to_name:
            new_path.append("enhancements")
            new_path.append(enhancement_index_to_name[path[-1]])
        elif k == "detachments" and len(path) > 0 and path[-1] in detachment_index_to_name:
            new_path.append("detachments")
            new_path.append(detachment_index_to_name[path[-1]])
        elif k == "army" and len(path) > 1 and path[-2] == "rules" and path[-1] in army_rule_index_to_name:
            new_path.append("rules")
            new_path.append("army")
            new_path.append(army_rule_index_to_name[path[-1]])
        else:
            new_path.append(clean_key(str(k)))
        return '.'.join(new_path)

    def extract_texts(obj, path=None, translations=None, replaced=None, value_to_key=None, root_data=None):
        if path is None:
            path = []
        if translations is None:
            translations = {}
        if replaced is None:
            replaced = obj
        if value_to_key is None:
            value_to_key = {}
        if root_data is None:
            root_data = obj

        def is_priority_value(val):
            return (
                val in KEYWORDS_PRIORITY
                or val in ADDITIONAL_PRIORITY_WORDS
                or any(val.startswith(prefix) for prefix in PRIORITY_PREFIXES)
            )

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
                        value_to_key[item] = item
                        temp[k].append(item)
                    continue
                if isinstance(v, TEXT_TYPES) and v.strip() != "" and not v.strip().startswith("http"):
                    if is_priority_value(v):
                        translations[v] = v
                        value_to_key[v] = v
                        temp[k] = v
                        continue
                if is_enhancement_path(path):
                    if k in ENHANCEMENT_TRANSLATE_FIELDS and isinstance(v, TEXT_TYPES) and v.strip() != "" and not v.strip().startswith("http"):
                        if is_priority_value(v):
                            key = v
                        elif v in value_to_key:
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
                        if is_priority_value(v):
                            key = v
                        elif v in value_to_key:
                            key = value_to_key[v]
                        else:
                            # Pour les stratagèmes, on utilise uniquement le nom du stratagème et l'attribut
                            stratagem_name = obj.get('name', '')
                            key = f"stratagems.{clean_key(stratagem_name)}.{k}"
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
                        if is_priority_value(v):
                            key = v
                        elif v in value_to_key:
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
                    if is_priority_value(v):
                        key = v
                    elif v in value_to_key:
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
                            if is_priority_value(item):
                                key = item
                            elif item in value_to_key:
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
                                extract_texts(item, new_path + [str(idx)], translations, sub, value_to_key, root_data)
                                if (isinstance(sub, dict) and not sub) or (isinstance(sub, list) and not sub):
                                    sublist.append(item)
                                else:
                                    sublist.append(sub)
                            elif isinstance(item, TEXT_TYPES) and item.strip() != "" and not item.strip().startswith("http"):
                                if is_priority_value(item):
                                    key = item
                                elif item in value_to_key:
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
                    extract_texts(v, new_path, translations, sub, value_to_key, root_data)
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
                    extract_texts(item, path + [str(idx)], translations, sub, value_to_key, root_data)
                    if (isinstance(sub, dict) and not sub) or (isinstance(sub, list) and not sub):
                        sublist.append(item)
                    else:
                        sublist.append(sub)
                elif isinstance(item, TEXT_TYPES) and item.strip() != "" and not item.strip().startswith("http"):
                    if is_priority_value(item):
                        key = item
                    elif item in value_to_key:
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
    translations, replaced = extract_texts(data, root_data=data)

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

    print(f"Traitement terminé pour {input_file}. Fichiers à plat dans {FLAT_FILE_FR} et {FLAT_FILE_EN}, JSON modifié dans {OUTPUT_FILE}.")

def main():
    if len(sys.argv) < 2:
        print("Usage :")
        print("  Pour un fichier unique : python extract_and_replace_translations.py <fichier.json>")
        print("  Pour un dossier entier : python extract_and_replace_translations.py --dir <dossier>")
        sys.exit(1)

    if sys.argv[1] == "--dir":
        if len(sys.argv) != 3:
            print("Usage pour le traitement d'un dossier : python extract_and_replace_translations.py --dir <dossier>")
            sys.exit(1)
        
        directory = sys.argv[2]
        if not os.path.isdir(directory):
            print(f"Erreur : {directory} n'est pas un dossier valide")
            sys.exit(1)

        json_files = [f for f in os.listdir(directory) if f.endswith('.json')]
        if not json_files:
            print(f"Aucun fichier JSON trouvé dans {directory}")
            sys.exit(1)

        print(f"Traitement de {len(json_files)} fichiers JSON dans {directory}")
        for json_file in json_files:
            input_file = os.path.join(directory, json_file)
            try:
                process_file(input_file)
            except Exception as e:
                print(f"Erreur lors du traitement de {json_file}: {str(e)}")
    else:
        input_file = sys.argv[1]
        if not os.path.isfile(input_file):
            print(f"Erreur : {input_file} n'est pas un fichier valide")
            sys.exit(1)
        process_file(input_file)

if __name__ == "__main__":
    main() 