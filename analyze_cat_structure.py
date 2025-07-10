#!/usr/bin/env python3
"""
Script pour analyser la structure complète d'un fichier .cat
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter

def analyze_cat_structure(cat_file: str):
    """Analyse la structure complète d'un fichier .cat"""
    
    if not Path(cat_file).exists():
        print(f"❌ Fichier {cat_file} non trouvé")
        return
    
    print(f"=== Analyse de la structure de '{cat_file}' ===")
    
    # Parser le fichier XML
    tree = ET.parse(cat_file)
    root = tree.getroot()
    
    # Namespace
    namespace = {'bs': 'http://www.battlescribe.net/schema/catalogueSchema'}
    
    # Chercher tous les selectionEntry
    selection_entries = root.findall('.//bs:selectionEntry', namespace) + root.findall('.//selectionEntry')
    
    print(f"📊 Nombre total de selectionEntry: {len(selection_entries)}")
    
    # Analyser les types
    types_counter = Counter()
    names_by_type = {}
    
    for entry in selection_entries:
        entry_type = entry.get('type', 'unknown')
        entry_name = entry.get('name', 'Unknown')
        types_counter[entry_type] += 1
        
        if entry_type not in names_by_type:
            names_by_type[entry_type] = []
        names_by_type[entry_type].append(entry_name)
    
    print(f"\n📋 Types d'entrées trouvés:")
    for entry_type, count in types_counter.most_common():
        print(f"   - {entry_type}: {count} entrées")
        
        # Afficher quelques exemples pour chaque type
        examples = names_by_type[entry_type][:5]
        print(f"     Exemples: {', '.join(examples)}")
        if len(names_by_type[entry_type]) > 5:
            print(f"     ... et {len(names_by_type[entry_type]) - 5} autres")
    
    # Analyser les profils
    print(f"\n📄 Analyse des profils:")
    profiles = root.findall('.//bs:profile', namespace) + root.findall('.//profile')
    profile_types = Counter()
    
    for profile in profiles:
        profile_type = profile.get('typeName', 'unknown')
        profile_types[profile_type] += 1
    
    print(f"   Nombre total de profils: {len(profiles)}")
    for profile_type, count in profile_types.most_common():
        print(f"   - {profile_type}: {count} profils")
    
    # Analyser les infoLinks
    print(f"\n🔗 Analyse des infoLinks:")
    info_links = root.findall('.//bs:infoLink', namespace) + root.findall('.//infoLink')
    info_link_types = Counter()
    
    for info_link in info_links:
        info_type = info_link.get('type', 'unknown')
        info_link_types[info_type] += 1
    
    print(f"   Nombre total d'infoLinks: {len(info_links)}")
    for info_type, count in info_link_types.most_common():
        print(f"   - {info_type}: {count} liens")
    
    # Suggestions d'extraction
    print(f"\n💡 Suggestions d'extraction:")
    if 'unit' in types_counter:
        print(f"   ✅ Unités (type='unit'): {types_counter['unit']} - À extraire")
    if 'model' in types_counter:
        print(f"   ⚠️ Modèles (type='model'): {types_counter['model']} - Peut contenir des datasheets individuelles")
    if 'upgrade' in types_counter:
        print(f"   ⚠️ Améliorations (type='upgrade'): {types_counter['upgrade']} - Peut contenir des options d'équipement")
    if 'selectionEntryGroup' in types_counter:
        print(f"   ℹ️ Groupes (type='selectionEntryGroup'): {types_counter['selectionEntryGroup']} - Conteneurs d'options")

if __name__ == "__main__":
    import sys
    
    cat_file = "POC/Imperium - Space Marines.cat"
    if len(sys.argv) > 1:
        cat_file = sys.argv[1]
    
    analyze_cat_structure(cat_file) 