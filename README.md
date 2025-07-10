# 40K Data Source

Projet de gestion des données Warhammer 40,000 avec extraction et traduction.

## Scripts principaux

### Extraction de données
- **`extract_munitorum_data.py`** : Extraction des données du PDF Munitorum Field Manual
  - Extrait les factions, unités avec coûts, et améliorations de détachement
  - Génère `munitorum_data.json`
  - Utilise PyMuPDF pour l'extraction

### Validation
- **`validate_extraction.py`** : Validation du format des données extraites
  - Vérifie la conformité avec les spécifications
  - Affiche des statistiques détaillées

### Gestion des données
- **`download_json_files.py`** : Téléchargement des fichiers JSON depuis GitHub
  - Télécharge les datasheets des factions depuis game-datacards/datasources
  - Sauvegarde dans le dossier `archive/`

- **`update_costs.py`** : Mise à jour des coûts dans les fichiers traduits
  - Synchronise les coûts entre les fichiers d'archive et traduits
  - Met à jour datasheets, enhancements et stratagèmes

- **`update_faction_ability_keys.py`** : Mise à jour des clés d'aptitudes de faction
- **`update_weapon_keys.py`** : Mise à jour des clés d'armes

### Traduction
- **`extract_and_replace_translations.py`** : Gestion des traductions
  - Extrait et remplace les traductions entre fichiers EN et FR

### Utilitaires
- **`update_points_from_bds.py`** : Mise à jour des points depuis BDS
- **`test_mapping.py`** : Tests de mapping

## Structure des dossiers

- **`archive/`** : Fichiers JSON originaux téléchargés
- **`en/`** : Fichiers JSON en anglais (format plat)
- **`fr/`** : Fichiers JSON en français (format plat)
- **`structure/`** : Fichiers JSON traduits avec structure complète
- **`Input Points/`** : Fichiers source (PDF, etc.)
- **`wargear_options/`** : Options d'équipement

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

1. **Télécharger les données** :
   ```bash
   python download_json_files.py
   ```

2. **Extraire les données du PDF** :
   ```bash
   python extract_munitorum_data.py
   ```

3. **Valider l'extraction** :
   ```bash
   python validate_extraction.py
   ```

4. **Mettre à jour les coûts** :
   ```bash
   python update_costs.py
   ``` 