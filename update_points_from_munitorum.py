#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour mettre à jour les points des unités dans les fichiers d'archive
avec les données du fichier munitorum_data_final.json
"""

import json
import os
import re
from pathlib import Path

def normalize_faction_name(name):
    """Normalise le nom de faction pour la correspondance avec les fichiers d'archive"""
    # Mapping des noms de factions vers les noms de fichiers d'archive
    faction_mapping = {
        "ADEPTA SORORITAS": "adeptasororitas",
        "ADEPTUS CUSTODES": "adeptuscustodes", 
        "ADEPTUS MECHANICUS": "adeptusmechanicus",
        "AELDARI": "aeldari",
        "AGENTS OF THE IMPERIUM": "agents",
        "ASTRA MILITARUM": "astramilitarum",
        "BLACK TEMPLARS": "blacktemplar",
        "BLOOD ANGELS": "bloodangels",
        "CHAOS SPACE MARINES": "chaos_spacemarines",
        "CHAOS DAEMONS": "chaosdaemons",
        "CHAOS KNIGHTS": "chaosknights",
        "CORE": "core",
        "DARK ANGELS": "darkangels",
        "DEATH GUARD": "deathguard",
        "DEATHWATCH": "Deathwatch",
        "DRUKHARI": "drukhari",
        "EMPEROR'S CHILDREN": "emperors_children",
        "GREY KNIGHTS": "greyknights",
        "GENESTEALER CULTS": "gsc",
        "IMPERIAL KNIGHTS": "imperialknights",
        "LEAGUES OF VOTANN": "votann",
        "NECRONS": "necrons",
        "ORKS": "orks",
        "SPACE MARINES": "space_marines",
        "SPACE WOLVES": "spacewolves",
        "TAU EMPIRE": "tau",
        "THOUSAND SONS": "thousandsons",
        "TYRANIDS": "tyranids",
        "UNALIGNED": "unaligned",
        "VOTANN": "votann",
        "WORLD EATERS": "worldeaters",
        # Ajout des noms avec "CODEX SUPPLEMENT:" et "IMPERIAL AGENTS"
        "CODEX SUPPLEMENT: BLOOD ANGELS": "bloodangels",
        "CODEX SUPPLEMENT: DARK ANGELS": "darkangels",
        "IMPERIAL AGENTS": "agents",
        # Ajout des variantes avec apostrophes typographiques
        "EMPEROR'S CHILDREN": "emperors_children",
        "T'AU EMPIRE": "tau"
    }
    
    # Normalisation pour gérer toutes les apostrophes Unicode
    normalized_name = name.upper()
    for apostrophe in ["’", "‘", "‛", "′", "ʻ", "ʼ", "ʽ", "ʾ", "ʿ", "ˈ", "ˊ", "ˋ", "˴", "`", "´", "ʹ", "ʺ", "'", "＇"]:
        normalized_name = normalized_name.replace(apostrophe, "'")
    
    # Essayer d'abord avec le mapping exact
    if normalized_name in faction_mapping:
        return faction_mapping[normalized_name]
    
    # Si pas trouvé, essayer avec la normalisation par défaut
    fallback_name = normalized_name.lower().replace(" ", "").replace("'", "")
    return faction_mapping.get(normalized_name, fallback_name)

def normalize_unit_name(name):
    """Normalise le nom d'unité pour la correspondance"""
    # Supprime les caractères spéciaux et met en minuscules
    normalized = re.sub(r'[^\w\s]', '', name.lower())
    return normalized.strip()

def find_matching_unit(unit_name, datasheets):
    """Trouve l'unité correspondante dans les datasheets"""
    normalized_search = normalize_unit_name(unit_name)
    
    for datasheet in datasheets:
        datasheet_name = datasheet.get('name', '')
        normalized_datasheet = normalize_unit_name(datasheet_name)
        
        # Correspondance exacte
        if normalized_search == normalized_datasheet:
            return datasheet
        
        # Correspondance partielle (pour gérer les variations de noms)
        if normalized_search in normalized_datasheet or normalized_datasheet in normalized_search:
            return datasheet
    
    return None

def update_points_in_archive():
    """Met à jour les points dans les fichiers d'archive"""
    
    # Charger les données du munitorum
    print("Chargement du fichier munitorum_data_final.json...")
    with open('munitorum_data_final.json', 'r', encoding='utf-8') as f:
        munitorum_data = json.load(f)
    
    archive_dir = Path('archive')
    if not archive_dir.exists():
        print("Erreur: Le dossier 'archive' n'existe pas!")
        return
    
    total_updates = 0
    total_factions = 0
    
    # Parcourir chaque faction dans les données du munitorum
    for faction_data in munitorum_data.get('factions', []):
        faction_name = faction_data.get('name', '')
        units_data = faction_data.get('units', [])
        
        if not faction_name or not units_data:
            continue
        
        # Trouver le fichier d'archive correspondant
        archive_filename = normalize_faction_name(faction_name) + '.json'
        archive_path = archive_dir / archive_filename
        
        if not archive_path.exists():
            print(f"⚠️  Fichier d'archive non trouvé pour {faction_name}: {archive_filename}")
            continue
        
        print(f"\n📁 Traitement de {faction_name} ({archive_filename})...")
        
        # Charger le fichier d'archive
        try:
            with open(archive_path, 'r', encoding='utf-8') as f:
                archive_data = json.load(f)
        except Exception as e:
            print(f"❌ Erreur lors du chargement de {archive_filename}: {e}")
            continue
        
        datasheets = archive_data.get('datasheets', [])
        faction_updates = 0
        
        # Parcourir chaque unité de la faction
        for unit_data in units_data:
            unit_name = unit_data.get('name', '')
            new_costs = unit_data.get('costs', [])
            
            if not unit_name or not new_costs:
                continue
            
            # Trouver l'unité correspondante dans les datasheets
            matching_datasheet = find_matching_unit(unit_name, datasheets)
            
            if matching_datasheet:
                # Mettre à jour les points
                old_points = matching_datasheet.get('points', [])
                matching_datasheet['points'] = new_costs
                
                print(f"  ✅ {unit_name}: {len(old_points)} → {len(new_costs)} coûts")
                faction_updates += 1
            else:
                print(f"  ❌ {unit_name}: unité non trouvée dans les datasheets")
        
        # Sauvegarder le fichier d'archive mis à jour
        if faction_updates > 0:
            try:
                with open(archive_path, 'w', encoding='utf-8') as f:
                    json.dump(archive_data, f, indent=2, ensure_ascii=False)
                print(f"💾 {faction_name}: {faction_updates} unités mises à jour")
                total_updates += faction_updates
                total_factions += 1
            except Exception as e:
                print(f"❌ Erreur lors de la sauvegarde de {archive_filename}: {e}")
        else:
            print(f"ℹ️  {faction_name}: aucune mise à jour nécessaire")
    
    print(f"\n🎉 Mise à jour terminée!")
    print(f"📊 Total: {total_updates} unités mises à jour dans {total_factions} factions")

if __name__ == "__main__":
    print("🔄 Début de la mise à jour des points depuis munitorum_data_final.json")
    update_points_in_archive() 