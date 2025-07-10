import requests
import os
import json
from urllib.parse import urljoin

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
    
    # Ajouter les datasheets de démons du chaos
    add_daemon_datasheets()

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

def add_daemon_datasheets():
    """
    Ajoute les datasheets de démons du chaos dans les fichiers appropriés.
    """
    print("\n👹 Ajout des datasheets de démons du chaos...")
    
    # Charger chaosdaemons.json
    chaosdaemons_path = os.path.join("archive", "chaosdaemons.json")
    if not os.path.exists(chaosdaemons_path):
        print("❌ chaosdaemons.json non trouvé")
        return
    
    try:
        with open(chaosdaemons_path, 'r', encoding='utf-8') as f:
            chaosdaemons_data = json.load(f)
        
        # Définir les mappings des datasheets à ajouter
        daemon_mappings = {
            "thousandsons.json": [
                "Blue Horrors",
                "Flamers", 
                "Kairos Fateweaver",
                "Lord of Change",
                "Pink Horrors",
                "Screamers"
            ],
            "worldeaters.json": [
                "Bloodcrushers",
                "Bloodletters", 
                "Bloodthirster",
                "Flesh Hounds",
                "Skarbrand"
            ],
            "emperors_children.json": [
                "Daemonettes",
                "Fiends",
                "Keeper of Secrets", 
                "Seekers",
                "Shalaxi Helbane"
            ],
            "deathguard.json": [
                "Beasts of Nurgle",
                "Great Unclean One",
                "Nurglings",
                "Plague Drones",
                "Plaguebearers",
                "Rotigus"
            ]
        }
        
        # Traiter chaque fichier cible
        for target_file, daemon_names in daemon_mappings.items():
            target_path = os.path.join("archive", target_file)
            
            if not os.path.exists(target_path):
                print(f"⚠️ {target_file} non trouvé, ignoré")
                continue
            
            try:
                # Charger le fichier cible
                with open(target_path, 'r', encoding='utf-8') as f:
                    target_data = json.load(f)
                
                # Collecter les datasheets à ajouter
                datasheets_to_add = []
                existing_names = {ds.get('name', '') for ds in target_data.get('datasheets', [])}
                
                for daemon_name in daemon_names:
                    # Chercher la datasheet dans chaosdaemons.json
                    found = False
                    for datasheet in chaosdaemons_data.get('datasheets', []):
                        if datasheet.get('name') == daemon_name:
                            if daemon_name not in existing_names:
                                datasheets_to_add.append(datasheet)
                                print(f"➕ Ajout de {daemon_name} dans {target_file}")
                                found = True
                            else:
                                print(f"⏭️ {daemon_name} existe déjà dans {target_file}")
                                found = True
                            break
                    
                    if not found:
                        print(f"⚠️ {daemon_name} non trouvé dans chaosdaemons.json")
                
                # Ajouter les datasheets au fichier cible
                if datasheets_to_add:
                    target_data['datasheets'].extend(datasheets_to_add)
                    
                    # Sauvegarder avec backup
                    backup_path = target_path + ".backup"
                    if not os.path.exists(backup_path):
                        os.rename(target_path, backup_path)
                        print(f"💾 Backup créé pour {target_file}")
                    
                    with open(target_path, 'w', encoding='utf-8') as f:
                        json.dump(target_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"✅ {len(datasheets_to_add)} datasheets ajoutées à {target_file}")
                else:
                    print(f"ℹ️ Aucune nouvelle datasheet à ajouter à {target_file}")
                
            except Exception as e:
                print(f"❌ Erreur lors du traitement de {target_file}: {e}")
        
        print("✅ Ajout des datasheets de démons terminé")
        
    except Exception as e:
        print(f"❌ Erreur lors du chargement de chaosdaemons.json: {e}")

if __name__ == "__main__":
    download_json_files() 