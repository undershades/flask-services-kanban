from flask import Flask, request, jsonify
from c_bridge import calculer_describe, calculer_dot_product

app = Flask(__name__)


@app.route('/c/stats/describe', methods=['POST'])
def describe():
    """Calcule moyenne, écart-type, min, max d'une série via le moteur C."""
    data = request.get_json()

    if not data or 'valeurs' not in data:
        return jsonify({'erreur': 'Le champ "valeurs" est requis'}), 400

    valeurs = data['valeurs']

    if not isinstance(valeurs, list) or len(valeurs) == 0:
        return jsonify({'erreur': '"valeurs" doit être une liste non vide'}), 400

    try:
        valeurs = [float(v) for v in valeurs]
    except (ValueError, TypeError):
        return jsonify({'erreur': 'Toutes les valeurs doivent être numériques'}), 400

    resultat = calculer_describe(valeurs)

    return jsonify({
        'resultat': resultat,
        'source': 'c/ctypes'
    })


@app.route('/c/stats/dot', methods=['POST'])
def dot():
    """Calcule le produit scalaire entre deux vecteurs via le moteur C."""
    data = request.get_json()

    if not data or 'a' not in data or 'b' not in data:
        return jsonify({'erreur': 'Les champs "a" et "b" sont requis'}), 400

    a = data['a']
    b = data['b']

    if not isinstance(a, list) or not isinstance(b, list):
        return jsonify({'erreur': '"a" et "b" doivent être des listes'}), 400

    if len(a) != len(b):
        return jsonify({'erreur': '"a" et "b" doivent avoir la même longueur'}), 400

    try:
        a = [float(v) for v in a]
        b = [float(v) for v in b]
    except (ValueError, TypeError):
        return jsonify({'erreur': 'Toutes les valeurs doivent être numériques'}), 400

    resultat = calculer_dot_product(a, b)

    return jsonify({
        'produit_scalaire': resultat,
        'n': len(a),
        'source': 'c/ctypes'
    })


if __name__ == '__main__':
    app.run(debug=True, port=5005)