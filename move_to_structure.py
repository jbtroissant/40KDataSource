import os
import shutil
import sys
from glob import glob

def move_files_to_structure():
    """
    Déplace tous les fichiers .translated.json du dossier "updated translations in progress" 
    vers le dossier "structure"
    """
    source_dir = "updated translations in progress"
    target_dir = "structure"
    
    # Vérifier que le dossier source existe
    if not os.path.exists(source_dir):
        print(f"Erreur : Le dossier '{source_dir}' n'existe pas")
        return False
    
    # Créer le dossier de destination s'il n'existe pas
    os.makedirs(target_dir, exist_ok=True)
    
    # Chercher tous les fichiers .translated.json dans le dossier source
    source_files = glob(os.path.join(source_dir, "*.translated.json"))
    
    if not source_files:
        print(f"Aucun fichier .translated.json trouvé dans '{source_dir}'")
        return False
    
    print(f"Trouvé {len(source_files)} fichiers à déplacer")
    
    moved_count = 0
    for source_file in source_files:
        filename = os.path.basename(source_file)
        target_file = os.path.join(target_dir, filename)
        
        try:
            # Vérifier si le fichier de destination existe déjà
            if os.path.exists(target_file):
                print(f"Attention : {filename} existe déjà dans {target_dir}, remplacement...")
            
            # Déplacer le fichier
            shutil.move(source_file, target_file)
            print(f"Déplacé : {filename}")
            moved_count += 1
            
        except Exception as e:
            print(f"Erreur lors du déplacement de {filename}: {str(e)}")
    
    print(f"\nDéplacement terminé : {moved_count}/{len(source_files)} fichiers déplacés")
    
    # Vérifier si le dossier source est maintenant vide
    remaining_files = os.listdir(source_dir)
    if not remaining_files:
        try:
            os.rmdir(source_dir)
            print(f"Le dossier '{source_dir}' a été supprimé car il était vide")
        except Exception as e:
            print(f"Impossible de supprimer le dossier '{source_dir}': {str(e)}")
    else:
        print(f"Le dossier '{source_dir}' contient encore {len(remaining_files)} fichiers")
    
    return True

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Usage : python move_to_structure.py")
            print("Déplace tous les fichiers .translated.json du dossier 'updated translations in progress' vers 'structure'")
            return
    
    print("Déplacement des fichiers vers le dossier 'structure'...")
    success = move_files_to_structure()
    
    if success:
        print("Opération terminée avec succès")
    else:
        print("Opération échouée")
        sys.exit(1)

if __name__ == "__main__":
    main()
