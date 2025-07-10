import json
import re
import fitz
from typing import Dict, List, Any

def clean_text(text: str) -> str:
    """Nettoie le texte en supprimant les caractères spéciaux"""
    # Supprimer les caractères de contrôle et les espaces multiples
    text = re.sub(r'[^\x20-\x7E]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_munitorum_data(pdf_path: str) -> Dict[str, Any]:
    """
    Extrait les données du PDF Munitorum Field Manual
    """
    doc = fitz.open(pdf_path)
    data = {"factions": []}
    
    current_faction = None
    current_unit = None
    current_enhancement_category = None
    in_agents_section = False
    in_enhancements_section = False
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = clean_text(line)
            if not line:
                continue
            
            # Détection des factions (CODEX SUPPLEMENT: sur deux lignes)
            if line.startswith('CODEX SUPPLEMENT:'):
                # Concaténer la ligne suivante pour le nom complet
                next_line = ''
                if i + 1 < len(lines):
                    next_line = clean_text(lines[i + 1])
                faction_name = f"{line} {next_line}".strip()
                # Sauvegarder la faction précédente
                if current_faction and current_faction["name"]:
                    data["factions"].append(current_faction)
                current_faction = {
                    "name": faction_name,
                    "units": [],
                    "enhancements": []
                }
                current_unit = None
                current_enhancement_category = None
                in_enhancements_section = False
                continue
            
            # Détection des sections CODEX/INDEX (factions)
            if line.startswith('CODEX:') or line.startswith('INDEX:'):
                faction_name = line.replace('CODEX:', '').replace('INDEX:', '').strip()
                
                # Gestion spéciale pour Agents of the Imperium
                if 'AGENTS OF THE IMPERIUM' in faction_name:
                    in_agents_section = True
                else:
                    in_agents_section = False
                
                # Sauvegarder la faction précédente
                if current_faction and current_faction["name"]:
                    data["factions"].append(current_faction)
                
                current_faction = {
                    "name": faction_name,
                    "units": [],
                    "enhancements": []
                }
                current_unit = None
                current_enhancement_category = None
                in_enhancements_section = False
                continue
            
            # Ignorer les sections "EVERY MODEL HAS IMPERIUM KEYWORD" pour Agents
            if in_agents_section and 'EVERY MODEL HAS IMPERIUM KEYWORD' in line:
                continue
            
            # Ignorer les en-têtes de page et sections spéciales
            if any(skip in line for skip in ['FORGE WORLD POINTS VALUES', 'MUNITORUM', 'FIELD MANUAL']):
                continue
            
            # Détection des sections DETACHMENT ENHANCEMENTS
            if line.startswith('DETACHMENT ENHANCEMENTS'):
                in_enhancements_section = True
                current_enhancement_category = None
                continue
            
            # Si on est dans la section des améliorations, traiter différemment
            if in_enhancements_section:
                # Ignorer les lignes purement numériques
                if line.isdigit():
                    continue
                # Détection d'une nouvelle catégorie (ligne non vide, sans 'pts', non numérique)
                if line and 'pts' not in line and not line.isdigit():
                    category_name = line.strip()
                    current_enhancement_category = {
                        "category": category_name,
                        "enhancements": []
                    }
                    if current_faction:
                        current_faction["enhancements"].append(current_enhancement_category)
                    continue
                # Ajout des améliorations à la catégorie courante
                if current_enhancement_category and 'pts' in line:
                    enhancement_pattern = r'^(.+?)(\d+)\s*pts'
                    enhancement_match = re.match(enhancement_pattern, line)
                    if enhancement_match:
                        enhancement_name = enhancement_match.group(1).strip()
                        enhancement_cost = enhancement_match.group(2)
                        current_enhancement_category["enhancements"].append({
                            "name": enhancement_name,
                            "cost": enhancement_cost
                        })
                    else:
                        print(f"Ligne enhancement non reconnue: '{line}' dans {current_enhancement_category['category']}")
                    continue
            
            # Détection des unités (lignes sans points qui ne sont pas des en-têtes)
            if (current_faction and 
                not in_enhancements_section and
                not line.startswith('CODEX:') and 
                not line.startswith('INDEX:') and
                'pts' not in line and
                not line.isupper() and
                len(line) > 3 and
                not any(skip in line for skip in ['FORGE WORLD', 'DETACHMENT', 'MUNITORUM', 'FIELD MANUAL', 'CONTENTS'])):
                
                # C'est probablement le nom d'une unité
                current_unit = {
                    "name": line,
                    "costs": []
                }
                continue
            
            # Détection des coûts pour l'unité courante
            if current_unit and 'pts' in line and 'model' in line:
                # Pattern pour extraire le nombre de modèles et les points
                # Exemple: "1 model 160 pts" ou "5 model 65 pts"
                cost_pattern = r'(\d+)\s*model.*?(\d+)\s*pts'
                cost_matches = re.findall(cost_pattern, line)
                
                for model_count, cost_value in cost_matches:
                    current_unit["costs"].append({
                        "name": "model",
                        "model": model_count,
                        "cost": cost_value
                    })
                
                # Si c'est le premier coût, ajouter l'unité à la faction
                if len(current_unit["costs"]) == 1:
                    current_faction["units"].append(current_unit)
                continue

            # Détection des options supplémentaires du type "Nom d'option +XX pts" (ex: Invader ATV +60 pts)
            if current_unit and re.search(r'\+\d+\s*pts', line):
                # Pattern pour extraire les options supplémentaires
                # Exemple: "Invader ATV +60 pts"
                option_pattern = r'^(.+?)\s*\+(\d+)\s*pts'
                option_match = re.match(option_pattern, line)
                if option_match:
                    option_name = option_match.group(1).strip()
                    option_cost = option_match.group(2)
                    current_unit["costs"].append({
                        "cost_name": option_name,
                        "cost": f"+{option_cost}"
                    })
                continue
    
    # Ajouter la dernière faction
    if current_faction and current_faction["name"]:
        data["factions"].append(current_faction)
    
    doc.close()

    # === POST-TRAITEMENT IMPERIAL AGENTS ALLIED (par catégorie) ===
    agents_faction = None
    for faction in data["factions"]:
        if "IMPERIAL AGENTS" in faction["name"].upper():
            agents_faction = faction
            break
    if agents_faction:
        # On garde la liste des catégories à supprimer
        categories_to_remove = []
        for enh in agents_faction["enhancements"]:
            for unit in agents_faction["units"]:
                if unit["name"].strip() == enh["category"].strip():
                    for enh_item in enh.get("enhancements", []):
                        # Essayer d'extraire le nombre et le type depuis le nom de l'enhancement (ex: '1 model')
                        m = re.match(r'^(\d+)\s*(model|models)', enh_item["name"].strip(), re.IGNORECASE)
                        if m:
                            model = int(m.group(1))
                            name_type = "model"
                        else:
                            model = None
                            name_type = enh_item["name"].strip()
                        unit["costs"].append({
                            "name": name_type,
                            "model": model,
                            "cost": enh_item["cost"],
                            "source": "ALLIED"
                        })
                    categories_to_remove.append(enh)
        # Supprimer les catégories utilisées
        agents_faction["enhancements"] = [e for e in agents_faction["enhancements"] if e not in categories_to_remove]
    # === SUPPRESSION DES ENHANCEMENTS VIDES ===
    for faction in data["factions"]:
        faction["enhancements"] = [e for e in faction["enhancements"] if e.get("enhancements") and len(e["enhancements"]) > 0]

    return data

def save_data(data: Dict[str, Any], output_path: str):
    """Sauvegarde les données extraites en JSON"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    pdf_path = "Input Points/bds.pdf"
    output_path = "munitorum_data_final.json"
    
    print("Extraction des données du PDF Munitorum Field Manual (version finale)...")
    data = extract_munitorum_data(pdf_path)
    
    print(f"Données extraites : {len(data['factions'])} factions trouvées")
    
    # Afficher un résumé
    total_units = 0
    total_enhancements = 0
    
    for faction in data["factions"]:
        if faction["name"]:  # Ignorer les factions vides
            units_count = len(faction['units'])
            enhancements_count = len(faction['enhancements'])
            total_units += units_count
            total_enhancements += enhancements_count
            
            print(f"\nFaction: {faction['name']}")
            print(f"  Unités: {units_count}")
            print(f"  Catégories d'améliorations: {enhancements_count}")
            
            # Afficher quelques exemples d'unités
            if faction['units']:
                print("  Exemples d'unités:")
                for unit in faction['units'][:2]:
                    print(f"    - {unit['name']}: {len(unit['costs'])} coûts")
                    for cost in unit['costs'][:2]:
                        if 'model' in cost and 'name' in cost:
                            print(f"      {cost['model']} {cost['name']}: {cost['cost']} pts")
                        elif 'name' in cost:
                            print(f"      {cost['name']}: {cost['cost']} pts")
                        else:
                            print(f"      {cost}: {cost.get('cost', '')} pts")
            
            # Afficher quelques exemples d'améliorations
            if faction['enhancements']:
                print("  Exemples d'améliorations:")
                for category in faction['enhancements'][:2]:
                    print(f"    - {category['category']}: {len(category['enhancements'])} améliorations")
                    for enhancement in category['enhancements'][:2]:
                        print(f"      {enhancement['name']}: {enhancement['cost']} pts")
    
    print(f"\n=== RÉSUMÉ GLOBAL ===")
    print(f"Total des factions: {len(data['factions'])}")
    print(f"Total des unités: {total_units}")
    print(f"Total des catégories d'améliorations: {total_enhancements}")
    
    save_data(data, output_path)
    print(f"\nDonnées sauvegardées dans {output_path}") 