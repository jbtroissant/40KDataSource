#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour corriger les erreurs dans les sections composition des datasheets.
Supprime les entrées qui ne suivent pas le format de composition standard.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import List, Dict

# Configurer l'encodage pour Windows
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Icônes pour améliorer la lisibilité
ICONS = {
    "success": "✅",
    "warning": "⚠️",
    "error": "❌",
    "info": "ℹ️",
    "processing": "🔄",
    "file": "📁",
    "check": "✓",
    "skip": "⏭️",
    "clean": "🧹"
}

def is_valid_composition_entry(entry: str) -> bool:
    """
    Vérifie si une entrée de composition est valide.
    
    Formats valides :
    - "1 Nom" (nombre + nom)
    - "1-5 Nom" (plage + nom)
    - "0-1 Nom" (plage optionnelle + nom)
    - "1 Nom – SUFFIX" (avec suffixe)
    """
    entry = entry.strip()
    
    # Patterns valides pour les entrées de composition
    valid_patterns = [
        r'^\d+\s+[A-Za-z\s\-\'\.]+$',  # "1 Nom"
        r'^\d+-\d+\s+[A-Za-z\s\-\'\.]+$',  # "1-5 Nom"
        r'^\d+\s+[A-Za-z\s\-\'\.]+\s*–\s*[A-Za-z\s\-\'\.]+$',  # "1 Nom – SUFFIX"
        r'^\d+-\d+\s+[A-Za-z\s\-\'\.]+\s*–\s*[A-Za-z\s\-\'\.]+$',  # "1-5 Nom – SUFFIX"
    ]
    
    for pattern in valid_patterns:
        if re.match(pattern, entry):
            return True
    
    return False

def clean_composition(composition: List[str]) -> List[str]:
    """
    Nettoie une liste de composition en supprimant les entrées invalides.
    """
    cleaned = []
    removed = []
    
    for entry in composition:
        if is_valid_composition_entry(entry):
            cleaned.append(entry)
        else:
            removed.append(entry)
    
    if removed:
        print(f"{ICONS['warning']} Entrées supprimées de la composition:")
        for entry in removed:
            print(f"   - {entry}")
    
    return cleaned

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
        total_removed_entries = 0
        
        for datasheet in data['datasheets']:
            if 'composition' in datasheet and isinstance(datasheet['composition'], list):
                original_count = len(datasheet['composition'])
                cleaned_composition = clean_composition(datasheet['composition'])
                
                if len(cleaned_composition) != original_count:
                    datasheet['composition'] = cleaned_composition
                    modified = True
                    processed_datasheets += 1
                    removed_count = original_count - len(cleaned_composition)
                    total_removed_entries += removed_count
                    
                    print(f"{ICONS['clean']} {datasheet.get('name', 'Unknown')}: {removed_count} entrées supprimées")
        
        if modified:
            # Sauvegarder avec backup
            backup_path = file_path.with_suffix('.json.backup')
            if not backup_path.exists():
                os.rename(file_path, backup_path)
                print(f"{ICONS['info']} Backup créé: {backup_path.name}")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"{ICONS['success']} {file_path.name} traité et sauvegardé ({processed_datasheets} datasheets modifiées, {total_removed_entries} entrées supprimées)")
        else:
            print(f"{ICONS['skip']} {file_path.name} déjà propre ou pas de modifications")
    
    except Exception as e:
        print(f"{ICONS['error']} Erreur lors du traitement de {file_path.name}: {e}")

def print_usage():
    """Affiche l'utilisation du script."""
    print(f"{ICONS['info']} Utilisation:")
    print("  python fix_composition_errors.py                    # Traite tous les fichiers du dossier archive")
    print("  python fix_composition_errors.py <fichier.json>     # Traite un seul fichier spécifique")
    print("  python fix_composition_errors.py --help             # Affiche cette aide")

def main():
    """Fonction principale."""
    import sys
    
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
    print(f"{ICONS['info']} Icônes: {ICONS['success']} Succès | {ICONS['warning']} Avertissement | {ICONS['error']} Erreur | {ICONS['skip']} Ignoré | {ICONS['clean']} Nettoyage")
    print("-" * 80)
    
    for i, file_path in enumerate(json_files, 1):
        print(f"\n{ICONS['info']} [{i}/{len(json_files)}] ", end="")
        process_faction_file(file_path)
    
    print(f"\n{ICONS['success']} Traitement terminé !")

if __name__ == "__main__":
    main() 