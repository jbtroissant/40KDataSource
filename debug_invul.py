#!/usr/bin/env python3
"""
Script pour analyser les sauvegardes d'invulnérabilité dans le fichier .cat
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import re

def debug_invulnerable_saves(cat_file: str):
    """Debug les sauvegardes d'invulnérabilité"""
    
    if not Path(cat_file).exists():
        print(f"❌ Fichier {cat_file} non trouvé")
        return
    
    print(f"=== Debug des sauvegardes d'invulnérabilité ===")
    
    # Parser le fichier XML
    tree = ET.parse(cat_file)
    root = tree.getroot()
    
    # Namespace
    namespace = {'bs': 'http://www.battlescribe.net/schema/catalogueSchema'}
    
    # Chercher les profils avec des invulnérabilités
    print(f"\n🔍 Recherche des profils contenant 'invul' ou 'invulnerable':")
    
    # 1. Chercher dans les profils de capacités
    ability_profiles = root.findall('.//bs:profile[@typeName="Abilities"]', namespace) + root.findall('.//profile[@typeName="Abilities"]')
    
    invul_profiles = []
    for profile in ability_profiles:
        name = profile.get('name', '').lower()
        if 'invul' in name or 'invulnerable' in name:
            invul_profiles.append(profile)
    
    print(f"   Profils de capacités avec 'invul': {len(invul_profiles)}")
    for profile in invul_profiles[:5]:
        name = profile.get('name')
        desc_elem = profile.find('.//bs:characteristic[@name="Description"]', namespace)
        if desc_elem is None:
            desc_elem = profile.find('.//characteristic[@name="Description"]')
        description = desc_elem.text if desc_elem is not None else ""
        print(f"   - {name}: {description}")
    
    # 2. Chercher dans les profils d'unités
    print(f"\n🔍 Recherche dans les profils d'unités:")
    unit_profiles = root.findall('.//bs:profile[@typeName="Unit"]', namespace) + root.findall('.//profile[@typeName="Unit"]')
    
    for profile in unit_profiles[:10]:
        name = profile.get('name', '')
        characteristics = profile.findall('.//bs:characteristic', namespace) + profile.findall('.//characteristic')
        
        for char in characteristics:
            char_name = char.get('name', '')
            char_value = char.text or ""
            
            # Chercher des valeurs d'invulnérabilité
            if char_name.lower() in ['invulnerable', 'invul', 'invulnerable save'] or \
               (char_value and re.search(r'\d+\+', char_value) and 'invul' in char_name.lower()):
                print(f"   - {name}: {char_name} = {char_value}")
    
    # 3. Chercher dans les infoLinks
    print(f"\n🔍 Recherche dans les infoLinks:")
    info_links = root.findall('.//bs:infoLink', namespace) + root.findall('.//infoLink')
    
    invul_links = []
    for info_link in info_links:
        name = info_link.get('name', '').lower()
        if 'invul' in name or 'invulnerable' in name:
            invul_links.append(info_link)
    
    print(f"   InfoLinks avec 'invul': {len(invul_links)}")
    for link in invul_links[:5]:
        name = link.get('name')
        target_id = link.get('targetId')
        print(f"   - {name} (targetId: {target_id})")
        
        # Chercher le profil correspondant
        if target_id:
            profile = root.find(f'.//bs:profile[@id="{target_id}"]', namespace)
            if profile is None:
                profile = root.find(f'.//profile[@id="{target_id}"]')
            
            if profile:
                desc_elem = profile.find('.//bs:characteristic[@name="Description"]', namespace)
                if desc_elem is None:
                    desc_elem = profile.find('.//characteristic[@name="Description"]')
                description = desc_elem.text if desc_elem is not None else ""
                print(f"     Description: {description}")
    
    # 4. Chercher des patterns spécifiques dans les descriptions
    print(f"\n🔍 Recherche de patterns d'invulnérabilité dans les descriptions:")
    all_profiles = root.findall('.//bs:profile', namespace) + root.findall('.//profile')
    
    invul_patterns = []
    for profile in all_profiles:
        characteristics = profile.findall('.//bs:characteristic', namespace) + profile.findall('.//characteristic')
        
        for char in characteristics:
            if char.get('name') == 'Description':
                description = char.text or ""
                # Chercher des patterns comme "4+ invulnerable save" ou "invulnerable save of 4+"
                if re.search(r'(\d+)\+.*invulnerable|invulnerable.*(\d+)\+', description, re.IGNORECASE):
                    invul_patterns.append((profile.get('name'), description))
    
    print(f"   Patterns trouvés: {len(invul_patterns)}")
    for name, desc in invul_patterns[:5]:
        print(f"   - {name}: {desc}")

if __name__ == "__main__":
    import sys
    
    cat_file = "POC/Imperium - Space Marines.cat"
    if len(sys.argv) > 1:
        cat_file = sys.argv[1]
    
    debug_invulnerable_saves(cat_file) 