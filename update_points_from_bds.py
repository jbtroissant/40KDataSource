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

# Mapping des noms de fichiers archive vers les noms de factions du bds.txt
FACTION_FILENAME_TO_BDS = {
    "adeptasororitas": "ADEPTA SORORITAS",
    "adeptuscustodes": "ADEPTUS CUSTODES",
    "adeptusmechanicus": "ADEPTUS MECHANICUS",
    "aeldari": "AELDARI",
    "agents": "AGENTS OF THE IMPERIUM",
    "astramilitarum": "ASTRA MILITARUM",
    "blacktemplar": "BLACK TEMPLARS",
    "bloodangels": "BLOOD ANGELS",
    "chaos_spacemarines": "CHAOS SPACE MARINES",
    "chaosdaemons": "CHAOS DAEMONS",
    "chaosknights": "CHAOS KNIGHTS",
    "core": "CORE",
    "darkangels": "DARK ANGELS",
    "deathguard": "DEATH GUARD",
    "Deathwatch": "DEATHWATCH",
    "drukhari": "DRUKHARI",
    "emperors_children": "EMPEROR\u2019S CHILDREN",
    "greyknights": "GREY KNIGHTS",
    "gsc": "GENESTEALER CULTS",
    "imperialknights": "IMPERIAL KNIGHTS",
    "necrons": "NECRONS",
    "orks": "ORKS",
    "space_marines": "SPACE MARINES",
    "spacewolves": "SPACE WOLVES",
    "tau": "T\u2019AU EMPIRE",
    "thousandsons": "THOUSAND SONS",
    "tyranids": "TYRANIDS",
    "unaligned": "UNALIGNED",
    "votann": "LEAGUES OF VOTANN",
    "worldeaters": "WORLD EATERS",
}

def parse_bds_file(file_path):
    """
    Parse le fichier bds.txt et extrait les points par faction
    """
    faction_points = {}
    current_faction = None
    current_datasheet = None
    waiting_for_faction_name = False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Détecter une nouvelle faction (ligne commençant par CODEX, INDEX, ou AGENTS OF THE IMPERIUM)
            if line.startswith('CODEX') or line.startswith('INDEX') or line == 'AGENTS OF THE IMPERIUM':
                # Extraire le nom de faction en ignorant les préfixes
                faction_name = line
                if line.startswith('CODEX SUPPLEMENT: '):
                    faction_name = line.replace('CODEX SUPPLEMENT: ', '')
                elif line.startswith('CODEX: '):
                    faction_name = line.replace('CODEX: ', '')
                elif line.startswith('INDEX: '):
                    faction_name = line.replace('INDEX: ', '')
                elif line == 'AGENTS OF THE IMPERIUM':
                    faction_name = 'AGENTS OF THE IMPERIUM'
                
                # Si c'est juste "CODEX SUPPLEMENT:" sans nom, on attend la ligne suivante
                if faction_name == 'CODEX SUPPLEMENT:':
                    waiting_for_faction_name = True
                    continue
                
                # Ignorer les lignes vides après les préfixes
                if not faction_name:
                    continue
                
                current_faction = faction_name
                faction_points[current_faction] = {}
                print(f"Faction trouvée: {current_faction}")
                waiting_for_faction_name = False
                continue
            
            # Si on attend le nom de faction après CODEX SUPPLEMENT:
            if waiting_for_faction_name:
                current_faction = line
                faction_points[current_faction] = {}
                print(f"Faction trouvée: {current_faction}")
                waiting_for_faction_name = False
                continue
            
            # Ignorer les lignes de détachement et d'amélioration
            if (line.startswith('DETACHMENT') or 
                line.startswith('FORGE WORLD') or 
                line.startswith('LEGIONS OF') or
                line.startswith('SCINTILLATING') or
                line.startswith('AUXILIARY') or
                line.startswith('EXPERIMENTAL') or
                line.startswith('KAUYON') or
                line.startswith('KROOT') or
                line.startswith('MONT\'KA') or
                line.startswith('RETALIATION') or
                line.startswith('CARNIVAL') or
                line.startswith('COTERIE') or
                line.startswith('MERCURIAL') or
                line.startswith('PEERLESS') or
                line.startswith('RAPID') or
                line.startswith('SLAANESH\'S') or
                line.startswith('BIOSANCTIC') or
                line.startswith('BROOD') or
                line.startswith('FINAL') or
                line.startswith('HOST') or
                line.startswith('OUTLANDER') or
                line.startswith('XENOCREED') or
                line.startswith('AURIC') or
                line.startswith('LIONS') or
                line.startswith('NULL') or
                line.startswith('SHIELD') or
                line.startswith('ARMY') or
                line.startswith('BRINGERS') or
                line.startswith('CHAMPIONS') or
                line.startswith('HALLOWED') or
                line.startswith('PENITENT')):
                current_faction = None
                continue
            
            # Ignorer la section "EVERY MODEL HAS IMPERIUM KEYWORD" pour les agents
            if line == 'EVERY MODEL HAS IMPERIUM KEYWORD':
                current_faction = None
                continue
            
            # Si on n'a pas de faction courante, ignorer la ligne
            if not current_faction:
                continue
            
            # Détecter une datasheet (ligne qui ne contient pas de points)
            if not re.search(r'\d+\s+pts', line) and not line.startswith('+'):
                # C'est probablement une datasheet
                datasheet_name = line
                current_datasheet = datasheet_name
                faction_points[current_faction][datasheet_name] = {
                    'base_points': None,
                    'options': []
                }
                continue
            
            # Détecter les points de base ou les options
            if re.search(r'\d+\s+pts', line):
                if line.startswith('+'):
                    # C'est une option
                    if current_datasheet:
                        faction_points[current_faction][current_datasheet]['options'].append(line)
                else:
                    # C'est probablement les points de base
                    if current_datasheet:
                        # Extraire les points
                        match = re.search(r'(\d+)\s+pts', line)
                        if match:
                            points = int(match.group(1))
                            faction_points[current_faction][current_datasheet]['base_points'] = points
    
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

