from flask import Flask, request, jsonify 
import numpy as np 
from scipy import stats 
from db import fetch_series
from config import Config
from Controller import bp

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(bp)

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

@app.route('/db/stats/correlation', methods=['GET'])
def db_correlation():
    serie_x = request.args.get('serie_x')
    serie_y = request.args.get('serie_y')
    if not serie_x or not serie_y:
        return jsonify({'erreur': 'Paramètres serie_x et serie_y requis'}), 400
    try:
        x = np.array(fetch_series(serie_x))
        y = np.array(fetch_series(serie_y))
        n = min(len(x), len(y))
        x, y = x[:n], y[:n]  # Aligner les longueurs
        r, p_value = stats.pearsonr(x, y)
        return jsonify({
            'source': 'mysql',
            'series': {'x': serie_x, 'y': serie_y, 'n_points': n},
            'resultat': {
                'r': round(float(r), 4),
                'p_value': round(float(p_value), 6),
                'significatif': bool(p_value < 0.05)
            }         })
    except ValueError as e:
        return jsonify({'erreur': str(e)}), 404
    except Exception as e:
        return jsonify({'erreur': 'Erreur base de données', 'detail': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5003)
