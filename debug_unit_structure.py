#!/usr/bin/env python3
"""
Script de debug pour analyser la structure XML d'une unité spécifique
"""

import xml.etree.ElementTree as ET
from pathlib import Path

def debug_unit_structure(cat_file: str, unit_name: str = "Intercessor Squad"):
    """Debug la structure d'une unité spécifique"""
    
    if not Path(cat_file).exists():
        print(f"❌ Fichier {cat_file} non trouvé")
        return
    
    print(f"=== Debug de la structure de '{unit_name}' ===")
    
    # Parser le fichier XML
    tree = ET.parse(cat_file)
    root = tree.getroot()
    
    # Namespace
    namespace = {'bs': 'http://www.battlescribe.net/schema/catalogueSchema'}
    
    # Chercher l'unité par nom
    selection_entries = root.findall('.//bs:selectionEntry', namespace) + root.findall('.//selectionEntry')
    
    target_entry = None
    for entry in selection_entries:
        if entry.get('name') == unit_name:
            target_entry = entry
            break
    
    if not target_entry:
        print(f"❌ Unit '{unit_name}' non trouvée")
        return
    
    print(f"✅ Unit '{unit_name}' trouvée")
    print(f"   ID: {target_entry.get('id')}")
    print(f"   Type: {target_entry.get('type')}")
    
    # Analyser la structure de l'unité
    print(f"\n📋 Structure de l'unité:")
    
    # Chercher tous les éléments enfants
    children = list(target_entry)
    print(f"   Nombre d'éléments enfants: {len(children)}")
    
    for i, child in enumerate(children[:10]):  # Afficher les 10 premiers
        tag = child.tag.replace('{http://www.battlescribe.net/schema/catalogueSchema}', 'bs:')
        print(f"   {i+1}. {tag}")
        if child.attrib:
            print(f"      Attributs: {dict(child.attrib)}")
    
    # Chercher spécifiquement les infoLink
    print(f"\n🔗 InfoLinks:")
    info_links = target_entry.findall('.//bs:infoLink', namespace) + target_entry.findall('.//infoLink')
    print(f"   Nombre d'infoLinks trouvés: {len(info_links)}")
    
    for i, info_link in enumerate(info_links[:5]):  # Afficher les 5 premiers
        print(f"   {i+1}. Type: {info_link.get('type')}")
        print(f"      Name: {info_link.get('name')}")
        print(f"      TargetId: {info_link.get('targetId')}")
        print(f"      Id: {info_link.get('id')}")
    
    # Chercher les profils
    print(f"\n📄 Profils:")
    profiles = target_entry.findall('.//bs:profile', namespace) + target_entry.findall('.//profile')
    print(f"   Nombre de profils trouvés: {len(profiles)}")
    
    for i, profile in enumerate(profiles[:3]):  # Afficher les 3 premiers
        print(f"   {i+1}. TypeName: {profile.get('typeName')}")
        print(f"      Name: {profile.get('name')}")
        print(f"      Id: {profile.get('id')}")
        
        # Chercher les caractéristiques
        characteristics = profile.findall('.//bs:characteristic', namespace) + profile.findall('.//characteristic')
        for char in characteristics:
            name = char.get('name')
            value = char.text
            print(f"      - {name}: {value}")
    
    # Chercher les sous-entrées
    print(f"\n📦 Sous-entrées:")
    sub_entries = target_entry.findall('.//bs:selectionEntry', namespace) + target_entry.findall('.//selectionEntry')
    print(f"   Nombre de sous-entrées: {len(sub_entries)}")
    
    for i, sub_entry in enumerate(sub_entries[:3]):  # Afficher les 3 premiers
        print(f"   {i+1}. Name: {sub_entry.get('name')}")
        print(f"      Type: {sub_entry.get('type')}")
        print(f"      Id: {sub_entry.get('id')}")
        
        # Chercher les infoLink de cette sous-entrée
        sub_info_links = sub_entry.findall('.//bs:infoLink', namespace) + sub_entry.findall('.//infoLink')
        if sub_info_links:
            print(f"      InfoLinks: {len(sub_info_links)}")
            for info_link in sub_info_links[:2]:
                print(f"        - {info_link.get('name')} (type: {info_link.get('type')})")

if __name__ == "__main__":
    import sys
    
    cat_file = "POC/Imperium - Space Marines.cat"
    unit_name = "Intercessor Squad"
    
    if len(sys.argv) > 1:
        cat_file = sys.argv[1]
    if len(sys.argv) > 2:
        unit_name = sys.argv[2]
    
    debug_unit_structure(cat_file, unit_name) 