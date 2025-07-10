#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour mettre à jour les points des datasheets à partir du fichier munitorum_data_final.json
"""

import json
import os
from pathlib import Path
import unicodedata

def normalize_name(name):
    # Supprimer les accents, mettre en minuscule, enlever certains mots, espaces et caractères spéciaux
    name = name.lower()
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    # Enlever les mots inutiles à la fin
    for suffix in [" squad", " unit", " team", " detachment", " squads", " units", " teams"]:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    # Enlever tout ce qui n'est pas lettre ou chiffre
    name = ''.join(c for c in name if c.isalnum())
    return name

def find_matching_datasheet(datasheet_name, munitorum_units):
    clean_name = normalize_name(datasheet_name)
    for unit in munitorum_units:
        clean_unit_name = normalize_name(unit['name'])
        if clean_unit_name == clean_name:
            return unit
        if clean_name in clean_unit_name or clean_unit_name in clean_name:
            return unit
    return None

def update_datasheet_points(datasheet, munitorum_unit):
    datasheet['points'] = []
    for cost in munitorum_unit.get('costs', []):
        # On garde la structure la plus simple possible
        new_point = {
            "cost": cost["cost"],
            "name": cost.get("cost_name", None),
        }
        if "source" in cost:
            new_point["source"] = cost["source"]
        datasheet['points'].append(new_point)

def main():
    munitorum_file = "munitorum_data_final.json"
    archive_dir = "archive"

    if not os.path.exists(munitorum_file):
        print(f"Fichier {munitorum_file} non trouvé!")
        return

    with open(munitorum_file, 'r', encoding='utf-8') as f:
        munitorum_data = json.load(f)

    # Indexer les factions par nom normalisé
    munitorum_factions = {}
    for faction in munitorum_data.get('factions', []):
        norm_name = normalize_name(faction['name'])
        munitorum_factions[norm_name] = faction

    all_legends = []
    all_missing = []
    for archive_file in Path(archive_dir).glob("*.json"):
        with open(archive_file, 'r', encoding='utf-8') as f:
            archive_data = json.load(f)
        archive_faction_name = archive_file.stem
        norm_archive_faction = normalize_name(archive_faction_name)
        # Trouver la faction correspondante dans le JSON
        munitorum_faction = None
        for key in munitorum_factions:
            if norm_archive_faction == key or norm_archive_faction in key or key in norm_archive_faction:
                munitorum_faction = munitorum_factions[key]
                break
        updated_count = 0
        legends_count = 0
        legends_list = []
        missing_count = 0
        missing_list = []
        munitorum_units = munitorum_faction['units'] if munitorum_faction else []
        # Créer une liste des noms de datasheets dans le JSON
        munitorum_unit_names = [unit['name'] for unit in munitorum_units]
        # Mettre à jour chaque datasheet
        for datasheet in archive_data.get('datasheets', []):
            datasheet_name = datasheet['name']
            munitorum_unit = find_matching_datasheet(datasheet_name, munitorum_units)
            if munitorum_unit:
                update_datasheet_points(datasheet, munitorum_unit)
                updated_count += 1
            else:
                if 'legends' not in datasheet:
                    datasheet['legends'] = True
                    legends_count += 1
                    legends_list.append(datasheet_name)
        # Vérifier les datasheets du JSON qui ne sont pas dans l'archive
        archive_datasheet_names = [ds['name'] for ds in archive_data.get('datasheets', [])]
        for unit_name in munitorum_unit_names:
            found = False
            for archive_name in archive_datasheet_names:
                if normalize_name(unit_name) == normalize_name(archive_name) or normalize_name(unit_name) in normalize_name(archive_name) or normalize_name(archive_name) in normalize_name(unit_name):
                    found = True
                    break
            if not found:
                missing_count += 1
                missing_list.append(unit_name)
        # Sauvegarder le fichier
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(archive_data, f, indent=2, ensure_ascii=False)
        print(f"{updated_count} datasheets mises à jour dans {archive_file.name}")
        if legends_count > 0:
            print(f"{legends_count} datasheets marquées comme legends dans {archive_file.name}")
            for name in legends_list:
                print(f"  - {name}")
        if missing_count > 0:
            print(f"{missing_count} datasheets du JSON manquantes dans {archive_file.name}")
            for name in missing_list:
                print(f"  - {name}")
        all_legends.extend([(archive_file.name, name) for name in legends_list])
        all_missing.extend([(archive_file.name, name) for name in missing_list])
    print("\nMise à jour terminée!")
    if all_legends:
        print(f"\n=== LISTE COMPLÈTE DES DATASHEETS LEGENDS ===")
        print(f"Total: {len(all_legends)} datasheets marquées comme legends")
        legends_by_faction = {}
        for faction, name in all_legends:
            if faction not in legends_by_faction:
                legends_by_faction[faction] = []
            legends_by_faction[faction].append(name)
        for faction in sorted(legends_by_faction.keys()):
            print(f"{faction}:")
            for name in sorted(legends_by_faction[faction]):
                print(f"  - {name}")
            print()
    else:
        print("\nAucune datasheet marquée comme legends.")
    if all_missing:
        print(f"\n=== LISTE COMPLÈTE DES DATASHEETS MANQUANTES ===")
        print(f"Total: {len(all_missing)} datasheets du JSON manquantes")
        missing_by_faction = {}
        for faction, name in all_missing:
            if faction not in missing_by_faction:
                missing_by_faction[faction] = []
            missing_by_faction[faction].append(name)
        for faction in sorted(missing_by_faction.keys()):
            print(f"{faction}:")
            for name in sorted(missing_by_faction[faction]):
                print(f"  - {name}")
            print()
    else:
        print("\nAucune datasheet du JSON manquante.")

if __name__ == "__main__":
    main() 