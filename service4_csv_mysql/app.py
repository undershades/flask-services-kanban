from flask import Flask, request, jsonify # import flask pour créer l'api, le request pour lire ce qu'on recoit, jsonify pour renvoyer du json
import pandas as pd  #Permet de lire le csv et manipuler  le fichier CSV
import mysql.connector 
from flask_cors import CORS # Autorise le navigateur  à appeler l'api.
from dotenv import load_dotenv
import os
import io

load_dotenv()  # Charge les variables du fichier .env (DB_HOST, DB_USER...)

app = Flask(__name__)
CORS(app) # Autorise les requêtes depuis d'autres origines (navigateur, Postman)

# Colonnes obligatoires et colonnes acceptées dans le CSV
COLONNES_REQUISES = {'nom_serie', 'valeur'} #colonnes qui doivent être dans le CSV, sinon on refuse
COLONNES_VALIDES  = {'nom_serie', 'valeur', 'categorie', 'date_mesure'} #toutes les colonnes qu'on accepte
TAILLE_MAX_OCTETS = 5 * 1024 * 1024  # limite le fichier à 5 Mo

def get_connection():
     # Connexion à MySQL via les variables d'environnement du .env
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

# Route 1 : POST /upload/csv 
@app.route('/upload/csv', methods=['POST'])
def upload_csv():
    # 1. Vérifier la présence du fichier
    if 'file' not in request.files:
        return jsonify({'erreur': 'Aucun fichier envoyé (clé "file" manquante)'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'erreur': 'Nom de fichier vide'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'erreur': 'Seuls les fichiers .csv sont acceptés'}), 400

    # 2. Lire et valider le contenu CSV
    try:
        content = file.read()
        if len(content) > TAILLE_MAX_OCTETS:
            return jsonify({'erreur': 'Fichier trop volumineux (max 5 Mo)'}), 413
        df = pd.read_csv(io.BytesIO(content), sep=None, engine='python', encoding='utf-8-sig')
    except Exception as e:
        return jsonify({'erreur': f'Lecture CSV impossible : {e}'}), 400

    # 3. Vérifier les colonnes obligatoires
    colonnes_manquantes = COLONNES_REQUISES - set(df.columns)
    if colonnes_manquantes:
        return jsonify({
            'erreur': 'Colonnes obligatoires manquantes',
            'manquantes': list(colonnes_manquantes)
        }), 400

    # 4. Nettoyer les données
    df = df[[c for c in df.columns if c in COLONNES_VALIDES]]
    df['valeur'] = pd.to_numeric(df['valeur'], errors='coerce') # Met NaN si non numérique
    lignes_invalides = df['valeur'].isna().sum()# Compte les lignes ignorées
    df.dropna(subset=['valeur'], inplace=True)# Supprime les lignes avec NaN


    if df.empty:
        return jsonify({'erreur': 'Aucune ligne valide dans le CSV'}), 400

    # 5. Insère chaque ligne dans la table MySQL "donnees"
    try:
        conn = get_connection()
        cursor = conn.cursor()
        insertions = 0
        for _, row in df.iterrows():
            cursor.execute(
                'INSERT INTO donnees (nom_serie, valeur, categorie, date_mesure) VALUES (%s, %s, %s, %s)',
                (
                    str(row['nom_serie']),
                    float(row['valeur']),
                    str(row['categorie']) if 'categorie' in df.columns else None,
                    str(row['date_mesure']) if 'date_mesure' in df.columns else None,
                )
            )
            insertions += 1
        conn.commit()  # Valide toutes les insertions
        cursor.close()
        conn.close()
    except Exception as e:
        return jsonify({'erreur': 'Erreur base de données', 'detail': str(e)}), 500

    return jsonify({
        'statut': 'success',
        'lignes_inserees': insertions,
        'lignes_invalides_ignorees': int(lignes_invalides),
        'message': f'{insertions} ligne(s) chargée(s) dans la table donnees'
    }), 201

#  Route 2 : GET /upload/series 
@app.route('/upload/series', methods=['GET'])
def list_series():
    # Retourne la liste des séries avec leur nombre de points et leurs dates min/max
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT nom_serie, COUNT(*) AS n, MIN(date_mesure), MAX(date_mesure)'
            ' FROM donnees GROUP BY nom_serie ORDER BY nom_serie'
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        series = [
            {'serie': r[0], 'n_points': r[1], 'debut': str(r[2]), 'fin': str(r[3])}
            for r in rows
        ]
        return jsonify({'series': series, 'total': len(series)})
    except Exception as e:
        return jsonify({'erreur': 'Erreur base de données', 'detail': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5004)