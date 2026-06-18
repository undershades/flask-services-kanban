# Flask : framework web, request = données reçues, jsonify = convertit dict → JSON
from flask import Flask, request, jsonify, send_from_directory
import os                          # pour récupérer le chemin du dossier courant
import numpy as np                 # calculs numériques (tableaux, stats)
from scipy import stats as scipy_stats  # tests statistiques (Pearson, Shapiro, Student)

app = Flask(__name__)              # crée l'application Flask (__name__ = nom du fichier)
app.config['JSON_AS_ASCII'] = False  # envoie les accents directement (é au lieu de é)


def parse_serie(data, key="valeurs"):
    """Récupère et valide une série de valeurs numériques depuis le JSON reçu."""
    if data is None or key not in data:               # JSON absent ou champ manquant
        raise ValueError(f"Le champ '{key}' est manquant dans la requête JSON")

    valeurs = data[key]

    if not isinstance(valeurs, list) or len(valeurs) == 0:  # doit être une liste non vide
        raise ValueError(f"Le champ '{key}' doit être une liste non vide")

    try:
        array = np.array(valeurs, dtype=float)  # convertit en tableau NumPy de flottants
    except (ValueError, TypeError):             # si la liste contient du texte ou None
        raise ValueError(f"Le champ '{key}' doit contenir uniquement des nombres")

    return array
    # le paramètre key permet de réutiliser cette fonction pour "valeurs", "x", "y", "groupe1"...


# @app.route = décorateur : lie l'URL /stats/describe à la fonction describe()
# methods=["POST"] : seule la méthode POST est acceptée, Flask renvoie une erreur sur GET automatiquement
@app.route("/stats/describe", methods=["POST"])
def describe():
    data = request.get_json()  # extrait le corps de la requête et le transforme en dictionnaire Python
    try:
        valeurs = parse_serie(data, "valeurs")  # valide les données, lève ValueError si invalide

        resultat = {
            "n": int(valeurs.size),  # .size = nb d'éléments NumPy. int() car NumPy renvoie des types pas JSON-sérialisables
            "moyenne": round(float(np.mean(valeurs)), 4),    # float() pour convertir en type Python standard, round() pour 4 décimales
            "mediane": round(float(np.median(valeurs)), 4),  # valeur du milieu une fois les données triées
            "ecart_type": round(float(np.std(valeurs, ddof=1)), 4),  # ddof=1 = écart-type échantillon (÷ n-1, pas n)
            "variance": round(float(np.var(valeurs, ddof=1)), 4),    # variance = écart-type², même logique ddof=1
            "min": round(float(np.min(valeurs)), 4),
            "max": round(float(np.max(valeurs)), 4),
            "q1": round(float(np.percentile(valeurs, 25)), 4),  # 25% des valeurs sont en dessous
            "q3": round(float(np.percentile(valeurs, 75)), 4),  # 75% des valeurs sont en dessous
        }
        return jsonify(resultat), 200  # jsonify convertit le dict en JSON, 200 = succès

    except ValueError as e:       # erreur levée par parse_serie, faute du client
        return jsonify({"erreur": str(e)}), 400   # 400 = Bad Request
    except Exception as e:        # filet de sécurité pour toute erreur imprévue (ne pas planter le serveur)
        return jsonify({"erreur": f"Erreur interne : {str(e)}"}), 500  # 500 = erreur côté serveur


@app.route("/stats/correlation", methods=["POST"])
def correlation():
    data = request.get_json()
    try:
        x = parse_serie(data, "x")  # parse_serie appelée deux fois avec des clés différentes
        y = parse_serie(data, "y")  # c'est pour ça que le paramètre key existe dans parse_serie

        if x.size != y.size:  # chaque point x doit avoir un point y correspondant
            return jsonify({"erreur": "Les séries x et y doivent avoir la même taille"}), 400

        if x.size < 2:  # une corrélation n'a pas de sens avec moins de 2 points
            return jsonify({"erreur": "Au moins 2 valeurs sont nécessaires par série"}), 400

        # pearsonr renvoie 2 valeurs → tuple unpacking : on les récupère en une seule ligne
        # r entre -1 et 1 (force du lien), p_value (fiabilité statistique du résultat)
        r, p_value = scipy_stats.pearsonr(x, y)

        abs_r = abs(r)  # valeur absolue : -0.9 est aussi fort que +0.9, juste sens inverse
        # if/elif/else : cascade testée dans l'ordre, dès qu'une condition est vraie Python ignore le reste
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
            "p_value": round(float(p_value), 6),  # 6 décimales car les p_values sont souvent très petites
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

        if valeurs.size < 3:  # Shapiro-Wilk n'est pas mathématiquement valide en dessous de 3 valeurs
            return jsonify({"erreur": "Au moins 3 valeurs sont nécessaires pour ce test"}), 400

        # shapiro renvoie 2 valeurs → tuple unpacking (même principe que pearsonr)
        statistique, p_value = scipy_stats.shapiro(valeurs)

        # 0.05 = seuil de signification (alpha), convention scientifique universelle
        # p > 0.05 : pas assez de preuves pour rejeter l'hypothèse de normalité
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
        groupe2 = parse_serie(data, "groupe2")

        # les deux groupes n'ont pas besoin d'avoir la même taille (contrairement à pearsonr)
        if groupe1.size < 2 or groupe2.size < 2:  # 2 valeurs minimum pour calculer une variance
            return jsonify({"erreur": "Chaque groupe doit contenir au moins 2 valeurs"}), 400

        # ttest_ind = t-test pour groupes indépendants → tuple unpacking
        t_statistique, p_value = scipy_stats.ttest_ind(groupe1, groupe2)

        # attention sens inverse du test de normalité : ici p < 0.05 = différence significative
        if p_value < 0.05:
            interpretation = "Différence significative entre les deux groupes (p < 0.05)"
        else:
            interpretation = "Pas de différence significative entre les deux groupes (p >= 0.05)"

        resultat = {
            "t_statistique": round(float(t_statistique), 4),
            "p_value": round(float(p_value), 6),
            "interpretation": interpretation,
            "moyenne_groupe1": round(float(np.mean(groupe1)), 4),  # ajoutées pour voir concrètement
            "moyenne_groupe2": round(float(np.mean(groupe2)), 4),  # la différence entre les deux groupes
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
    dossier = os.path.dirname(os.path.abspath(__file__))  # dossier du fichier app.py
    return send_from_directory(dossier, "test_client_service2.html")


# ce bloc ne s'exécute que si on lance directement "python app.py"
if __name__ == "__main__":
    print("Page de test : http://localhost:5002/test")
    app.run(host="0.0.0.0", port=5002, debug=True)  # 0.0.0.0 = accessible sur tout le réseau
