from flask import Flask, request, jsonify 
import numpy as np 
from scipy import stats 
from db import fetch_series
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

@app.route('/db/stats/describe', methods=['GET']) 
def db_describe():
    nom_serie = request.args.get('serie')
    if not nom_serie:
        return jsonify({'erreur': "Paramètre 'serie' manquant"}), 400
    try:
        values = np.array(fetch_series(nom_serie))
        result = {             'serie':      nom_serie,
            'n':          int(len(values)),
            'moyenne':    round(float(np.mean(values)), 4),
            'mediane':    round(float(np.median(values)), 4),
            'ecart_type': round(float(np.std(values, ddof=1)), 4),
            'minimum':    round(float(np.min(values)), 4),
            'maximum':    round(float(np.max(values)), 4),
                }
        return jsonify({'source': 'mysql', 'resultat': result})
    except ValueError as e:
        return jsonify({'erreur': str(e)}), 404
    except Exception as e:
        return jsonify({'erreur': 'Erreur base de données', 'detail': str(e)}), 500
# Exemple d'appel :
# GET http://localhost:5003/db/stats/describe?serie=serie_A

if __name__ == "__main__":
    app.run(debug=True)