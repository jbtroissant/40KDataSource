#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour mettre à jour les points des datasheets à partir du fichier bds.txt
"""

import json
import re
import os
from pathlib import Path
import unicodedata

def parse_bds_file(file_path):
    """
    Parse le fichier bds.txt et extrait les points pour chaque faction
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Diviser le contenu par les sections CODEX/INDEX
    sections = re.split(r'CODEX:|INDEX:', content)
    
    faction_points = {}
    current_faction = None
    
    for section in sections[1:]:  # Ignorer la première section vide
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        # Extraire le nom de la faction de la première ligne
        faction_name = lines[0].strip()
        
        # Mapper les noms de faction vers les noms de fichiers
        faction_mapping = {
            'ADEPTA SORORITAS': 'adeptasororitas',
            'ADEPTUS CUSTODES': 'adeptuscustodes',
            'ADEPTUS MECHANICUS': 'adeptusmechanicus',
            'AELDARI': 'aeldari',
            'AGENTS OF THE IMPERIUM': 'agents',
            'ASTRA MILITARUM': 'astramilitarum',
            'BLACK TEMPLARS': 'blacktemplar',
            'BLOOD ANGELS': 'bloodangels',
            'CHAOS SPACE MARINES': 'chaos_spacemarines',
            'CHAOS DAEMONS': 'chaosdaemons',
            'CHAOS KNIGHTS': 'chaosknights',
            'DARK ANGELS': 'darkangels',
            'DEATH GUARD': 'deathguard',
            'DEATHWATCH': 'Deathwatch',
            'DRUKHARI': 'drukhari',
            'EMPEROR\'S CHILDREN': 'emperors_children',
            'GREY KNIGHTS': 'greyknights',
            'GENESTEALER CULTS': 'gsc',
            'IMPERIAL KNIGHTS': 'imperialknights',
            'NECRONS': 'necrons',
            'ORKS': 'orks',
            'SPACE MARINES': 'space_marines',
            'SPACE WOLVES': 'spacewolves',
            'TAU EMPIRE': 'tau',
            'THOUSAND SONS': 'thousandsons',
            'TYRANIDS': 'tyranids',
            'VOTANN': 'votann',
            'WORLD EATERS': 'worldeaters'
        }
        
        file_name = faction_mapping.get(faction_name)
        if not file_name:
            print(f"Faction non reconnue: {faction_name}")
            continue
            
        faction_points[file_name] = {}
        
        # Parser les points pour cette faction
        i = 1
        datasheet_count = 0
        current_datasheet = None
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith('DETACHMENT ENHANCEMENTS') or line.startswith('FORGE WORLD'):
                break
            
            # Vérifier si c'est une option avec "+"
            option_match = re.match(r'^(.+?)\s+.*?\+(\d+)\s+pts$', line)
            if option_match:
                option_name = option_match.group(1).strip()
                points = option_match.group(2)
                
                # Nettoyer le nom de l'option
                option_name = re.sub(r'[^\w\s\-\.]', '', option_name).strip()
                
                # Si on a une datasheet courante, ajouter l'option à cette datasheet
                if current_datasheet and current_datasheet in faction_points[file_name]:
                    faction_points[file_name][current_datasheet].append({
                        'models': '1',
                        'points': points,
                        'is_option': True,
                        'option_name': option_name
                    })
                i += 1
                continue
            
            # Vérifier si la ligne suivante contient les points
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                
                # Pattern pour matcher les points: "X models" + "Y pts"
                match = re.match(r'^(\d+)\s+models?\s+.*?(\d+)\s+pts$', next_line)
                if match:
                    datasheet_name = line
                    models = match.group(1)
                    points = match.group(2)
                    
                    # Nettoyer le nom de la datasheet
                    datasheet_name = re.sub(r'[^\w\s\-\.]', '', datasheet_name).strip()
                    current_datasheet = datasheet_name
                    
                    if datasheet_name not in faction_points[file_name]:
                        faction_points[file_name][datasheet_name] = []
                    
                    # Ajouter cette entrée de points
                    faction_points[file_name][datasheet_name].append({
                        'models': models,
                        'points': points,
                        'is_option': False
                    })
                    
                    # Vérifier s'il y a d'autres entrées de points pour la même datasheet
                    j = i + 2
                    while j < len(lines):
                        next_next_line = lines[j].strip()
                        if not next_next_line:
                            break
                        
                        # Si c'est une nouvelle datasheet, arrêter
                        if not re.match(r'^\d+\s+models?\s+.*?\d+\s+pts$', next_next_line):
                            break
                        
                        # C'est une autre entrée de points pour la même datasheet
                        match2 = re.match(r'^(\d+)\s+models?\s+.*?(\d+)\s+pts$', next_next_line)
                        if match2:
                            models2 = match2.group(1)
                            points2 = match2.group(2)
                            
                            faction_points[file_name][datasheet_name].append({
                                'models': models2,
                                'points': points2,
                                'is_option': False
                            })
                            j += 1
                        else:
                            break
                    
                    i = j
                    datasheet_count += 1
                else:
                    i += 1
            else:
                i += 1
    
    return faction_points

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

