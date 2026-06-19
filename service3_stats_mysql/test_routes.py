import pytest
import json
import numpy as np
from scipy import stats
from unittest.mock import patch
from app import app
from db import fetch_series


# ─────────────────────────────────────────────
#  Fixture client Flask
# ─────────────────────────────────────────────
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ─────────────────────────────────────────────
#  Données réelles récupérées une seule fois
# ─────────────────────────────────────────────
@pytest.fixture(scope='session')
def valeurs_serie_A():
    return fetch_series('serie_A')

@pytest.fixture(scope='session')
def valeurs_serie_B():
    return fetch_series('serie_B')


# ══════════════════════════════════════════════
#  /db/stats/describe
# ══════════════════════════════════════════════

class TestDescribe:

    # ── Cas nominaux ──────────────────────────

    def test_describe_serie_A_status_200(self, client):
        """Retourne un 200 pour une série existante."""
        r = client.get('/db/stats/describe?serie=serie_A')
        assert r.status_code == 200

    def test_describe_source_mysql(self, client):
        """La source indiquée doit être 'mysql'."""
        r = client.get('/db/stats/describe?serie=serie_A')
        data = r.get_json()
        assert data['source'] == 'mysql'

    def test_describe_champs_presents(self, client):
        """Tous les champs attendus sont présents dans le résultat."""
        r = client.get('/db/stats/describe?serie=serie_A')
        resultat = r.get_json()['resultat']
        for champ in ('serie', 'n', 'moyenne', 'mediane', 'ecart_type', 'minimum', 'maximum'):
            assert champ in resultat, f"Champ manquant : {champ}"

    def test_describe_nom_serie_correct(self, client):
        """Le nom de la série est répercuté dans le résultat."""
        r = client.get('/db/stats/describe?serie=serie_A')
        assert r.get_json()['resultat']['serie'] == 'serie_A'

    def test_describe_n_correspond_aux_donnees(self, client, valeurs_serie_A):
        """n doit correspondre au nombre de lignes en base."""
        r = client.get('/db/stats/describe?serie=serie_A')
        assert r.get_json()['resultat']['n'] == len(valeurs_serie_A)

    def test_describe_moyenne_correcte(self, client, valeurs_serie_A):
        """La moyenne calculée doit correspondre à celle de numpy."""
        r = client.get('/db/stats/describe?serie=serie_A')
        expected = round(float(np.mean(valeurs_serie_A)), 4)
        assert r.get_json()['resultat']['moyenne'] == expected

    def test_describe_mediane_correcte(self, client, valeurs_serie_A):
        """La médiane calculée doit correspondre à celle de numpy."""
        r = client.get('/db/stats/describe?serie=serie_A')
        expected = round(float(np.median(valeurs_serie_A)), 4)
        assert r.get_json()['resultat']['mediane'] == expected

    def test_describe_ecart_type_correct(self, client, valeurs_serie_A):
        """L'écart-type (ddof=1) doit correspondre à celui de numpy."""
        r = client.get('/db/stats/describe?serie=serie_A')
        expected = round(float(np.std(valeurs_serie_A, ddof=1)), 4)
        assert r.get_json()['resultat']['ecart_type'] == expected

    def test_describe_minimum_correct(self, client, valeurs_serie_A):
        """Le minimum doit correspondre à celui de numpy."""
        r = client.get('/db/stats/describe?serie=serie_A')
        expected = round(float(np.min(valeurs_serie_A)), 4)
        assert r.get_json()['resultat']['minimum'] == expected

    def test_describe_maximum_correct(self, client, valeurs_serie_A):
        """Le maximum doit correspondre à celui de numpy."""
        r = client.get('/db/stats/describe?serie=serie_A')
        expected = round(float(np.max(valeurs_serie_A)), 4)
        assert r.get_json()['resultat']['maximum'] == expected

    def test_describe_serie_B_status_200(self, client):
        """La route fonctionne aussi pour serie_B (catégorie pression)."""
        r = client.get('/db/stats/describe?serie=serie_B')
        assert r.status_code == 200

    def test_describe_serie_B_valeurs_coherentes(self, client, valeurs_serie_B):
        """Les statistiques de serie_B sont cohérentes avec les données brutes."""
        r = client.get('/db/stats/describe?serie=serie_B')
        res = r.get_json()['resultat']
        assert res['minimum'] <= res['moyenne'] <= res['maximum']
        assert res['n'] == len(valeurs_serie_B)

    # ── Erreurs client ────────────────────────

    def test_describe_sans_parametre_400(self, client):
        """Absence du paramètre 'serie' → 400."""
        r = client.get('/db/stats/describe')
        assert r.status_code == 400

    def test_describe_sans_parametre_message(self, client):
        """Le message d'erreur mentionne le paramètre manquant."""
        r = client.get('/db/stats/describe')
        assert 'serie' in r.get_json()['erreur'].lower()

    def test_describe_serie_inexistante_404(self, client):
        """Une série absente de la base → 404."""
        r = client.get('/db/stats/describe?serie=serie_inexistante_xyz')
        assert r.status_code == 404

    def test_describe_serie_inexistante_message(self, client):
        """Le message d'erreur indique que la série n'a pas été trouvée."""
        r = client.get('/db/stats/describe?serie=serie_inexistante_xyz')
        erreur = r.get_json()['erreur'].lower()
        assert 'aucune' in erreur or 'trouvé' in erreur or 'série' in erreur


