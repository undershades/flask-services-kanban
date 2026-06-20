# Service 4 — Chargement CSV → MySQL

# À quoi sert ce service

Ce service permet de charger des données depuis un fichier CSV vers une table MySQL partagée avec le Service 3. Il valide le fichier, nettoie les données, puis les insère dans la base.

Port : **5004**

## Routes disponibles

# POST /upload/csv

Reçoit un fichier CSV, le valide et insère les données dans la table `donnees`.

**Paramètre :** `file` (multipart/form-data)

**Exemple curl :**
```bash
curl.exe -X POST -F "file=@data/donnees_exemple.csv" http://127.0.0.1:5004/upload/csv
```

**Réponse succès (201) :**
```json
{
  "lignes_inserees": 22,
  "lignes_invalides_ignorees": 0,
  "message": "22 ligne(s) charg\u00e9e(s) dans la table donnees",
  "statut": "success"
}
```

**Réponse erreur (400) :**
```json
{
  "erreur": "Colonnes obligatoires manquantes",
  "manquantes": ["valeur", "nom_serie"]
}
```

# GET /upload/series

Liste les séries présentes dans la base de données avec leur nombre de points et leurs dates.

**Exemple curl :**
```bash
curl.exe http://127.0.0.1:5004/upload/series
```

**Réponse (200) :**
```json
{
  "series": [
    {"serie": "serie_A", "n_points": 80, "debut": "None", "fin": "None"},
    {"serie": "serie_B", "n_points": 80, "debut": "None", "fin": "None"},
    {"serie": "serie_C", "n_points": 60, "debut": "None", "fin": "None"},
    {"serie": "serie_unitaire", "n_points": 8, "debut": "2026-06-18", "fin": "2026-06-18"}
  ],
  "total": 4
}
```


# Format du CSV attendu

| Colonne | Type | Obligatoire | Exemple |
|---|---|---|---|
| nom_serie | Texte | Oui | serie_A |
| valeur | Nombre | Oui | 12.50 |
| categorie | Texte | Non | temperature |
| date_mesure | Date | Non | 2024-01-15 |

**Exemple de fichier CSV :**
```csv
nom_serie,valeur,categorie,date_mesure
serie_A,12.50,temperature,2024-01-15
serie_A,15.30,temperature,2024-01-16
```