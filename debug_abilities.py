#!/usr/bin/env python3
"""
Script de debug pour analyser l'extraction des capacités
"""

import xml.etree.ElementTree as ET
from pathlib import Path

def debug_abilities():
    """Debug l'extraction des capacités"""
    
    cat_file = "POC/Imperium - Space Marines.cat"
    
    if not Path(cat_file).exists():
        print(f"❌ Fichier {cat_file} non trouvé")
        return
    
    print("=== Debug de l'extraction des capacités ===")
    
    # Parser le fichier XML
    tree = ET.parse(cat_file)
    root = tree.getroot()
    
    # Namespace
    namespace = {'bs': 'http://www.battlescribe.net/schema/catalogueSchema'}
    
    # Chercher tous les profils de capacités
    ability_profiles = root.findall('.//bs:profile[@typeName="Abilities"]', namespace)
    print(f"📊 Profils de capacités trouvés: {len(ability_profiles)}")
    
    # Afficher les premiers profils
    for i, profile in enumerate(ability_profiles[:5]):
        print(f"\n--- Profil {i+1} ---")
        print(f"ID: {profile.get('id')}")
        print(f"Name: {profile.get('name')}")
        
        # Chercher les caractéristiques
        characteristics = profile.findall('.//bs:characteristic', namespace)
        for char in characteristics:
            name = char.get('name')
            value = char.text
            print(f"  {name}: {value}")
    
    # Chercher les infoLink vers les capacités
    info_links = root.findall('.//bs:infoLink[@type="profile"]', namespace)
    print(f"\n📊 InfoLinks vers profils trouvés: {len(info_links)}")
    
    # Compter les références aux capacités
    ability_refs = {}
    for info_link in info_links:
        name = info_link.get('name')
        target_id = info_link.get('targetId')
        if name and target_id:
            if name not in ability_refs:
                ability_refs[name] = []
            ability_refs[name].append(target_id)
    
    print(f"\n📊 Capacités référencées: {len(ability_refs)}")
    for name, refs in list(ability_refs.items())[:10]:
        print(f"  {name}: {len(refs)} références")
    
    # Chercher une capacité spécifique
    print(f"\n🔍 Recherche de 'Rites of Battle':")
    if 'Rites of Battle' in ability_refs:
        target_id = ability_refs['Rites of Battle'][0]
        print(f"  Target ID: {target_id}")
        
        # Chercher le profil correspondant
        profile = root.find(f'.//bs:profile[@id="{target_id}"]', namespace)
        if profile:
            print(f"  Profil trouvé: {profile.get('name')}")
            characteristics = profile.findall('.//bs:characteristic', namespace)
            for char in characteristics:
                name = char.get('name')
                value = char.text
                print(f"    {name}: {value}")
        else:
            print("  ❌ Profil non trouvé")

if __name__ == "__main__":
    debug_abilities() 