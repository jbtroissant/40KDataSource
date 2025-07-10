#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour ajouter la valeur "compo_structure" à chaque datasheet
en analysant la composition et en générant des UUIDs pour les stats.
"""

import json
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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

def generate_uuid() -> str:
    """Génère un UUID v4."""
    return str(uuid.uuid4())

def parse_composition_entry(entry: str) -> Tuple[str, int, int, int]:
    """
    Parse une entrée de composition et retourne (nom, count, min, max).
    
    Exemples:
    "1 Marneus Calgar – EPIC HERO" -> ("Marneus Calgar", 1, 1, 1)
    "2-5 Outriders" -> ("Outriders", 2, 2, 5)
    "0-1 Invader ATV" -> ("Invader ATV", 0, 0, 1)
    """
    # Nettoyer l'entrée
    entry = entry.strip()
    
    # Pattern pour extraire le nombre et le nom
    # Supporte: "1 Nom", "2-5 Nom", "0-1 Nom", "1 Nom – SUFFIX"
    pattern = r'^(\d+)(?:-(\d+))?\s+(.+?)(?:\s*–\s*[^–]+)?$'
    match = re.match(pattern, entry)
    
    if not match:
        print(f"{ICONS['warning']} Impossible de parser l'entrée de composition: {entry}")
        return (entry, 1, 1, 1)
    
    min_count = int(match.group(1))
    max_count = int(match.group(2)) if match.group(2) else min_count
    name = match.group(3).strip()
    
    # Le count par défaut est le min
    count = min_count
    
    return (name, count, min_count, max_count)

def find_matching_stat_name(unit_name: str, stats: List[Dict]) -> Optional[str]:
    """
    Trouve le nom de stat correspondant au nom d'unité.
    
    Stratégies de correspondance:
    1. Correspondance exacte
    2. Correspondance sans pluriel (Outriders -> Outrider)
    3. Correspondance partielle (Outrider Sergeant -> Outrider)
    """
    # Nettoyer le nom
    clean_unit_name = unit_name.strip()
    
    # 1. Correspondance exacte
    for stat in stats:
        if stat.get('name', '').strip() == clean_unit_name:
            return stat.get('name')
    
    # 2. Correspondance sans pluriel
    if clean_unit_name.endswith('s'):
        singular_name = clean_unit_name[:-1]
        for stat in stats:
            if stat.get('name', '').strip() == singular_name:
                return stat.get('name')
    
    # 3. Correspondance partielle (pour les cas comme "Outrider Sergeant" -> "Outrider")
    for stat in stats:
        stat_name = stat.get('name', '').strip()
        if stat_name in clean_unit_name or clean_unit_name in stat_name:
            return stat_name
    
    # 4. Correspondance avec le nom de la datasheet (fallback)
    return None

def ensure_stat_has_id(stat: Dict) -> str:
    """S'assure qu'une stat a un ID, en génère un si nécessaire."""
    if 'id' not in stat:
        stat['id'] = generate_uuid()
    return stat['id']

def create_compo_structure(composition: List[str], stats: List[Dict]) -> List[Dict]:
    """
    Crée la structure compo_structure à partir de la composition et des stats.
    """
    compo_structure = []
    
    for entry in composition:
        name, count, min_count, max_count = parse_composition_entry(entry)
        
        # Trouver la stat correspondante
        matching_stat_name = find_matching_stat_name(name, stats)
        
        if matching_stat_name:
            # Trouver la stat correspondante dans la liste
            matching_stat = None
            for stat in stats:
                if stat.get('name') == matching_stat_name:
                    matching_stat = stat
                    break
            
            if matching_stat:
                stat_id = ensure_stat_has_id(matching_stat)
                
                compo_structure.append({
                    "name": name,
                    "id": stat_id,
                    "count": count,
                    "min": min_count,
                    "max": max_count
                })
            else:
                print(f"{ICONS['warning']} Stat trouvée mais pas dans la liste: {matching_stat_name}")
                # Créer une entrée avec un ID généré
                compo_structure.append({
                    "name": name,
                    "id": generate_uuid(),
                    "count": count,
                    "min": min_count,
                    "max": max_count
                })
        else:
            print(f"{ICONS['warning']} Aucune stat correspondante trouvée pour: {name}")
            # Créer une entrée avec un ID généré
            compo_structure.append({
                "name": name,
                "id": generate_uuid(),
                "count": count,
                "min": min_count,
                "max": max_count
            })
    
    return compo_structure

def process_faction_file(file_path: Path) -> None:
    """Traite un fichier de faction."""
    print(f"{ICONS['processing']} Traitement de {file_path.name}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'datasheets' not in data:
            print(f"{ICONS['warning']} Pas de datasheets dans {file_path.name}")
            return
        
        modified = False
        processed_datasheets = 0
        
        for datasheet in data['datasheets']:
            if 'composition' in datasheet and 'stats' in datasheet:
                # Vérifier si compo_structure existe déjà
                if 'compo_structure' not in datasheet:
                    compo_structure = create_compo_structure(
                        datasheet['composition'], 
                        datasheet['stats']
                    )
                    datasheet['compo_structure'] = compo_structure
                    modified = True
                    processed_datasheets += 1
        
        if modified:
            # Sauvegarder avec backup
            backup_path = file_path.with_suffix('.json.backup')
            if not backup_path.exists():
                os.rename(file_path, backup_path)
                print(f"{ICONS['info']} Backup créé: {backup_path.name}")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"{ICONS['success']} {file_path.name} traité et sauvegardé ({processed_datasheets} datasheets modifiées)")
        else:
            print(f"{ICONS['skip']} {file_path.name} déjà traité ou pas de modifications")
    
    except Exception as e:
        print(f"{ICONS['error']} Erreur lors du traitement de {file_path.name}: {e}")

def print_usage():
    """Affiche l'utilisation du script."""
    print(f"{ICONS['info']} Utilisation:")
    print("  python add_compo_structure.py                    # Traite tous les fichiers du dossier archive")
    print("  python add_compo_structure.py <fichier.json>     # Traite un seul fichier spécifique")
    print("  python add_compo_structure.py --help             # Affiche cette aide")

