from flask import Blueprint, render_template, jsonify, request
from db import fetch_series
import numpy as np
from scipy import stats

bp = Blueprint('ui', __name__)

SERIES_DISPONIBLES = ['serie_A', 'serie_B', 'serie_C', 'serie_unitaire']  

@bp.route('/')
def index():
    return render_template('Index.html', series=SERIES_DISPONIBLES)

@bp.route('/ui/stats/describe', methods=['GET'])
def ui_describe():
    """Appelle la logique de describe pour une ou plusieurs séries."""
    series = request.args.getlist('serie')
    if not series:
        return jsonify({'erreur': "Paramètre 'serie' manquant"}), 400

    resultats = {}
    for nom_serie in series:
        try:
            values = np.array(fetch_series(nom_serie))
            resultats[nom_serie] = {
                'serie':      nom_serie,
                'n':          int(len(values)),
                'moyenne':    round(float(np.mean(values)), 4),
                'mediane':    round(float(np.median(values)), 4),
                'ecart_type': round(float(np.std(values, ddof=1)), 4),
                'minimum':    round(float(np.min(values)), 4),
                'maximum':    round(float(np.max(values)), 4),
            }
        except ValueError as e:
            resultats[nom_serie] = {'erreur': str(e)}
        except Exception as e:
            resultats[nom_serie] = {'erreur': 'Erreur base de données', 'detail': str(e)}

    return jsonify({'source': 'mysql', 'resultats': resultats})


@bp.route('/ui/stats/correlation', methods=['GET'])
def ui_correlation():
    """Corrélation entre deux séries choisies."""
    serie_x = request.args.get('serie_x')
    serie_y = request.args.get('serie_y')
    if not serie_x or not serie_y:
        return jsonify({'erreur': 'Paramètres serie_x et serie_y requis'}), 400
    try:
        x = np.array(fetch_series(serie_x))
        y = np.array(fetch_series(serie_y))
        n = min(len(x), len(y))
        x, y = x[:n], y[:n]
        r, p_value = stats.pearsonr(x, y)
        return jsonify({
            'source': 'mysql',
            'series': {'x': serie_x, 'y': serie_y, 'n_points': n},
            'resultat': {
                'r':           round(float(r), 4),
                'p_value':     round(float(p_value), 6),
                'significatif': bool(p_value < 0.05)
            }
        })
    except ValueError as e:
        return jsonify({'erreur': str(e)}), 404
    except Exception as e:
        return jsonify({'erreur': 'Erreur base de données', 'detail': str(e)}), 500