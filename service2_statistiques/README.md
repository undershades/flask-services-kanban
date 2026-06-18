# Service 2 — Statistiques sur données JSON

Microservice Flask exposant des fonctions statistiques calculées sur des données envoyées directement en JSON.

**Port :** 5002

## Installation

```bash
cd service2_statistiques
python -m venv venv
source venv/bin/activate
pip install flask numpy scipy
python app.py
```

## Routes disponibles

### POST /stats/describe
Calcule les statistiques descriptives d'une série de valeurs.

**Body :**
```json
{"valeurs": [12.5, 14.2, 13.8, 15.1, 11.9]}
```

### POST /stats/correlation
Calcule le coefficient de corrélation de Pearson entre deux séries.

**Body :**
```json
{"x": [1,2,3,4,5], "y": [2,4,5,4,5]}
```

### POST /stats/test_normalite
Effectue le test de normalité de Shapiro-Wilk.

**Body :**
```json
{"valeurs": [12.5, 14.2, 13.8, 15.1, 11.9]}
```

### POST /stats/test_student
Compare les moyennes de deux groupes indépendants (test t de Student).

**Body :**
```json
{"groupe1": [10,12,11,13,9], "groupe2": [15,16,14,17,15]}
```

## Auteur
Sébastien