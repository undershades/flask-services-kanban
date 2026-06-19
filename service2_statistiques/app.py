#Route 1 — POST /stats/describe : elle résume une liste de nombres.
#Route 2 — POST /stats/correlation : elle mesure si deux séries de nombres évoluent ensemble ou en sens inverse.
#Route 3 — POST /stats/test_normalite : elle vérifie si tes données suivent une courbe en cloche (loi normale).
#Route 4 — POST /stats/test_student : elle compare les moyennes de deux groupes pour savoir si leur différence 
#est réelle ou due au hasard.

from flask import Flask, request, jsonify, send_from_directory
import os
import numpy as np
from scipy import stats as scipy_stats  # alias pour éviter d'écrire scipy.stats à chaque fois

app = Flask(__name__)               # __name__ = nom du fichier, Flask en a besoin pour se repérer
app.config['JSON_AS_ASCII'] = False  # envoie les accents directement (é) au lieu du code Unicode


def parse_serie(data, key="valeurs"):  # key="valeurs" = valeur par défaut, changeable selon la route
    """Récupère et valide une série de valeurs numériques depuis le JSON reçu."""
    if data is None or key not in data:
        raise ValueError(f"Le champ '{key}' est manquant dans la requête JSON")  # raise = déclenche une erreur volontairement

    valeurs = data[key]

    if not isinstance(valeurs, list) or len(valeurs) == 0:  # isinstance vérifie que c'est bien une liste
        raise ValueError(f"Le champ '{key}' doit être une liste non vide")

    try:
        array = np.array(valeurs, dtype=float)  # dtype=float force la conversion en nombres décimaux
    except (ValueError, TypeError):
        raise ValueError(f"Le champ '{key}' doit contenir uniquement des nombres")

    return array


@app.route("/stats/describe", methods=["POST"])  # décorateur : lie l'URL /stats/describe à cette fonction
def describe():
    data = request.get_json()  # lit le JSON envoyé par le client, le convertit en dictionnaire Python
    try:
        valeurs = parse_serie(data, "valeurs")

        resultat = {
            "n": int(valeurs.size),                              # int() car les types NumPy ne sont pas JSON-sérialisables
            "moyenne": round(float(np.mean(valeurs)), 4),        # float() même raison, round() pour 4 décimales
            "mediane": round(float(np.median(valeurs)), 4),
            "ecart_type": round(float(np.std(valeurs, ddof=1)), 4),  # ddof=1 = écart-type échantillon (÷ n-1, pas n)
            "variance": round(float(np.var(valeurs, ddof=1)), 4),
            "min": round(float(np.min(valeurs)), 4),
            "max": round(float(np.max(valeurs)), 4),
            "q1": round(float(np.percentile(valeurs, 25)), 4),
            "q3": round(float(np.percentile(valeurs, 75)), 4),
        }
        return jsonify(resultat), 200  # 200 = succès

    except ValueError as e:
        return jsonify({"erreur": str(e)}), 400  # 400 = Bad Request (faute du client)
    except Exception as e:
        return jsonify({"erreur": f"Erreur interne : {str(e)}"}), 500  # 500 = erreur serveur


@app.route("/stats/correlation", methods=["POST"])
def correlation():
    data = request.get_json()
    try:
        x = parse_serie(data, "x")  # parse_serie réutilisée avec des clés différentes selon le champ JSON
        y = parse_serie(data, "y")

        if x.size != y.size:
            return jsonify({"erreur": "Les séries x et y doivent avoir la même taille"}), 400

        if x.size < 2:
            return jsonify({"erreur": "Au moins 2 valeurs sont nécessaires par série"}), 400

        r, p_value = scipy_stats.pearsonr(x, y)  # tuple unpacking : pearsonr renvoie 2 valeurs récupérées en une ligne

        abs_r = abs(r)  # valeur absolue : -0.9 est aussi fort que +0.9, juste sens inverse
        if abs_r >= 0.7:
            interpretation = "Corrélation forte"
        elif abs_r >= 0.4:
            interpretation = "Corrélation modérée"
        elif abs_r >= 0.2:
            interpretation = "Corrélation faible"
        else:
            interpretation = "Corrélation très faible ou nulle"

        resultat = {
            "coefficient_pearson": round(float(r), 4),
            "p_value": round(float(p_value), 6),  # 6 décimales car les p_values peuvent être très petites
            "interpretation": interpretation,
            "n": int(x.size),
        }
        return jsonify(resultat), 200

    except ValueError as e:
        return jsonify({"erreur": str(e)}), 400
    except Exception as e:
        return jsonify({"erreur": f"Erreur interne : {str(e)}"}), 500


