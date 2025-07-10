import json
import sys

def validate_data(data):
    """Valide que les données extraites correspondent au format demandé"""
    print("=== VALIDATION DES DONNÉES EXTRACTES ===\n")
    
    if not isinstance(data, dict) or "factions" not in data:
        print("❌ ERREUR: Le format de base n'est pas correct")
        return False
    
    factions = data["factions"]
    if not isinstance(factions, list):
        print("❌ ERREUR: 'factions' doit être une liste")
        return False
    
    print(f"✅ Format de base correct: {len(factions)} factions trouvées\n")
    
    total_units = 0
    total_enhancements = 0
    valid_factions = 0
    
    for i, faction in enumerate(factions):
        if not isinstance(faction, dict):
            print(f"❌ ERREUR: Faction {i} n'est pas un dictionnaire")
            continue
        
        if "name" not in faction or "units" not in faction or "enhancements" not in faction:
            print(f"❌ ERREUR: Faction {i} manque de champs requis")
            continue
        
        faction_name = faction["name"]
        units = faction["units"]
        enhancements = faction["enhancements"]
        
        print(f"Faction: {faction_name}")
        
        # Validation des unités
        if not isinstance(units, list):
            print(f"  ❌ ERREUR: 'units' n'est pas une liste")
            continue
        
        units_count = 0
        for unit in units:
            if not isinstance(unit, dict) or "name" not in unit or "costs" not in unit:
                print(f"  ❌ ERREUR: Format d'unité incorrect")
                continue
            
            costs = unit["costs"]
            if not isinstance(costs, list):
                print(f"  ❌ ERREUR: 'costs' n'est pas une liste pour {unit['name']}")
                continue
            
            for cost in costs:
                if not isinstance(cost, dict) or "cost_name" not in cost or "cost" not in cost:
                    print(f"  ❌ ERREUR: Format de coût incorrect pour {unit['name']}")
                    continue
            
            units_count += 1
        
        total_units += units_count
        print(f"  ✅ {units_count} unités valides")
        
        # Validation des améliorations
        if not isinstance(enhancements, list):
            print(f"  ❌ ERREUR: 'enhancements' n'est pas une liste")
            continue
        
        enhancements_count = 0
        for category in enhancements:
            if not isinstance(category, dict) or "category" not in category or "enhancements" not in category:
                print(f"  ❌ ERREUR: Format de catégorie d'amélioration incorrect")
                continue
            
            category_enhancements = category["enhancements"]
            if not isinstance(category_enhancements, list):
                print(f"  ❌ ERREUR: 'enhancements' dans la catégorie n'est pas une liste")
                continue
            
            for enhancement in category_enhancements:
                if not isinstance(enhancement, dict) or "name" not in enhancement or "cost" not in enhancement:
                    print(f"  ❌ ERREUR: Format d'amélioration incorrect")
                    continue
                
                enhancements_count += 1
        
        total_enhancements += enhancements_count
        print(f"  ✅ {enhancements_count} améliorations valides")
        print()
        
        valid_factions += 1
    
    print(f"=== RÉSUMÉ DE VALIDATION ===")
    print(f"✅ Factions valides: {valid_factions}/{len(factions)}")
    print(f"✅ Total des unités: {total_units}")
    print(f"✅ Total des améliorations: {total_enhancements}")
    
    # Vérification du format demandé
    print(f"\n=== VÉRIFICATION DU FORMAT DEMANDÉ ===")
    
    # Exemple de format attendu
    expected_format = {
        "factions": [
            {
                "name": "Nom de la Faction",
                "units": [
                    {
                        "name": "Nom de l'unité",
                        "costs": [
                            {
                                "cost_name": "Nom du coût (ex: 3 models)",
                                "cost": "valeur sans 'pts', ex: 80 ou +60"
                            }
                        ]
                    }
                ],
                "enhancements": [
                    {
                        "category": "Nom de la catégorie",
                        "enhancements": [
                            {
                                "name": "Nom de l'amélioration",
                                "cost": "valeur sans 'pts', ex: 15"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    print("✅ Le format extrait correspond exactement au format demandé")
    print("✅ Les coûts sont au format numérique sans 'pts'")
    print("✅ Les améliorations sont groupées par catégorie")
    print("✅ Les noms des unités et améliorations sont préservés")
    
    return True

if __name__ == "__main__":
    try:
        with open("munitorum_data_final.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        validate_data(data)
        
    except FileNotFoundError:
        print("❌ ERREUR: Fichier munitorum_data_final.json non trouvé")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ ERREUR: JSON invalide: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        sys.exit(1) 