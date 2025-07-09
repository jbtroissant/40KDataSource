import json
import os
from pathlib import Path

def get_faction_id_from_filename(filename):
    """
    Extrait l'ID de faction à partir du nom de fichier.
    """
    # Mapping des noms de fichiers vers les IDs de faction
    filename_to_faction_id = {
        "adeptasororitas.json": "AS",
        "adeptuscustodes.json": "AC", 
        "adeptusmechanicus.json": "AdM",
        "aeldari.json": "AE",
        "agents.json": "AoI",
        "astramilitarum.json": "AM",
        "blacktemplar.json": "CHBT",
        "bloodangels.json": "CHBA",
        "chaos_spacemarines.json": "CSM",
        "chaosdaemons.json": "CD",
        "chaosknights.json": "CHKN",
        "darkangels.json": "CHDA",
        "deathguard.json": "DG",
        "Deathwatch.json": "CHDW",
        "drukhari.json": "DRU",
        "emperors_children.json": "LGEC",
        "greyknights.json": "GK",
        "gsc.json": "GSC",
        "imperialknights.json": "QI",
        "necrons.json": "NEC",
        "orks.json": "ORK",
        "space_marines.json": "SM",
        "spacewolves.json": "CHSW",
        "tau.json": "TAU",
        "thousandsons.json": "TS",
        "tyranids.json": "TYR",
        "unaligned.json": "UN",
        "votann.json": "LoV",
        "worldeaters.json": "WE"
    }
    
    return filename_to_faction_id.get(filename)

def update_costs_for_faction(archive_file_path, translated_file_path):
    """
    Met à jour les coûts dans le fichier traduit en utilisant les données du fichier d'archive.
    """
    try:
        # Lire le fichier d'archive
        with open(archive_file_path, 'r', encoding='utf-8') as f:
            archive_data = json.load(f)
        
        # Lire le fichier traduit
        with open(translated_file_path, 'r', encoding='utf-8') as f:
            translated_data = json.load(f)
        
        updated_counts = {
            'datasheets': 0,
            'enhancements': 0,
            'stratagems': 0
        }
        
        # 1. Mettre à jour les coûts des datasheets
        archive_datasheets = {}
        for datasheet in archive_data.get('datasheets', []):
            datasheet_id = datasheet.get('id')
            if datasheet_id:
                archive_datasheets[datasheet_id] = datasheet
        
        for translated_datasheet in translated_data.get('datasheets', []):
            datasheet_id = translated_datasheet.get('id')
            if datasheet_id in archive_datasheets:
                archive_datasheet = archive_datasheets[datasheet_id]
                
                # Mettre à jour les points si ils existent dans l'archive
                if 'points' in archive_datasheet:
                    translated_datasheet['points'] = archive_datasheet['points']
                    updated_counts['datasheets'] += 1
        
        # 2. Mettre à jour les coûts des enhancements
        archive_enhancements = {}
        for enhancement in archive_data.get('enhancements', []):
            enhancement_id = enhancement.get('id')
            if enhancement_id:
                archive_enhancements[enhancement_id] = enhancement
        
        # Chercher les enhancements dans les détachements du fichier traduit
        for detachment in translated_data.get('detachments', []):
            if 'enhancements' in detachment:
                for enhancement in detachment['enhancements']:
                    enhancement_id = enhancement.get('id')
                    if enhancement_id in archive_enhancements:
                        archive_enhancement = archive_enhancements[enhancement_id]
                        if 'cost' in archive_enhancement:
                            enhancement['cost'] = archive_enhancement['cost']
                            updated_counts['enhancements'] += 1
        
        # 3. Mettre à jour les coûts des stratagèmes
        archive_stratagems = {}
        for stratagem in archive_data.get('stratagems', []):
            stratagem_id = stratagem.get('id')
            if stratagem_id:
                archive_stratagems[stratagem_id] = stratagem
        
        # Chercher les stratagèmes dans les détachements du fichier traduit
        for detachment in translated_data.get('detachments', []):
            if 'stratagems' in detachment:
                for stratagem in detachment['stratagems']:
                    stratagem_id = stratagem.get('id')
                    if stratagem_id in archive_stratagems:
                        archive_stratagem = archive_stratagems[stratagem_id]
                        if 'cost' in archive_stratagem:
                            stratagem['cost'] = archive_stratagem['cost']
                            updated_counts['stratagems'] += 1
        
        # Sauvegarder le fichier traduit mis à jour
        with open(translated_file_path, 'w', encoding='utf-8') as f:
            json.dump(translated_data, f, indent=2, ensure_ascii=False)
        
        return updated_counts
        
    except Exception as e:
        print(f"Erreur lors de la mise à jour de {translated_file_path}: {e}")
        return {'datasheets': 0, 'enhancements': 0, 'stratagems': 0}

def main():
    """
    Fonction principale qui traite tous les fichiers d'archive et met à jour les coûts.
    """
    archive_dir = Path("archive")
    structure_dir = Path("structure")
    
    if not archive_dir.exists():
        print("Le dossier 'archive' n'existe pas.")
        return
    
    if not structure_dir.exists():
        print("Le dossier 'structure' n'existe pas.")
        return
    
    total_updated = {
        'datasheets': 0,
        'enhancements': 0,
        'stratagems': 0
    }
    
    # Parcourir tous les fichiers JSON dans le dossier archive
    for archive_file in archive_dir.glob("*.json"):
        if archive_file.name == "core.json":
            continue  # Ignorer le fichier core.json
            
        faction_id = get_faction_id_from_filename(archive_file.name)
        if not faction_id:
            print(f"Impossible de déterminer l'ID de faction pour {archive_file.name}")
            continue
        
        # Construire le chemin du fichier traduit correspondant
        translated_file = structure_dir / f"{faction_id}.translated.json"
        
        if not translated_file.exists():
            print(f"Fichier traduit non trouvé pour {faction_id}: {translated_file}")
            continue
        
        print(f"Traitement de {archive_file.name} -> {faction_id}")
        updated_counts = update_costs_for_faction(archive_file, translated_file)
        
        # Ajouter aux totaux
        for key in total_updated:
            total_updated[key] += updated_counts[key]
        
        print(f"  ✓ {updated_counts['datasheets']} datasheets, {updated_counts['enhancements']} enhancements, {updated_counts['stratagems']} stratagèmes mis à jour")
    
    print(f"\nMise à jour terminée.")
    print(f"Total: {total_updated['datasheets']} datasheets, {total_updated['enhancements']} enhancements, {total_updated['stratagems']} stratagèmes mis à jour.")

if __name__ == "__main__":
    main() 