@app.route("/stats/test_normalite", methods=["POST"])
def test_normalite():
    data = request.get_json()
    try:
        valeurs = parse_serie(data, "valeurs")

        if valeurs.size < 3:  # Shapiro-Wilk exige au moins 3 valeurs pour être valide
            return jsonify({"erreur": "Au moins 3 valeurs sont nécessaires pour ce test"}), 400

        statistique, p_value = scipy_stats.shapiro(valeurs)  # tuple unpacking, même principe que pearsonr

        # seuil 0.05 = convention statistique universelle (alpha)
        # p > 0.05 : pas assez de preuves pour rejeter la normalité
        if p_value > 0.05:
            interpretation = "La série suit probablement une loi normale (p > 0.05)"
        else:
            interpretation = "La série ne suit probablement pas une loi normale (p <= 0.05)"

        resultat = {
            "statistique": round(float(statistique), 4),
            "p_value": round(float(p_value), 6),
            "interpretation": interpretation,
            "n": int(valeurs.size),
        }
        return jsonify(resultat), 200

    except ValueError as e:
        return jsonify({"erreur": str(e)}), 400
    except Exception as e:
        return jsonify({"erreur": f"Erreur interne : {str(e)}"}), 500


@app.route("/stats/test_student", methods=["POST"])
def test_student():
    data = request.get_json()
    try:
        groupe1 = parse_serie(data, "groupe1")
        groupe2 = parse_serie(data, "groupe2")  # les deux groupes peuvent avoir des tailles différentes

        if groupe1.size < 2 or groupe2.size < 2:
            return jsonify({"erreur": "Chaque groupe doit contenir au moins 2 valeurs"}), 400

        t_statistique, p_value = scipy_stats.ttest_ind(groupe1, groupe2)  # ttest_ind = t-test pour groupes indépendants

        # attention : sens inverse du test de normalité, ici p < 0.05 = différence significative
        if p_value < 0.05:
            interpretation = "Différence significative entre les deux groupes (p < 0.05)"
        else:
            interpretation = "Pas de différence significative entre les deux groupes (p >= 0.05)"

        resultat = {
            "t_statistique": round(float(t_statistique), 4),
            "p_value": round(float(p_value), 6),
            "interpretation": interpretation,
            "moyenne_groupe1": round(float(np.mean(groupe1)), 4),
            "moyenne_groupe2": round(float(np.mean(groupe2)), 4),
        }
        return jsonify(resultat), 200

    except ValueError as e:
        return jsonify({"erreur": str(e)}), 400
    except Exception as e:
        return jsonify({"erreur": f"Erreur interne : {str(e)}"}), 500


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "service": "Service 2 — Statistiques sur données JSON",
        "routes_disponibles": [
            "POST /stats/describe",
            "POST /stats/correlation",
            "POST /stats/test_normalite",
            "POST /stats/test_student",
        ],
    }), 200


@app.route("/test", methods=["GET"])
def test_client():
    dossier = os.path.dirname(os.path.abspath(__file__))  # chemin absolu du dossier contenant app.py
    return send_from_directory(dossier, "test_client_service2.html")


if __name__ == "__main__":  # s'exécute seulement si on lance directement "python app.py"
    print("Page de test : http://localhost:5002/test")
    app.run(host="0.0.0.0", port=5002, debug=True)  # 0.0.0.0 = accessible sur tout le réseau local


#Route 1 : curl -X POST http://localhost:5002/stats/describe -H "Content-Type: application/json" -d "{\"valeurs\": [10, 12, 14, 16, 18]}"
#Route 2 : curl -X POST http://localhost:5002/stats/correlation -H "Content-Type: application/json" -d "{\"x\": [1,2,3,4,5], \"y\": [2,4,6,8,10]}"
#Route 3 : curl -X POST http://localhost:5002/stats/test_normalite -H "Content-Type: application/json" -d "{\"valeurs\": [12.5, 14.2, 13.8, 15.1, 11.9, 13.0, 14.5]}"
#Route 4 : curl -X POST http://localhost:5002/stats/test_student -H "Content-Type: application/json" -d "{\"groupe1\": [10,12,11,13,9], \"groupe2\": [15,16,14,17,15]}"