# ══════════════════════════════════════════════
#  /db/stats/correlation
# ══════════════════════════════════════════════

class TestCorrelation:

    # ── Cas nominaux ──────────────────────────

    def test_correlation_status_200(self, client):
        """Retourne un 200 pour deux séries existantes."""
        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_B')
        assert r.status_code == 200

    def test_correlation_source_mysql(self, client):
        """La source indiquée doit être 'mysql'."""
        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_B')
        assert r.get_json()['source'] == 'mysql'

    def test_correlation_champs_series(self, client):
        """Les champs serie_x, serie_y et n_points sont présents."""
        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_B')
        series = r.get_json()['series']
        assert series['x'] == 'serie_A'
        assert series['y'] == 'serie_B'
        assert 'n_points' in series

    def test_correlation_champs_resultat(self, client):
        """Les champs r, p_value et significatif sont présents."""
        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_B')
        resultat = r.get_json()['resultat']
        for champ in ('r', 'p_value', 'significatif'):
            assert champ in resultat, f"Champ manquant : {champ}"

    def test_correlation_r_dans_intervalle(self, client):
        """Le coefficient r doit être compris entre -1 et 1."""
        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_B')
        r_value = r.get_json()['resultat']['r']
        assert -1.0 <= r_value <= 1.0

    def test_correlation_p_value_positive(self, client):
        """La p-value doit être comprise entre 0 et 1."""
        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_B')
        p = r.get_json()['resultat']['p_value']
        assert 0.0 <= p <= 1.0

    def test_correlation_significatif_est_bool(self, client):
        """Le champ 'significatif' doit être un booléen."""
        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_B')
        sig = r.get_json()['resultat']['significatif']
        assert isinstance(sig, bool)

    def test_correlation_significatif_coherent_avec_p_value(self, client):
        """'significatif' doit valoir True si et seulement si p_value < 0.05."""
        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_B')
        res = r.get_json()['resultat']
        assert res['significatif'] == (res['p_value'] < 0.05)

    def test_correlation_n_points_correct(self, client, valeurs_serie_A, valeurs_serie_B):
        """n_points doit être le minimum des deux longueurs."""
        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_B')
        expected_n = min(len(valeurs_serie_A), len(valeurs_serie_B))
        assert r.get_json()['series']['n_points'] == expected_n

    def test_correlation_valeur_r_correcte(self, client, valeurs_serie_A, valeurs_serie_B):
        """La valeur de r doit correspondre au calcul scipy.pearsonr."""
        n = min(len(valeurs_serie_A), len(valeurs_serie_B))
        x = np.array(valeurs_serie_A[:n])
        y = np.array(valeurs_serie_B[:n])
        r_expected, _ = stats.pearsonr(x, y)
        r_expected = round(float(r_expected), 4)

        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_B')
        assert r.get_json()['resultat']['r'] == r_expected

    def test_correlation_avec_elle_meme_r_egal_1(self, client):
        """La corrélation d'une série avec elle-même doit être 1.0."""
        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_A')
        assert r.status_code == 200
        assert r.get_json()['resultat']['r'] == 1.0

    def test_correlation_symetrie(self, client):
        """Pearson est symétrique : corr(A,B) == corr(B,A)."""
        r1 = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_B').get_json()
        r2 = client.get('/db/stats/correlation?serie_x=serie_B&serie_y=serie_A').get_json()
        assert r1['resultat']['r'] == r2['resultat']['r']

    # ── Erreurs client ────────────────────────

    def test_correlation_sans_parametres_400(self, client):
        """Absence des deux paramètres → 400."""
        r = client.get('/db/stats/correlation')
        assert r.status_code == 400

    def test_correlation_sans_serie_y_400(self, client):
        """Absence de serie_y seul → 400."""
        r = client.get('/db/stats/correlation?serie_x=serie_A')
        assert r.status_code == 400

    def test_correlation_sans_serie_x_400(self, client):
        """Absence de serie_x seul → 400."""
        r = client.get('/db/stats/correlation?serie_y=serie_B')
        assert r.status_code == 400

    def test_correlation_serie_x_inexistante_404(self, client):
        """serie_x absente de la base → 404."""
        r = client.get('/db/stats/correlation?serie_x=serie_xyz&serie_y=serie_B')
        assert r.status_code == 404

    def test_correlation_serie_y_inexistante_404(self, client):
        """serie_y absente de la base → 404."""
        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_xyz')
        assert r.status_code == 404

    def test_correlation_message_erreur_parametres(self, client):
        """Le message d'erreur mentionne les paramètres requis."""
        r = client.get('/db/stats/correlation')
        erreur = r.get_json()['erreur'].lower()
        assert 'serie_x' in erreur or 'serie_y' in erreur or 'paramètre' in erreur

if __name__ == "__main__":
    pytest.main([__file__, "-v"])