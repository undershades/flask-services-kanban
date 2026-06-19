# Importation des modules Flask nécessaires
from flask import Flask, request, jsonify
# Importation de CORS pour autoriser les requêtes depuis le navigateur
from flask_cors import CORS
# Importation de NumPy pour les calculs matriciels
import numpy as np

# Création de l'application Flask
app = Flask(__name__)

# Activation de CORS sur toute l'application
CORS(app)

# fonction utilitaire utilisée par toutes les routes
def parse_matrix(data, key):
    """Convertit une liste de listes JSON en tableau NumPy pour les calculs."""
    try:
        # Récupère la matrice depuis le JSON et la convertit en tableau de flottants
        return np.array(data[key], dtype=float)
    except (KeyError, ValueError) as e:
        # Si la clé n'existe pas ou les données sont invalides, on lève une erreur
        raise ValueError(f"Matrice '{key}' invalide : {e}")

# Route 1 : Addition de deux matrices
@app.route('/matrices/add', methods=['POST'])
def add_matrices():
    # Récupération du JSON envoyé par le client
    data = request.get_json()
    try:
        # Conversion des matrices A et B en tableaux NumPy
        A = parse_matrix(data, 'A')
        B = parse_matrix(data, 'B')
        # Vérification que les dimensions sont identiques
        if A.shape != B.shape:
            return jsonify({'erreur': 'Dimensions incompatibles'}), 400
        # Addition matricielle et conversion en liste Python
        result = (A + B).tolist() 
        return jsonify({'operation': 'addition', 'resultat': result})
    except (ValueError, TypeError) as e:
        return jsonify({'erreur': str(e)}), 400

# Route 2 : Multiplication de deux matrices
@app.route('/matrices/multiply', methods=['POST'])
def multiply_matrices():
    data = request.get_json()
    try:
        A = parse_matrix(data, 'A')
        B = parse_matrix(data, 'B')  # conversion en NUMPY
        # Règle mathématique : colonnes(A) doit égaler lignes(B)
        if A.shape[1] != B.shape[0]:
            return jsonify({'erreur': 'Colonnes(A) doit egalerLignes(B)'}), 400
        # Produit matriciel avec np.dot
        result = np.dot(A, B).tolist()
        return jsonify({'operation': 'multiplication', 'resultat': result})
    except (ValueError, TypeError) as e:
        return jsonify({'erreur': str(e)}), 400

# Route 3 : Transposition d'une matrice (lignes en colonnes)
@app.route('/matrices/transpose', methods=['POST'])
def transpose_matrix():
    data = request.get_json()
    try:
        A = parse_matrix(data, 'A')
        # .T retourne la transposée (lignes et colonnes inversées)
        result = A.T.tolist()
        return jsonify({'operation': 'transposee', 'resultat': result})
    except (ValueError, TypeError) as e:
        return jsonify({'erreur': str(e)}), 400

# Route 4 : Calcul du déterminant d'une matrice carrée
@app.route('/matrices/determinant', methods=['POST'])
def determinant_matrix():
    data = request.get_json()
    try:
        A = parse_matrix(data, 'A')
        # Le déterminant n'existe que pour les matrices carrées
        if A.shape[0] != A.shape[1]:
            return jsonify({'erreur': 'La matrice doit etre carree'}), 400
        # Calcul du déterminant, arrondi à 6 décimales
        det = np.linalg.det(A)
        return jsonify({'operation': 'determinant', 'resultat': round(det, 6)})
    except (ValueError, TypeError) as e:
        return jsonify({'erreur': str(e)}), 400

# Route 5 : Calcul de la matrice inverse
@app.route('/matrices/inverse', methods=['POST'])
def inverse_matrix():
    data = request.get_json()
    try:
        A = parse_matrix(data, 'A')
        # L'inverse n'existe que pour les matrices carrées
        if A.shape[0] != A.shape[1]:
            return jsonify({'erreur': 'La matrice doit etre carree'}), 400
        det = np.linalg.det(A) # Calcule le déterminant de la matrice A avec NumPy
        # Si le déterminant est proche de 0, la matrice est singulière (non inversible)
        if abs(det) < 1e-10:
            return jsonify({'erreur': 'Matrice singuliere, non inversible'}), 400
        # Calcul de la matrice inverse
        result = np.linalg.inv(A).tolist() # covertie en tableau numpy
        return jsonify({'operation': 'inverse', 'resultat': result})
    except (ValueError, TypeError) as e:
        return jsonify({'erreur': str(e)}), 400

# Point d'entrée : lance le serveur Flask en mode debug sur le port 5001
if __name__ == '__main__':
    app.run(debug=True, port=5001)