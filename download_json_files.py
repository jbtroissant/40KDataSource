import requests
import os
import json
import re
import sys
from urllib.parse import urljoin
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

def download_json_files():
    """
    Télécharge une liste de fichiers JSON depuis l'URL GitHub spécifiée.
    """
    # URL de base
    base_url = "https://raw.githubusercontent.com/game-datacards/datasources/main/10th/gdc/"
    
    # Liste des fichiers JSON à télécharger
    json_files = [
        "adeptasororitas.json",
        "adeptuscustodes.json",
        "adeptusmechanicus.json",
        "aeldari.json",
        "agents.json",
        "astramilitarum.json",
        "blacktemplar.json",
        "bloodangels.json",
        "chaos_spacemarines.json",
        "chaosdaemons.json",
        "chaosknights.json",
        "darkangels.json",
        "deathguard.json",
        "deathwatch.json",
        "drukhari.json",
        "emperors_children.json",
        "greyknights.json",
        "gsc.json",
        "imperialknights.json",
        "necrons.json",
        "orks.json",
        "space_marines.json",
        "spacewolves.json",
        "tau.json",
        "thousandsons.json",
        "tyranids.json",
        "unaligned.json",
        "votann.json",
        "worldeaters.json"
    ]
    
    # Utiliser le dossier archive comme destination
    output_dir = "archive"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Dossier '{output_dir}' créé.")
    
    # Télécharger chaque fichier
    for filename in json_files:
        file_url = urljoin(base_url, filename)
        output_path = os.path.join(output_dir, filename)
        
        try:
            print(f"Téléchargement de {filename}...")
            response = requests.get(file_url)
            response.raise_for_status()  # Lève une exception si la requête échoue
            
            # Sauvegarder le fichier
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"✓ {filename} téléchargé avec succès")
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Erreur lors du téléchargement de {filename}: {e}")
        except Exception as e:
            print(f"✗ Erreur lors de la sauvegarde de {filename}: {e}")
    
    print(f"\nTéléchargement terminé. Les fichiers sont dans le dossier '{output_dir}' et ont remplacé les fichiers existants.")
    
    # Nettoyer space_marines.json en supprimant les datasheets en double
    clean_space_marines_json()

def clean_space_marines_json():
    """
    Supprime les datasheets de space_marines.json qui existent déjà dans les autres fichiers de chapitres.
    """
    print("\n🧹 Nettoyage de space_marines.json...")
    
    # Fichiers contenant des datasheets à exclure
    chapter_files = [
        "spacewolves.json",
        "agents.json", 
        "bloodangels.json",
        "blacktemplar.json",
        "darkangels.json",
        "deathwatch.json"
    ]
    
    # Charger space_marines.json
    space_marines_path = os.path.join("archive", "space_marines.json")
    if not os.path.exists(space_marines_path):
        print("❌ space_marines.json non trouvé")
        return
    
    try:
        with open(space_marines_path, 'r', encoding='utf-8') as f:
            space_marines_data = json.load(f)
        
        # Collecter tous les noms de datasheets des chapitres
        chapter_datasheet_names = set()
        
        for chapter_file in chapter_files:
            chapter_path = os.path.join("archive", chapter_file)
            if os.path.exists(chapter_path):
                try:
                    with open(chapter_path, 'r', encoding='utf-8') as f:
                        chapter_data = json.load(f)
                    
                    if 'datasheets' in chapter_data:
                        for datasheet in chapter_data['datasheets']:
                            if 'name' in datasheet:
                                chapter_datasheet_names.add(datasheet['name'])
                    
                    print(f"📖 {chapter_file}: {len(chapter_data.get('datasheets', []))} datasheets lues")
                    
                except Exception as e:
                    print(f"⚠️ Erreur lors de la lecture de {chapter_file}: {e}")
            else:
                print(f"⚠️ {chapter_file} non trouvé")
        
        print(f"📋 Total des datasheets des chapitres: {len(chapter_datasheet_names)}")
        
        # Filtrer les datasheets de space_marines.json
        original_count = len(space_marines_data.get('datasheets', []))
        filtered_datasheets = []
        removed_count = 0
        
        for datasheet in space_marines_data.get('datasheets', []):
            if 'name' in datasheet:
                if datasheet['name'] in chapter_datasheet_names:
                    print(f"🗑️ Suppression: {datasheet['name']}")
                    removed_count += 1
                else:
                    filtered_datasheets.append(datasheet)
            else:
                # Garder les datasheets sans nom
                filtered_datasheets.append(datasheet)
        
        # Mettre à jour space_marines.json
        space_marines_data['datasheets'] = filtered_datasheets
        
        # Sauvegarder avec backup
        backup_path = space_marines_path + ".backup"
        if not os.path.exists(backup_path):
            os.rename(space_marines_path, backup_path)
            print(f"💾 Backup créé: {backup_path}")
        
        with open(space_marines_path, 'w', encoding='utf-8') as f:
            json.dump(space_marines_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Nettoyage terminé:")
        print(f"   - Datasheets originales: {original_count}")
        print(f"   - Datasheets supprimées: {removed_count}")
        print(f"   - Datasheets restantes: {len(filtered_datasheets)}")
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")

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
            # Sauvegarder directement sans backup
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"{ICONS['success']} {file_path.name} traité et sauvegardé ({processed_datasheets} datasheets modifiées, {total_removed_entries} entrées supprimées)")
        else:
            print(f"{ICONS['skip']} {file_path.name} déjà propre ou pas de modifications")
    
    except Exception as e:
        print(f"{ICONS['error']} Erreur lors du traitement de {file_path.name}: {e}")

def fix_composition_errors():
    """
    Corrige les erreurs dans les sections composition des datasheets.
    """
    print(f"\n{ICONS['clean']} Correction des erreurs de composition...")
    
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
    download_json_files()
    # Corriger les erreurs de composition après le téléchargement
    fix_composition_errors() 