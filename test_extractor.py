#!/usr/bin/env python3
"""
Script de test pour l'extracteur de fichiers .cat vers JSON
"""

import json
from pathlib import Path
from extract_cat_to_json import CatToJsonExtractor

def test_extraction(cat_file: str, reference_file: str, output_file: str):
    """Teste l'extraction des données"""
    
    extractor = CatToJsonExtractor()
    
    print("=== Test d'extraction des fichiers .cat vers JSON ===")
    
    # Vérifier que les fichiers existent
    if not Path(cat_file).exists():
        print(f"❌ Erreur: Le fichier {cat_file} n'existe pas.")
        return
    
    if not Path(reference_file).exists():
        print(f"❌ Erreur: Le fichier {reference_file} n'existe pas.")
        return
    
    print(f"✅ Fichiers trouvés:")
    print(f"   - Source: {cat_file}")
    print(f"   - Référence: {reference_file}")
    print(f"   - Sortie: {output_file}")
    
    # Extraire les données
    try:
        extracted_data = extractor.extract_cat_to_json(cat_file, output_file)
        print(f"✅ Extraction terminée avec succès!")
        print(f"📊 Nombre de datasheets extraites: {len(extracted_data['datasheets'])}")
        
        # Analyser les résultats
        analyze_results(extracted_data, reference_file)
        
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction: {e}")
        import traceback
        traceback.print_exc()

def analyze_results(extracted_data: dict, reference_file: str):
    """Analyse les résultats de l'extraction"""
    print("\n=== Analyse des résultats ===")
    
    datasheets = extracted_data.get('datasheets', [])
    print(f"📊 Datasheets extraites: {len(datasheets)}")
    
    if not datasheets:
        print("❌ Aucune datasheet extraite!")
        return
    
    # Statistiques
    total_melee = 0
    total_ranged = 0
    total_options = 0
    total_abilities = 0
    
    print(f"\n📋 Analyse des datasheets:")
    for i, datasheet in enumerate(datasheets[:10]):  # Afficher les 10 premières
        name = datasheet.get('name', 'Unknown')
        melee_count = len(datasheet.get('meleeWeapons', []))
        ranged_count = len(datasheet.get('rangedWeapons', []))
        options_count = len(datasheet.get('wargearOptions', []))
        
        total_melee += melee_count
        total_ranged += ranged_count
        total_options += options_count
        
        print(f"   - {name}: {melee_count} mêlée, {ranged_count} distance, {options_count} options")
    
    if len(datasheets) > 10:
        print(f"   ... et {len(datasheets) - 10} autres datasheets")
    
    print(f"\n📈 Totaux:")
    print(f"   - Armes de mêlée: {total_melee}")
    print(f"   - Armes à distance: {total_ranged}")
    print(f"   - Options d'équipement: {total_options}")
    
    # Comparaison avec le fichier de référence
    try:
        with open(reference_file, 'r', encoding='utf-8') as f:
            reference_data = json.load(f)
        
        ref_datasheets = reference_data.get('datasheets', [])
        print(f"\n🔍 Comparaison avec le fichier de référence:")
        print(f"   - Référence: {len(ref_datasheets)} datasheets")
        print(f"   - Extraites: {len(datasheets)} datasheets")
        
        if datasheets:
            # Analyser la première datasheet extraite
            first_ds = datasheets[0]
            print(f"\n📋 Exemple - {first_ds.get('name', 'Unknown')}:")
            print(f"   Nom: {first_ds.get('name', 'Unknown')}")
            print(f"   Faction: {first_ds.get('faction_id', 'Unknown')}")
            print(f"   Points: {first_ds.get('points', [])}")
            print(f"   Mots-clés: {first_ds.get('keywords', [])}")
            
            # Options d'équipement
            options = first_ds.get('wargearOptions', [])
            if options:
                print(f"   Options d'équipement: {len(options)}")
                for opt in options[:3]:  # Afficher les 3 premières
                    name = opt.get('name', 'Unknown')
                    min_val = opt.get('min', 0)
                    max_val = opt.get('max', 0)
                    print(f"     - {name} (min: {min_val}, max: {max_val})")
            
    except Exception as e:
        print(f"⚠️ Impossible de comparer avec le fichier de référence: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python test_extractor.py <fichier_cat> <fichier_reference> <fichier_sortie>")
        print("Exemple: python test_extractor.py 'POC/Imperium - Space Marines.cat' 'POC/space_marines.json' 'POC/space_marines_extracted.json'")
        sys.exit(1)
    
    cat_file = sys.argv[1]
    reference_file = sys.argv[2]
    output_file = sys.argv[3]
    
    test_extraction(cat_file, reference_file, output_file) 