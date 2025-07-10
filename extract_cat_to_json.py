#!/usr/bin/env python3
"""
Script pour extraire les données des fichiers .cat (Battlescribe) 
et les transformer en format JSON compatible avec la structure de référence.
Enrichit le modèle avec les options d'équipement et les liens vers les armes.
"""

import xml.etree.ElementTree as ET
import json
import re
import uuid
import argparse
import sys
from typing import Dict, List, Any, Optional
from pathlib import Path

class CatToJsonExtractor:
    def __init__(self):
        self.namespace = {'bs': 'http://www.battlescribe.net/schema/catalogueSchema'}
        self.weapon_profiles = {}  # Cache pour les profils d'armes
        self.ability_profiles = {}  # Cache pour les profils de capacités
        
    def extract_cat_to_json(self, cat_file: str, output_file: str) -> Dict:
        """Extrait les données d'un fichier .cat et les convertit en JSON"""
        
        # Vérifier que le fichier source existe
        if not Path(cat_file).exists():
            raise FileNotFoundError(f"Le fichier source '{cat_file}' n'existe pas.")
        
        # Parser le fichier XML
        tree = ET.parse(cat_file)
        root = tree.getroot()
        
        # Extraire les métadonnées (catalogue)
        catalogue = root.find('.//bs:catalogue', self.namespace)
        if catalogue is None:
            # Essayer sans namespace
            catalogue = root.find('.//catalogue')
        if catalogue is None:
            # Essayer à la racine
            if root.tag.endswith('catalogue'):
                catalogue = root
        if catalogue is None:
            raise ValueError("Aucun catalogue trouvé dans le fichier")
        
        # Créer la structure JSON de base
        json_data = {
            "compatibleDataVersion": 640,
            "datasheets": []
        }
        
        # Extraire toutes les entrées de sélection (unités ET modèles)
        selection_entries = root.findall('.//bs:selectionEntry[@type="unit"]', self.namespace)
        if not selection_entries:
            # Essayer sans namespace
            selection_entries = root.findall('.//selectionEntry[@type="unit"]')
        
        # Ajouter aussi les modèles (datasheets individuelles)
        model_entries = root.findall('.//bs:selectionEntry[@type="model"]', self.namespace)
        if not model_entries:
            # Essayer sans namespace
            model_entries = root.findall('.//selectionEntry[@type="model"]')
        
        all_entries = selection_entries + model_entries
        
        print(f"🔄 Extraction de {len(all_entries)} entrées depuis '{cat_file}'...")
        print(f"   - Unités: {len(selection_entries)}")
        print(f"   - Modèles: {len(model_entries)}")
        
        for entry in all_entries:
            try:
                datasheet = self._extract_datasheet(entry, root)
                if datasheet:
                    json_data["datasheets"].append(datasheet)
            except Exception as e:
                print(f"⚠️ Erreur lors de l'extraction de {entry.get('name', 'Unknown')}: {e}")
        
        # Sauvegarder le fichier JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Fichier JSON créé : {output_file}")
        return json_data
    
    def _extract_data_from_cat(self, root: ET.Element, reference_data: Dict) -> Dict:
        """Extrait les données principales du fichier .cat"""
        
        # Créer la structure de base basée sur la référence
        result = {
            "allied_factions": reference_data.get("allied_factions", []),
            "colours": reference_data.get("colours", {}),
            "compatibleDataVersion": reference_data.get("compatibleDataVersion", 640),
            "datasheets": [],
            "updated": reference_data.get("updated", "")
        }
        
        # Extraire les datasheets
        shared_entries = root.findall('.//bs:sharedSelectionEntries/bs:selectionEntry', self.namespace)
        for entry in shared_entries:
            if entry.get('type') == 'model':
                datasheet = self._extract_datasheet(entry, root)
                if datasheet:
                    result["datasheets"].append(datasheet)
        
        return result
    
    def _extract_datasheet(self, entry: ET.Element, root: ET.Element) -> Optional[Dict]:
        """Extrait une datasheet complète"""
        
        name = entry.get('name', '')
        if not name:
            return None
        
        # Extraire les profils de base
        unit_profile = self._find_profile(entry, 'Unit')
        if not unit_profile:
            return None
        
        # Extraire les statistiques
        stats = self._extract_stats(unit_profile)
        
        # Extraire les capacités
        abilities = self._extract_abilities(entry, root)
        
        # Extraire les armes
        melee_weapons = self._extract_melee_weapons(entry, root)
        ranged_weapons = self._extract_ranged_weapons(entry, root)
        
        # Extraire les options d'équipement
        wargear_options = self._extract_wargear_options(entry, root)
        
        # Extraire les points
        points = self._extract_points(entry)
        
        # Extraire les mots-clés
        keywords = self._extract_keywords(entry)
        
        # Extraire la composition
        composition = self._extract_composition(entry)
        
        # Extraire le loadout
        loadout = self._extract_loadout(entry)
        
        # Extraire le fluff
        fluff = self._extract_fluff(entry)
        
        # Extraire les informations de leader
        leader = self._extract_leader_info(entry)
        
        # Extraire les informations de transport
        transport = self._extract_transport_info(entry)
        
        # Extraire les informations de wargear
        wargear = self._extract_wargear_info(entry)
        
        return {
            "abilities": abilities,
            "cardType": "DataCard",
            "composition": composition,
            "factions": self._extract_factions(entry),
            "faction_id": self._extract_faction_id(entry),
            "fluff": fluff,
            "id": str(uuid.uuid4()),
            "keywords": keywords,
            "leader": leader,
            "loadout": loadout,
            "meleeWeapons": melee_weapons,
            "name": name,
            "points": points,
            "rangedWeapons": ranged_weapons,
            "source": "40k-10e",
            "stats": stats,
            "transport": transport,
            "wargear": wargear,
            "wargearOptions": wargear_options
        }
    
    def _find_profile(self, entry: ET.Element, profile_type: str) -> Optional[ET.Element]:
        """Trouve un profil spécifique dans une entrée"""
        profiles = entry.findall('.//bs:profile', self.namespace)
        for profile in profiles:
            if profile.get('typeName') == profile_type:
                return profile
        return None
    
    def _extract_stats(self, profile: ET.Element) -> List[Dict]:
        """Extrait les statistiques d'un profil d'unité"""
        stats = []
        
        characteristics = profile.findall('.//bs:characteristic', self.namespace)
        stat_data = {}
        
        for char in characteristics:
            name = char.get('name', '')
            value = char.text or ''
            if name and value:
                stat_data[name] = value
        
        if stat_data:
            stats.append({
                "active": True,
                "name": "Default",
                "m": stat_data.get('M', ''),
                "t": stat_data.get('T', ''),
                "sv": stat_data.get('SV', ''),
                "w": stat_data.get('W', ''),
                "ld": stat_data.get('LD', ''),
                "oc": stat_data.get('OC', ''),
                "showDamagedMarker": False,
                "showName": False
            })
        
        return stats
    
    def _extract_abilities(self, entry: ET.Element, root: ET.Element) -> Dict:
        """Extrait les capacités d'une unité en suivant les infoLink et profils liés par ID, et les profils locaux 'Abilities'"""
        abilities = {
            "core": [],
            "damaged": {
                "description": "",
                "range": "",
                "showDamagedAbility": False,
                "showDescription": True
            },
            "faction": ["Oath of Moment"],
            "invul": {
                "info": "",
                "showAtTop": True,
                "showInfo": False,
                "showInvulnerableSave": False,
                "value": ""
            },
            "other": [],
            "primarch": [],
            "special": [],
            "wargear": []
        }

        # 1. Extraire tous les profils locaux de type Abilities
        profiles = entry.findall('.//bs:profile', self.namespace) + entry.findall('.//profile')
        for profile in profiles:
            if profile.get('typeName', '').lower() == 'abilities':
                name = profile.get('name', '')
                desc_elem = profile.find('.//bs:characteristic[@name="Description"]', self.namespace)
                if desc_elem is None:
                    desc_elem = profile.find('.//characteristic[@name="Description"]')
                description = desc_elem.text if desc_elem is not None else ""
                
                # Vérifier si c'est une invulnérabilité
                if 'invul' in name.lower() or 'invulnerable' in name.lower():
                    invul_value = self._extract_invul_value(description)
                    if invul_value:
                        abilities["invul"]["showInvulnerableSave"] = True
                        abilities["invul"]["value"] = invul_value
                else:
                    abilities["other"].append({
                        "name": name,
                        "description": description,
                        "showAbility": True,
                        "showDescription": True
                    })

        # 2. Suivre tous les infoLink de l'unité (et sous-entrées)
        info_links = entry.findall('.//bs:infoLink', self.namespace) + entry.findall('.//infoLink')
        for info_link in info_links:
            if info_link.get('type') == 'profile':
                target_id = info_link.get('targetId')
                name = info_link.get('name', '')
                if target_id:
                    # Chercher le profil correspondant dans le fichier
                    profile = self._find_profile_by_id(root, target_id)
                    if profile is not None:
                        desc_elem = profile.find('.//bs:characteristic[@name="Description"]', self.namespace)
                        if desc_elem is None:
                            desc_elem = profile.find('.//characteristic[@name="Description"]')
                        description = desc_elem.text if desc_elem is not None else ""
                        
                        # Vérifier si c'est une invulnérabilité
                        if 'invul' in name.lower() or 'invulnerable' in name.lower():
                            invul_value = self._extract_invul_value(description)
                            if invul_value:
                                abilities["invul"]["showInvulnerableSave"] = True
                                abilities["invul"]["value"] = invul_value
                        elif "leader" in name.lower():
                            abilities["special"].append({
                                "name": name,
                                "description": description,
                                "showAbility": True,
                                "showDescription": True
                            })
                        elif "core" in name.lower() or name.lower() in ["deadly demise", "fly", "infiltrators", "scouts"]:
                            abilities["core"].append(name)
                        else:
                            abilities["other"].append({
                                "name": name,
                                "description": description,
                                "showAbility": True,
                                "showDescription": True
                            })
        
        # 3. Chercher les invulnérabilités dans les profils si pas encore trouvées
        if not abilities["invul"]["showInvulnerableSave"]:
            invul_value = self._extract_invul_from_profiles(entry)
            if invul_value:
                abilities["invul"]["showInvulnerableSave"] = True
                abilities["invul"]["value"] = invul_value
        
        return abilities
    
    def _find_profile_by_id(self, root: ET.Element, profile_id: str) -> Optional[ET.Element]:
        """Trouve un profil par son ID"""
        # Utiliser une recherche XPath plus précise
        profile = root.find(f'.//bs:profile[@id="{profile_id}"]', self.namespace)
        if profile is not None:
            return profile
        
        # Fallback: chercher dans tous les profils
        profiles = root.findall('.//bs:profile', self.namespace)
        for profile in profiles:
            if profile.get('id') == profile_id:
                return profile
        return None
    
    def _extract_invul_value(self, description: str) -> str:
        """Extrait la valeur d'invulnérabilité d'une description"""
        import re
        
        # Patterns pour trouver les valeurs d'invulnérabilité
        patterns = [
            r'(\d+)\+.*invulnerable',  # "4+ invulnerable save"
            r'invulnerable.*(\d+)\+',  # "invulnerable save of 4+"
            r'(\d+)\+',                # Juste "4+" dans le contexte d'invulnérabilité
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return f"{match.group(1)}+"
        
        return ""
    
    def _extract_invul_from_profiles(self, entry: ET.Element) -> str:
        """Extrait la valeur d'invulnérabilité depuis les profils de l'unité"""
        # Chercher dans les profils de capacités
        profiles = entry.findall('.//bs:profile', self.namespace) + entry.findall('.//profile')
        
        for profile in profiles:
            if profile.get('typeName', '').lower() == 'abilities':
                name = profile.get('name', '').lower()
                if 'invul' in name or 'invulnerable' in name:
                    # Chercher la valeur dans la description
                    desc_elem = profile.find('.//bs:characteristic[@name="Description"]', self.namespace)
                    if desc_elem is None:
                        desc_elem = profile.find('.//characteristic[@name="Description"]')
                    
                    if desc_elem is not None and desc_elem.text:
                        invul_value = self._extract_invul_value(desc_elem.text)
                        if invul_value:
                            return invul_value
                    
                    # Chercher une caractéristique avec juste la valeur
                    for char in profile.findall('.//bs:characteristic', self.namespace) + profile.findall('.//characteristic'):
                        char_name = char.get('name', '').lower()
                        char_value = char.text or ""
                        
                        if 'invul' in char_name and char_value and '+' in char_value:
                            return char_value
        
        return ""
    
    def _extract_melee_weapons(self, entry: ET.Element, root: ET.Element) -> List[Dict]:
        """Extrait les armes de mêlée"""
        weapons = []
        
        # Chercher dans les profils d'armes de mêlée
        melee_profiles = entry.findall('.//bs:profile[@typeName="Melee Weapons"]', self.namespace)
        for profile in melee_profiles:
            weapon = self._extract_weapon_profile(profile, "Melee")
            if weapon:
                weapons.append(weapon)
        
        # Chercher dans les sélections d'armes
        weapon_entries = entry.findall('.//bs:selectionEntry[@type="upgrade"]', self.namespace)
        for weapon_entry in weapon_entries:
            melee_profiles = weapon_entry.findall('.//bs:profile[@typeName="Melee Weapons"]', self.namespace)
            for profile in melee_profiles:
                weapon = self._extract_weapon_profile(profile, "Melee")
                if weapon:
                    weapons.append(weapon)
        
        return weapons
    
    def _extract_ranged_weapons(self, entry: ET.Element, root: ET.Element) -> List[Dict]:
        """Extrait les armes à distance"""
        weapons = []
        
        # Chercher dans les profils d'armes à distance
        ranged_profiles = entry.findall('.//bs:profile[@typeName="Ranged Weapons"]', self.namespace)
        for profile in ranged_profiles:
            weapon = self._extract_weapon_profile(profile, "Ranged")
            if weapon:
                weapons.append(weapon)
        
        # Chercher dans les sélections d'armes
        weapon_entries = entry.findall('.//bs:selectionEntry[@type="upgrade"]', self.namespace)
        for weapon_entry in weapon_entries:
            ranged_profiles = weapon_entry.findall('.//bs:profile[@typeName="Ranged Weapons"]', self.namespace)
            for profile in ranged_profiles:
                weapon = self._extract_weapon_profile(profile, "Ranged")
                if weapon:
                    weapons.append(weapon)
        
        return weapons
    
    def _extract_weapon_profile(self, profile: ET.Element, weapon_type: str) -> Optional[Dict]:
        """Extrait un profil d'arme"""
        characteristics = profile.findall('.//bs:characteristic', self.namespace)
        
        weapon_data = {}
        for char in characteristics:
            name = char.get('name', '')
            value = char.text or ''
            if name and value:
                weapon_data[name] = value
        
        if not weapon_data:
            return None
        
        # Mapper les caractéristiques
        profile_data = {
            "active": True,
            "ap": weapon_data.get('AP', ''),
            "attacks": weapon_data.get('A', ''),
            "damage": weapon_data.get('D', ''),
            "keywords": self._parse_keywords(weapon_data.get('Keywords', '')),
            "name": weapon_data.get('Name', ''),
            "range": weapon_data.get('Range', ''),
            "skill": weapon_data.get('BS' if weapon_type == "Ranged" else 'WS', ''),
            "strength": weapon_data.get('S', '')
        }
        
        return {
            "active": True,
            "profiles": [profile_data]
        }
    
    def _parse_keywords(self, keywords_str: str) -> List[str]:
        """Parse les mots-clés d'une chaîne"""
        if not keywords_str:
            return []
        return [kw.strip() for kw in keywords_str.split(',') if kw.strip()]
    
    def _extract_wargear_options(self, entry: ET.Element, root: ET.Element) -> List[Dict]:
        """Extrait les options d'équipement avec liens vers les armes"""
        options = []
        
        # Chercher les groupes de sélection
        selection_groups = entry.findall('.//bs:selectionEntryGroup', self.namespace)
        for group in selection_groups:
            group_name = group.get('name', '')
            if 'wargear' in group_name.lower() or 'weapon' in group_name.lower():
                group_options = self._extract_group_options(group, root)
                options.extend(group_options)
        
        # Chercher les sélections individuelles
        selection_entries = entry.findall('.//bs:selectionEntry[@type="upgrade"]', self.namespace)
        for selection in selection_entries:
            option = self._extract_selection_option(selection, root)
            if option:
                options.append(option)
        
        return options
    
    def _extract_group_options(self, group: ET.Element, root: ET.Element) -> List[Dict]:
        """Extrait les options d'un groupe de sélection"""
        options = []
        
        # Chercher les contraintes
        constraints = group.findall('.//bs:constraint', self.namespace)
        min_value = 0
        max_value = 1
        
        for constraint in constraints:
            if constraint.get('type') == 'min':
                min_value = int(constraint.get('value', 0))
            elif constraint.get('type') == 'max':
                max_value = int(constraint.get('value', 1))
        
        # Extraire les sélections du groupe
        selections = group.findall('.//bs:selectionEntry', self.namespace)
        for selection in selections:
            option = self._extract_selection_option(selection, root)
            if option:
                option["min"] = min_value
                option["max"] = max_value
                options.append(option)
        
        return options
    
    def _extract_selection_option(self, selection: ET.Element, root: ET.Element) -> Optional[Dict]:
        """Extrait une option de sélection"""
        name = selection.get('name', '')
        if not name:
            return None
        
        # Extraire les coûts
        costs = self._extract_costs(selection)
        
        # Extraire les armes liées
        linked_weapons = self._extract_linked_weapons(selection)
        
        # Extraire les contraintes
        constraints = self._extract_constraints(selection)
        
        return {
            "name": name,
            "costs": costs,
            "linkedWeapons": linked_weapons,
            "constraints": constraints,
            "min": 0,
            "max": 1
        }
    
    def _extract_costs(self, entry: ET.Element) -> List[Dict]:
        """Extrait les coûts d'une entrée"""
        costs = []
        cost_elements = entry.findall('.//bs:cost', self.namespace)
        
        for cost_elem in cost_elements:
            cost_name = cost_elem.get('name', '')
            cost_value = cost_elem.get('value', '0')
            costs.append({
                "name": cost_name,
                "value": cost_value
            })
        
        return costs
    
    def _extract_linked_weapons(self, entry: ET.Element) -> List[str]:
        """Extrait les armes liées à une option"""
        weapons = []
        
        # Chercher les profils d'armes
        weapon_profiles = entry.findall('.//bs:profile[@typeName="Melee Weapons"]', self.namespace)
        weapon_profiles.extend(entry.findall('.//bs:profile[@typeName="Ranged Weapons"]', self.namespace))
        
        for profile in weapon_profiles:
            name_elem = profile.find('.//bs:characteristic[@name="Name"]', self.namespace)
            if name_elem is not None and name_elem.text:
                weapons.append(name_elem.text)
        
        return weapons
    
    def _extract_constraints(self, entry: ET.Element) -> Dict:
        """Extrait les contraintes d'une entrée"""
        constraints = {}
        constraint_elements = entry.findall('.//bs:constraint', self.namespace)
        
        for constraint in constraint_elements:
            constraint_type = constraint.get('type', '')
            constraint_value = constraint.get('value', '')
            constraints[constraint_type] = constraint_value
        
        return constraints
    
    def _extract_points(self, entry: ET.Element) -> List[Dict]:
        """Extrait les points d'une unité"""
        points = []
        costs = entry.findall('.//bs:costs/bs:cost', self.namespace)
        
        for cost in costs:
            if cost.get('name') == 'pts':
                points.append({
                    "name": "model",
                    "model": "1",
                    "cost": cost.get('value', '0')
                })
                break
        
        return points
    
    def _extract_keywords(self, entry: ET.Element) -> List[str]:
        """Extrait les mots-clés d'une unité"""
        keywords = []
        category_links = entry.findall('.//bs:categoryLink', self.namespace)
        
        for link in category_links:
            keyword = link.get('name', '')
            if keyword and keyword not in keywords:
                keywords.append(keyword)
        
        return keywords
    
    def _extract_composition(self, entry: ET.Element) -> List[str]:
        """Extrait la composition d'une unité"""
        # Pour l'instant, on utilise le nom de l'unité
        name = entry.get('name', '')
        return [f"1 {name}"] if name else []
    
    def _extract_loadout(self, entry: ET.Element) -> str:
        """Extrait le loadout d'une unité"""
        # Pour l'instant, on utilise une description générique
        name = entry.get('name', '')
        return f"This model is equipped with: {name.lower()}."
    
    def _extract_fluff(self, entry: ET.Element) -> str:
        """Extrait le fluff d'une unité"""
        # Pour l'instant, on utilise une description générique
        name = entry.get('name', '')
        return f"Description of {name}."
    
    def _extract_leader_info(self, entry: ET.Element) -> str:
        """Extrait les informations de leader"""
        # Chercher les capacités de leader
        ability_profiles = entry.findall('.//bs:profile[@typeName="Abilities"]', self.namespace)
        for profile in ability_profiles:
            name_elem = profile.find('.//bs:characteristic[@name="Name"]', self.namespace)
            if name_elem is not None and "leader" in name_elem.text.lower():
                desc_elem = profile.find('.//bs:characteristic[@name="Description"]', self.namespace)
                return desc_elem.text if desc_elem is not None else ""
        
        return ""
    
    def _extract_transport_info(self, entry: ET.Element) -> str:
        """Extrait les informations de transport"""
        transport_profile = self._find_profile(entry, 'Transport')
        if transport_profile:
            capacity_elem = transport_profile.find('.//bs:characteristic[@name="Capacity"]', self.namespace)
            if capacity_elem is not None:
                return capacity_elem.text or ""
        
        return ""
    
    def _extract_wargear_info(self, entry: ET.Element) -> List[str]:
        """Extrait les informations de wargear"""
        wargear = []
        
        # Chercher les sélections d'équipement
        selection_entries = entry.findall('.//bs:selectionEntry[@type="upgrade"]', self.namespace)
        for selection in selection_entries:
            name = selection.get('name', '')
            if name:
                wargear.append(f"This model can be equipped with: {name}.")
        
        return wargear
    
    def _extract_factions(self, entry: ET.Element) -> List[str]:
        """Extrait les factions d'une unité"""
        factions = []
        category_links = entry.findall('.//bs:categoryLink', self.namespace)
        
        for link in category_links:
            name = link.get('name', '')
            if 'faction' in name.lower():
                faction_name = name.replace('Faction: ', '')
                if faction_name not in factions:
                    factions.append(faction_name)
        
        return factions if factions else ["Adeptus Astartes"]
    
    def _extract_faction_id(self, entry: ET.Element) -> str:
        """Extrait l'ID de faction"""
        # Basé sur les catégories, déterminer l'ID de faction
        category_links = entry.findall('.//bs:categoryLink', self.namespace)
        
        for link in category_links:
            name = link.get('name', '')
            if 'dark angels' in name.lower():
                return "CHDA"
            elif 'blood angels' in name.lower():
                return "CHBA"
            elif 'space wolves' in name.lower():
                return "CHSW"
        
        return "SM"  # Space Marines par défaut

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Script pour extraire les données des fichiers .cat (Battlescribe) et les transformer en format JSON.")
    parser.add_argument("cat_file", help="Chemin du fichier .cat source (ex: POC/Imperium - Dark Angels.cat)")
    parser.add_argument("reference_file", help="Chemin du fichier de référence JSON (ex: POC/darkangels.json)")
    parser.add_argument("output_file", help="Chemin du fichier JSON de sortie (ex: POC/darkangels_extracted.json)")
    
    args = parser.parse_args()
    
    # Vérifier que les fichiers existent
    if not Path(args.cat_file).exists():
        print(f"Erreur: Le fichier {args.cat_file} n'existe pas.")
        return
    
    if not Path(args.reference_file).exists():
        print(f"Erreur: Le fichier {args.reference_file} n'existe pas.")
        return
    
    # Extraire les données
    try:
        extractor = CatToJsonExtractor()
        extracted_data = extractor.extract_cat_to_json(args.cat_file, args.output_file)
        print(f"Extraction terminée avec succès!")
        print(f"Nombre de datasheets extraites: {len(extracted_data['datasheets'])}")
    except Exception as e:
        print(f"Erreur lors de l'extraction: {e}")

if __name__ == "__main__":
    main() 