def main():
    """Fonction principale."""
    # Vérifier les arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h', 'help']:
            print_usage()
            return
        
        # Traiter un fichier spécifique
        file_path = Path(sys.argv[1])
        
        if not file_path.exists():
            print(f"{ICONS['error']} Le fichier {file_path} n'existe pas")
            return
        
        if not file_path.suffix.lower() == '.json':
            print(f"{ICONS['error']} Le fichier doit être un fichier JSON")
            return
        
        print(f"{ICONS['file']} Traitement du fichier: {file_path}")
        process_faction_file(file_path)
        print(f"{ICONS['success']} Traitement terminé !")
        return
    
    # Traiter tous les fichiers du dossier archive
    archive_dir = Path("archive")
    
    if not archive_dir.exists():
        print(f"{ICONS['error']} Le dossier 'archive' n'existe pas")
        return
    
    # Traiter tous les fichiers JSON dans le dossier archive
    json_files = list(archive_dir.glob("*.json"))
    
    if not json_files:
        print(f"{ICONS['warning']} Aucun fichier JSON trouvé dans le dossier archive")
        return
    
    print(f"{ICONS['info']} Traitement de {len(json_files)} fichiers...")
    print(f"{ICONS['info']} Icônes: {ICONS['success']} Succès | {ICONS['warning']} Avertissement | {ICONS['error']} Erreur | {ICONS['skip']} Ignoré")
    print("-" * 80)
    
    for i, file_path in enumerate(json_files, 1):
        print(f"\n{ICONS['info']} [{i}/{len(json_files)}] ", end="")
        process_faction_file(file_path)
    
    print(f"\n{ICONS['success']} Traitement terminé !")

if __name__ == "__main__":
    main() 