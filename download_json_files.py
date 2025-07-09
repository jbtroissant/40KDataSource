import requests
import os
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

if __name__ == "__main__":
    download_json_files() 