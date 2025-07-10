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

# Icônes pour améliorer la lisibilité
ICONS = {
    "success": "✅",
    "warning": "⚠️",
    "error": "❌",
    "info": "ℹ️",
    "processing": "🔄",
    "file": "📁",
    "check": "✓",
    "skip": "⏭️"
}

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
        "EMPERORS CHILDREN": "emperors_children",  # Variante sans apostrophe
        "GREY KNIGHTS": "greyknights",
        "GENESTEALER CULTS": "gsc",
        "IMPERIAL KNIGHTS": "imperialknights",
        "LEAGUES OF VOTANN": "votann",
        "NECRONS": "necrons",
        "ORKS": "orks",
        "SPACE MARINES": "space_marines",
        "SPACE WOLVES": "spacewolves",
        "TAU EMPIRE": "tau",
        "T'AU EMPIRE": "tau",  # Variante avec apostrophe typographique
        "THOUSAND SONS": "thousandsons",
        "TYRANIDS": "tyranids",
        "UNALIGNED": "unaligned",
        "VOTANN": "votann",
        "WORLD EATERS": "worldeaters",
        # Ajout des noms avec "CODEX SUPPLEMENT:" et "IMPERIAL AGENTS"
        "CODEX SUPPLEMENT: BLOOD ANGELS": "bloodangels",
        "CODEX SUPPLEMENT: DARK ANGELS": "darkangels",
        "IMPERIAL AGENTS": "agents"
    }
    
    # Normalisation pour gérer toutes les apostrophes Unicode
    normalized_name = name.upper()
    for apostrophe in ["'", "'", "‛", "′", "ʻ", "ʼ", "ʽ", "ʾ", "ʿ", "ˈ", "ˊ", "ˋ", "˴", "`", "´", "ʹ", "ʺ", "'", "＇"]:
        normalized_name = normalized_name.replace(apostrophe, "'")
    
    # Essayer d'abord avec le mapping exact
    if normalized_name in faction_mapping:
        return faction_mapping[normalized_name]
    
    # Cas spécial pour T'AU EMPIRE qui peut avoir différentes variantes d'apostrophe
    if "TAU EMPIRE" in normalized_name or "T'AU EMPIRE" in normalized_name:
        return "tau"
    
    # Si pas trouvé, essayer avec la normalisation par défaut
    fallback_name = normalized_name.lower().replace(" ", "").replace("'", "")
    return faction_mapping.get(normalized_name, fallback_name)

def normalize_unit_name(name):
    """Normalise le nom d'unité pour la correspondance"""
    # Supprime les caractères spéciaux et met en minuscules
    normalized = re.sub(r'[^\w\s]', '', name.lower())
    return normalized.strip()

def find_matching_unit(unit_name, datasheets):
    """Trouve l'unité correspondante dans les datasheets avec une correspondance plus précise"""
    normalized_search = normalize_unit_name(unit_name)
    
    # Liste pour stocker toutes les correspondances trouvées
    matches = []
    
    for datasheet in datasheets:
        datasheet_name = datasheet.get('name', '')
        normalized_datasheet = normalize_unit_name(datasheet_name)
        
        # Correspondance exacte
        if normalized_search == normalized_datasheet:
            matches.append((datasheet, 100))  # Score parfait
        # Correspondance partielle
        elif normalized_search in normalized_datasheet or normalized_datasheet in normalized_search:
            # Calculer un score de similarité
            score = 0
            if normalized_search in normalized_datasheet:
                score += 50
            if normalized_datasheet in normalized_search:
                score += 50
            # Bonus pour les mots communs
            search_words = set(normalized_search.split())
            datasheet_words = set(normalized_datasheet.split())
            common_words = search_words.intersection(datasheet_words)
            score += len(common_words) * 10
            matches.append((datasheet, score))
    
    if not matches:
        return None
    
    # Trier par score et retourner le meilleur match
    matches.sort(key=lambda x: x[1], reverse=True)
    best_match = matches[0]
    
    # Si il y a plusieurs matches avec le même score, afficher un warning
    if len(matches) > 1 and matches[0][1] == matches[1][1]:
        print(f"{ICONS['warning']} Plusieurs correspondances trouvées pour '{unit_name}':")
        for match, score in matches[:3]:  # Afficher les 3 premiers
            print(f"    - {match.get('name', 'Unknown')} (score: {score})")
    
    return best_match[0]

def update_points_in_archive():
    """Met à jour les points dans les fichiers d'archive"""
    
    # Charger les données du munitorum
    print(f"{ICONS['info']} Chargement du fichier munitorum_data_final.json...")
    with open('munitorum_data_final.json', 'r', encoding='utf-8') as f:
        munitorum_data = json.load(f)
    
    archive_dir = Path('archive')
    if not archive_dir.exists():
        print(f"{ICONS['error']} Le dossier 'archive' n'existe pas!")
        return
    
    total_updates = 0
    total_factions = 0
    total_not_found = 0
    
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
            print(f"{ICONS['warning']} Fichier d'archive non trouvé pour {faction_name}: {archive_filename}")
            continue
        
        print(f"\n{ICONS['file']} Traitement de {faction_name} ({archive_filename})...")
        
        # Charger le fichier d'archive
        try:
            with open(archive_path, 'r', encoding='utf-8') as f:
                archive_data = json.load(f)
        except Exception as e:
            print(f"{ICONS['error']} Erreur lors du chargement de {archive_filename}: {e}")
            continue
        
        datasheets = archive_data.get('datasheets', [])
        faction_updates = 0
        faction_not_found = 0
        
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
                old_cost = old_points[0].get('cost', 'N/A') if old_points else 'N/A'
                new_cost = new_costs[0].get('cost', 'N/A') if new_costs else 'N/A'
                
                matching_datasheet['points'] = new_costs
                
                print(f"  {ICONS['success']} {unit_name}: {old_cost} → {new_cost}")
                faction_updates += 1
            else:
                print(f"  {ICONS['error']} {unit_name}: unité non trouvée dans les datasheets")
                faction_not_found += 1
        
        # Sauvegarder le fichier d'archive mis à jour
        if faction_updates > 0:
            try:
                with open(archive_path, 'w', encoding='utf-8') as f:
                    json.dump(archive_data, f, indent=2, ensure_ascii=False)
                print(f"{ICONS['success']} {faction_name}: {faction_updates} unités mises à jour")
                total_updates += faction_updates
                total_factions += 1
            except Exception as e:
                print(f"{ICONS['error']} Erreur lors de la sauvegarde de {archive_filename}: {e}")
        else:
            print(f"{ICONS['skip']} {faction_name}: aucune mise à jour nécessaire")
        
        if faction_not_found > 0:
            total_not_found += faction_not_found
    
    print(f"\n{ICONS['success']} Mise à jour terminée!")
    print(f"{ICONS['info']} Total: {total_updates} unités mises à jour dans {total_factions} factions")
    if total_not_found > 0:
        print(f"{ICONS['warning']} {total_not_found} unités non trouvées")

if __name__ == "__main__":
    print(f"{ICONS['processing']} Début de la mise à jour des points depuis munitorum_data_final.json")
    update_points_in_archive() 