def find_matching_datasheet(datasheet_name, archive_data):
    """
    Trouve la datasheet correspondante dans les données d'archive
    """
    clean_bds_name = normalize_name(datasheet_name)
    for datasheet in archive_data.get('datasheets', []):
        clean_archive_name = normalize_name(datasheet['name'])
        if clean_archive_name == clean_bds_name:
            return datasheet
        # Correspondance partielle
        if clean_bds_name in clean_archive_name or clean_archive_name in clean_bds_name:
            return datasheet
    return None

def update_datasheet_points(datasheet, new_points_data):
    """
    Met à jour les points d'une datasheet en remplaçant complètement les points existants
    """
    # Remplacer complètement le tableau points
    datasheet['points'] = []
    
    # Ajouter les nouveaux points
    for point_data in new_points_data:
        if point_data.get('is_option', False):
            # C'est une option, ajouter avec un keyword
            new_point = {
                "cost": point_data['points'],
                "keyword": "option",
                "models": point_data['models'],
                "active": True
            }
            datasheet['points'].append(new_point)
        else:
            # C'est un point de base
            new_point = {
                "cost": point_data['points'],
                "keyword": None,
                "models": point_data['models'],
                "active": True
            }
            datasheet['points'].append(new_point)

def process_faction_file(faction_file, faction_points):
    """
    Traite un fichier de faction et met à jour les points
    """
    if not os.path.exists(faction_file):
        print(f"Fichier non trouvé: {faction_file}")
        return
    
    print(f"Traitement de {faction_file}...")
    
    with open(faction_file, 'r', encoding='utf-8') as f:
        archive_data = json.load(f)
    
    faction_name = os.path.basename(faction_file).replace('.json', '')
    faction_data = faction_points.get(faction_name, {})
    
    updated_count = 0
    
    for datasheet_name, points_data in faction_data.items():
        datasheet = find_matching_datasheet(datasheet_name, archive_data)
        if datasheet:
            update_datasheet_points(datasheet, points_data)
            updated_count += 1
            print(f"  Mis à jour: {datasheet_name}")
        else:
            print(f"  Non trouvé: {datasheet_name}")
    
    # Sauvegarder les modifications
    with open(faction_file, 'w', encoding='utf-8') as f:
        json.dump(archive_data, f, indent=2, ensure_ascii=False)
    
    print(f"  {updated_count} datasheets mises à jour dans {faction_file}")

def main():
    """
    Fonction principale
    """
    bds_file = "Input Points/bds.txt"
    archive_dir = "archive"
    
    if not os.path.exists(bds_file):
        print(f"Fichier {bds_file} non trouvé!")
        return
    
    print("Parsing du fichier bds.txt...")
    faction_points = parse_bds_file(bds_file)
    
    print(f"Factions trouvées: {list(faction_points.keys())}")
    
    # Traiter chaque faction
    for faction_name in faction_points.keys():
        faction_file = os.path.join(archive_dir, f"{faction_name}.json")
        process_faction_file(faction_file, faction_points)
    
    print("Mise à jour terminée!")

if __name__ == "__main__":
    main() 