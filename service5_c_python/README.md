# Service 5 — Fonctions C depuis Python

# À quoi sert ce service

Ce service illustre l'utilisation de fonctions C compilées (calcul intensif) appelées depuis Python via `ctypes`. Les fonctions C (moyenne, écart-type, min, max, produit scalaire) sont compilées en bibliothèque partagée puis exposées en API REST avec Flask.

Port : **5005**

# Compilation de la bibliothèque C

 La compilation doit se faire depuis un terminal **MSYS2 MINGW64** (pas PowerShell).

```bash
cd service5_c_python
gcc -shared -o lib/stats.so src/stats.c -lm
```

# Routes disponibles

# POST /c/stats/describe

Calcule moyenne, écart-type, minimum et maximum d'une série via le moteur C.

**Exemple curl :**
```bash
curl.exe -X POST -H "Content-Type: application/json" -d "@describe.json" http://127.0.0.1:5005/c/stats/describe
```

**Réponse (200) :**
```json
{
  "resultat": {
    "ecart_type": 3.8446,
    "maximum": 21.0,
    "minimum": 8.7,
    "moyenne": 13.6875,
    "n": 8
  },
  "source": "c/ctypes"
}
```

# POST /c/stats/dot

Calcule le produit scalaire entre deux vecteurs via le moteur C.

**Exemple curl :**
```bash
curl.exe -X POST -H "Content-Type: application/json" -d "@dot.json" http://127.0.0.1:5005/c/stats/dot
```

**Réponse (200) :**
```json
{
  "n": 3,
  "produit_scalaire": 32.0,
  "source": "c/ctypes"
}
```

# Benchmark Python vs C

```bash
python benchmark.py
```

Sur 1 000 000 de valeurs, le moteur C/ctypes est environ **3.3x plus rapide** que Python pur pour le calcul de moyenne et écart-type.