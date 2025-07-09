import re

# Lire le bds.txt et extraire les noms de factions
faction_names = []
with open("Input Points/bds.txt", 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line.startswith('CODEX') or line.startswith('INDEX'):
            # Extraire le nom de faction en ignorant les préfixes
            faction_name = line
            if line.startswith('CODEX SUPPLEMENT: '):
                faction_name = line.replace('CODEX SUPPLEMENT: ', '')
            elif line.startswith('CODEX: '):
                faction_name = line.replace('CODEX: ', '')
            elif line.startswith('INDEX: '):
                faction_name = line.replace('INDEX: ', '')
            
            # Ignorer les lignes vides après les préfixes
            if faction_name:
                faction_names.append(faction_name)

print("Factions trouvées dans bds.txt:")
for name in faction_names:
    print(f"  '{name}' (longueur: {len(name)})")
    # Afficher les codes ASCII des caractères
    for i, char in enumerate(name):
        print(f"    [{i}]: '{char}' (ASCII: {ord(char)})")

print("\nMapping actuel:")
FACTION_FILENAME_TO_BDS = {
    "tau": "T'AU EMPIRE",
    "emperors_children": "EMPEROR'S CHILDREN",
}

for filename, bds_name in FACTION_FILENAME_TO_BDS.items():
    print(f"  '{filename}' -> '{bds_name}' (longueur: {len(bds_name)})")
    for i, char in enumerate(bds_name):
        print(f"    [{i}]: '{char}' (ASCII: {ord(char)})")

print("\nVérification des correspondances:")
for filename, bds_name in FACTION_FILENAME_TO_BDS.items():
    if bds_name in faction_names:
        print(f"  ✅ {filename} -> {bds_name} (TROUVÉ)")
    else:
        print(f"  ❌ {filename} -> {bds_name} (NON TROUVÉ)")
        # Chercher des correspondances partielles
        for found_name in faction_names:
            if bds_name.lower() in found_name.lower() or found_name.lower() in bds_name.lower():
                print(f"    Correspondance partielle: '{found_name}'") 