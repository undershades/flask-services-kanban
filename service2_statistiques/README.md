# Service 2 — Statistiques sur données JSON

Microservice Flask exposant des fonctions statistiques calculées directement sur des données envoyées en JSON, sans base de données. Le service utilise **NumPy** pour les calculs descriptifs et **SciPy** pour les tests statistiques.

**Port :** `5002`
**Responsable :** Sébastien
**Branche de développement :** `feature/s2-init`

---

## 📦 Installation

```bash
cd service2_statistiques
python -m venv venv
source venv/Scripts/activate    # Windows (Git Bash)
# ou : venv\Scripts\activate    # Windows (CMD)
# ou : source venv/bin/activate # Linux/Mac

pip install flask numpy scipy
```

## ▶️ Lancement du serveur

```bash
python app.py
```

Le serveur démarre sur `http://localhost:5002`. Une fois lancé, ouvre `http://localhost:5002/` pour vérifier que le service répond, ou `http://localhost:5002/test` pour accéder à la page de tests interactifs.

---

## 📋 Routes disponibles

### `GET /`
Route d'accueil — liste les routes disponibles. Utile pour vérifier que le service tourne.

### `GET /test`
Sert la page de tests unitaires HTML/JS (`test_client_service2.html`) directement depuis le serveur.

### `POST /stats/describe`
Calcule les statistiques descriptives d'une série de valeurs (moyenne, médiane, écart-type, variance, min, max, Q1, Q3).

**Body :**
```json
{"valeurs": [12.5, 14.2, 13.8, 15.1, 11.9]}
```

**Réponse :**
```json
{
  "n": 5,
  "moyenne": 13.5,
  "mediane": 13.8,
  "ecart_type": 1.27,
  "variance": 1.62,
  "min": 11.9,
  "max": 15.1,
  "q1": 12.5,
  "q3": 14.2
}
```

### `POST /stats/correlation`
Calcule le coefficient de corrélation de Pearson entre deux séries, avec interprétation (forte/modérée/faible).

**Body :**
```json
{"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]}
```

**Réponse :**
```json
{
  "coefficient_pearson": 1.0,
  "p_value": 0.0,
  "interpretation": "Corrélation forte",
  "n": 5
}
```

### `POST /stats/test_normalite`
Effectue le test de Shapiro-Wilk pour vérifier si une série suit une loi normale.

**Body :**
```json
{"valeurs": [12.5, 14.2, 13.8, 15.1, 11.9, 13.0, 14.5]}
```

**Réponse :**
```json
{
  "statistique": 0.9712,
  "p_value": 0.931,
  "interpretation": "La série suit probablement une loi normale (p > 0.05)",
  "n": 7
}
```

### `POST /stats/test_student` *(bonus)*
Compare les moyennes de deux groupes indépendants avec le test t de Student.

**Body :**
```json
{"groupe1": [10, 12, 11, 13, 9], "groupe2": [15, 16, 14, 17, 15]}
```

**Réponse :**
```json
{
  "t_statistique": -5.0471,
  "p_value": 0.000993,
  "interpretation": "Différence significative entre les deux groupes (p < 0.05)",
  "moyenne_groupe1": 11.0,
  "moyenne_groupe2": 15.4
}
```

---

## ⚠️ Gestion des erreurs

Toutes les routes valident les données reçues via la fonction `parse_serie()` et renvoient :

| Code | Cas |
|---|---|
| `200` | Calcul réussi |
| `400` | Données invalides (champ manquant, liste vide, valeurs non numériques, tailles incompatibles) |
| `500` | Erreur interne imprévue |

**Exemple d'erreur :**
```json
{"erreur": "Le champ 'valeurs' doit être une liste non vide"}
```

---

## 🧪 Tests

### Tests unitaires Python

```bash
python test_app.py
```

11 tests couvrant les 4 routes (cas de succès et cas d'erreur).

### Tests unitaires HTML/JS

Lance le serveur puis ouvre `http://localhost:5002/test` dans ton navigateur, et clique sur **"Lancer les tests"**. 8 tests sont exécutés via `fetch()`.

### Test manuel avec curl

```bash
curl -X POST http://localhost:5002/stats/describe \
  -H "Content-Type: application/json" \
  -d '{"valeurs": [10, 12, 14, 16, 18]}'
```

---

## 📁 Structure du dossier
