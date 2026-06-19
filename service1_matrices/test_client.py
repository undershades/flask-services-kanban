import requests
import json

BASE = "http://127.0.0.1:5001"

def tester(nom, url, body, check):
    try:
        res = requests.post(url, json=body)
        data = res.json()
        ok = check(res.status_code, data)
        statut = "✅" if ok else "❌"
        print(f"{statut} {nom}")
        print(f"   Réponse : {json.dumps(data, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ {nom} — Erreur : {e}")

print("=== Tests unitaires — Service 1 Matrices ===\n")

tester("Addition 2x2", f"{BASE}/matrices/add",
    {"A": [[1,2],[3,4]], "B": [[5,6],[7,8]]},
    lambda s, d: s == 200 and d["resultat"][0][0] == 6.0
)

tester("Multiplication 2x2", f"{BASE}/matrices/multiply",
    {"A": [[1,2],[3,4]], "B": [[5,6],[7,8]]},
    lambda s, d: s == 200 and d["resultat"][0][0] == 19.0
)

tester("Transposition 2x3", f"{BASE}/matrices/transpose",
    {"A": [[1,2,3],[4,5,6]]},
    lambda s, d: s == 200 and d["resultat"][0][1] == 4.0
)

tester("Déterminant 2x2", f"{BASE}/matrices/determinant",
    {"A": [[1,2],[3,4]]},
    lambda s, d: s == 200 and d["resultat"] == -2.0
)

tester("Inverse 2x2", f"{BASE}/matrices/inverse",
    {"A": [[1,2],[3,4]]},
    lambda s, d: s == 200 and d["operation"] == "inverse"
)

tester("Erreur matrice singulière", f"{BASE}/matrices/inverse",
    {"A": [[1,2],[2,4]]},
    lambda s, d: s == 400 and "erreur" in d
)

print("\n=== Tests terminés ===")