def update_datasheet_points(datasheet, points_data):
    """
    Met à jour les points d'une datasheet avec les nouvelles données
    """
    # Supprimer les anciennes options
    if 'options' in datasheet:
        datasheet['options'] = []
    
    # Mettre à jour les points de base
    if points_data.get('base_points') is not None:
        # Pour les agents, la structure des points est différente
        if 'points' in datasheet and isinstance(datasheet['points'], list):
            # Structure avec liste de points (agents.json)
            if datasheet['points']:
                datasheet['points'][0]['cost'] = str(points_data['base_points'])
        else:
            # Structure simple avec points directement
            datasheet['points'] = points_data['base_points']
    
    # Ajouter les nouvelles options
    for option in points_data.get('options', []):
        # Extraire le nom et les points de l'option
        option_match = re.match(r'^(.+?)\s+\+(\d+)\s+pts$', option)
        if option_match:
            option_name = option_match.group(1).strip()
            option_points = int(option_match.group(2))
            
            datasheet['options'].append({
                'name': option_name,
                'points': option_points
            })

def process_faction_file(faction_file, faction_points):
    """
    Traite un fichier de faction et met à jour les points
    """
    if not os.path.exists(faction_file):
        print(f"Fichier {faction_file} non trouvé!")
        return [], []
    
    print(f"Traitement de {faction_file}...")
    
    # Charger le fichier JSON
    with open(faction_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    faction_name = os.path.basename(faction_file).replace('.json', '')
    # Utiliser le mapping pour obtenir le nom du bds.txt
    bds_faction_name = FACTION_FILENAME_TO_BDS.get(faction_name, faction_name)
    updated_count = 0
    missing_count = 0
    missing_list = []
    
    if bds_faction_name not in faction_points:
        print(f"Faction {bds_faction_name} non trouvée dans le bds.txt")
        return [], []
    
    # Créer une liste des noms de datasheets dans l'archive
    archive_datasheets = [datasheet['name'] for datasheet in data.get('datasheets', [])]
    
    # Traiter chaque datasheet de l'archive
    for datasheet in data.get('datasheets', []):
        datasheet_name = datasheet['name']
        
        # Chercher la correspondance dans le bds.txt
        matching_data = None
        for bds_name, points_data in faction_points[bds_faction_name].items():
            # Vérifier si cette datasheet correspond au nom du bds
            clean_bds_name = normalize_name(bds_name)
            clean_datasheet_name = normalize_name(datasheet_name)
            if clean_datasheet_name == clean_bds_name or clean_bds_name in clean_datasheet_name or clean_datasheet_name in clean_bds_name:
                matching_data = points_data
                break
        
        if matching_data:
            # Datasheet trouvée dans le bds.txt, mettre à jour les points
            update_datasheet_points(datasheet, matching_data)
            print(f"  Mis à jour: {datasheet_name}")
            updated_count += 1
        # Si pas trouvée dans le bds.txt, on ne fait rien (pas de passage automatique à legends)
    
    # Vérifier les datasheets du bds.txt qui ne sont pas dans l'archive
    for bds_name in faction_points[bds_faction_name].keys():
        found = False
        for archive_name in archive_datasheets:
            clean_bds_name = normalize_name(bds_name)
            clean_archive_name = normalize_name(archive_name)
            if clean_archive_name == clean_bds_name or clean_bds_name in clean_archive_name or clean_archive_name in clean_bds_name:
                found = True
                break
        
        if not found:
            missing_count += 1
            missing_list.append(bds_name)
            print(f"  Manquant dans archive: {bds_name}")
    
    # Sauvegarder le fichier seulement si des modifications ont été apportées
    if updated_count > 0:
        with open(faction_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"{updated_count} datasheets mises à jour dans {faction_file}")
    if missing_count > 0:
        print(f"{missing_count} datasheets du bds.txt manquantes dans {faction_file}")
        print("  Liste des datasheets manquantes:")
        for name in missing_list:
            print(f"    - {name}")
    
    return [], missing_list

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
    print("\nMapping des factions:")
    for filename, bds_name in FACTION_FILENAME_TO_BDS.items():
        if bds_name in faction_points:
            print(f"  ✅ {filename} -> {bds_name}")
        else:
            print(f"  ❌ {filename} -> {bds_name} (non trouvée)")
    
    # Traiter chaque fichier de faction
    all_missing = []
    for faction_name in faction_points.keys():
        # Utiliser le mapping inverse pour trouver le nom de fichier
        faction_file = None
        for filename, bds_name in FACTION_FILENAME_TO_BDS.items():
            if bds_name == faction_name:
                faction_file = os.path.join(archive_dir, f"{filename}.json")
                break
        
        if not faction_file:
            print(f"❌ Aucun fichier trouvé pour la faction: {faction_name}")
            continue
            
        if not os.path.exists(faction_file):
            print(f"❌ Fichier {faction_file} non trouvé!")
            continue
            
        print(f"✅ Traitement de {faction_file} pour {faction_name}")
        legends_list, missing_list = process_faction_file(faction_file, faction_points)
        if missing_list:
            all_missing.extend([(faction_name, name) for name in missing_list])
    
    print("\nMise à jour terminée!")
    
    # Afficher la liste complète des datasheets manquantes
    if all_missing:
        print(f"\n=== LISTE COMPLÈTE DES DATASHEETS MANQUANTES ===")
        print(f"Total: {len(all_missing)} datasheets du bds.txt manquantes")
        print()
        
        # Grouper par faction
        missing_by_faction = {}
        for faction, name in all_missing:
            if faction not in missing_by_faction:
                missing_by_faction[faction] = []
            missing_by_faction[faction].append(name)
        
        for faction in sorted(missing_by_faction.keys()):
            print(f"{faction.upper()}:")
            for name in sorted(missing_by_faction[faction]):
                print(f"  - {name}")
            print()
    else:
        print("\nAucune datasheet du bds.txt manquante.")

if __name__ == "__main__":
    main() 