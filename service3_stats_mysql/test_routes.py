# ═══════════════════════════════════════════════════════════════════════
#  test_routes.py
#  Fichier de tests automatisés (pytest) pour les routes Flask de stats
#  exposées par le service3 : /db/stats/describe et /db/stats/correlation
# ═══════════════════════════════════════════════════════════════════════

import pytest               # Framework de test : fournit @pytest.fixture, pytest.main, etc.
import json                 # Importé mais non utilisé directement ici (get_json() suffit) — peut être retiré
import numpy as np          # Utilisé pour recalculer indépendamment moyenne/médiane/écart-type/min/max
from scipy import stats     # Utilisé pour recalculer indépendamment la corrélation de Pearson (pearsonr)
from unittest.mock import patch  # Importé mais non utilisé dans ce fichier (prévu pour mocker des appels DB ?)
from app import app         # Importe l'objet Flask "app" défini dans app.py (le serveur à tester)
from db import fetch_series # Importe la fonction qui va chercher les vraies données en base MySQL


# ─────────────────────────────────────────────
#  Fixture client Flask
# ─────────────────────────────────────────────
@pytest.fixture
def client():
    """
    Fixture pytest : exécutée automatiquement avant chaque test qui la demande
    en paramètre (ex: def test_xxx(self, client)).

    - app.config['TESTING'] = True :
        passe Flask en mode test. Cela désactive certains comportements de
        production (ex: les erreurs 500 ne sont pas masquées par une page
        d'erreur générique, ce qui facilite le debug).

    - with app.test_client() as client:
        crée un faux client HTTP qui peut appeler les routes de l'app
        SANS lancer un vrai serveur réseau (pas besoin de "python app.py").
        client.get(...) / client.post(...) simulent des requêtes HTTP.

    - yield client :
        renvoie le client au test en cours. Tout ce qui est après le yield
        (ici rien) s'exécuterait après la fin du test, pour du nettoyage.
        C'est le pattern standard pytest pour le setup/teardown.
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ─────────────────────────────────────────────
#  Données réelles récupérées une seule fois
# ─────────────────────────────────────────────
@pytest.fixture(scope='session')
def valeurs_serie_A():
    """
    Fixture avec scope='session' : contrairement à 'client' (recréée à
    CHAQUE test), celle-ci n'est exécutée qu'UNE SEULE FOIS pour toute
    la session de tests, puis le résultat est réutilisé partout.

    Pourquoi : interroger la base à chaque test serait lent et redondant
    (les données ne changent pas pendant l'exécution des tests).

    Retourne la liste/array des valeurs brutes de 'serie_A' directement
    depuis MySQL (via fetch_series), utilisée comme "vérité terrain"
    pour comparer aux résultats renvoyés par l'API.
    """
    return fetch_series('serie_A')

@pytest.fixture(scope='session')
def valeurs_serie_B():
    """Identique à valeurs_serie_A, mais pour la série 'serie_B'."""
    return fetch_series('serie_B')


# ══════════════════════════════════════════════
#  /db/stats/describe
# ══════════════════════════════════════════════
# Route testée : GET /db/stats/describe?serie=<nom>
# Comportement attendu : renvoie un JSON avec des statistiques descriptives
# (n, moyenne, médiane, écart-type, min, max) calculées sur la série demandée.

class TestDescribe:
    # Regrouper les tests dans une classe (TestXxx) est une convention pytest :
    # cela permet de les organiser/filtrer facilement (ex: pytest -k TestDescribe)

    # ── Cas nominaux ──────────────────────────
    # "Nominal" = scénario normal, sans erreur, où tout se passe comme prévu.

    def test_describe_serie_A_status_200(self, client):
        """Retourne un 200 pour une série existante."""
        # Appel GET sur la route avec serie=serie_A en query string
        r = client.get('/db/stats/describe?serie=serie_A')
        # 200 = OK, la requête a été traitée avec succès
        assert r.status_code == 200

    def test_describe_source_mysql(self, client):
        """La source indiquée doit être 'mysql'."""
        r = client.get('/db/stats/describe?serie=serie_A')
        data = r.get_json()  # Parse le corps de la réponse JSON en dict Python
        # Vérifie que l'API précise bien que les données viennent de MySQL
        # (et pas d'un CSV, ce qui distingue ce service des autres microservices)
        assert data['source'] == 'mysql'

    def test_describe_champs_presents(self, client):
        """Tous les champs attendus sont présents dans le résultat."""
        r = client.get('/db/stats/describe?serie=serie_A')
        resultat = r.get_json()['resultat']  # Sous-dictionnaire contenant les stats
        # On boucle sur la liste des clés obligatoires et on vérifie une à une
        # leur présence. Le message d'erreur personnalisé (f-string après la
        # virgule) précise QUEL champ manque si le test échoue, pour debug rapide.
        for champ in ('serie', 'n', 'moyenne', 'mediane', 'ecart_type', 'minimum', 'maximum'):
            assert champ in resultat, f"Champ manquant : {champ}"

    def test_describe_nom_serie_correct(self, client):
        """Le nom de la série est répercuté dans le résultat."""
        r = client.get('/db/stats/describe?serie=serie_A')
        # Vérifie que l'API renvoie bien dans sa réponse le nom de série
        # qu'on lui a demandé en entrée (pas un nom codé en dur par erreur)
        assert r.get_json()['resultat']['serie'] == 'serie_A'

    def test_describe_n_correspond_aux_donnees(self, client, valeurs_serie_A):
        """n doit correspondre au nombre de lignes en base."""
        r = client.get('/db/stats/describe?serie=serie_A')
        # len(valeurs_serie_A) = nombre réel de lignes récupérées par fetch_series
        # On compare au champ 'n' renvoyé par l'API : ils doivent être identiques
        assert r.get_json()['resultat']['n'] == len(valeurs_serie_A)

    def test_describe_moyenne_correcte(self, client, valeurs_serie_A):
        """La moyenne calculée doit correspondre à celle de numpy."""
        r = client.get('/db/stats/describe?serie=serie_A')
        # np.mean() calcule la moyenne arithmétique sur les données réelles
        # round(..., 4) arrondit à 4 décimales, pour matcher le format de l'API
        # float(...) convertit le type numpy (np.float64) en float Python natif
        expected = round(float(np.mean(valeurs_serie_A)), 4)
        assert r.get_json()['resultat']['moyenne'] == expected

    def test_describe_mediane_correcte(self, client, valeurs_serie_A):
        """La médiane calculée doit correspondre à celle de numpy."""
        r = client.get('/db/stats/describe?serie=serie_A')
        # np.median() = valeur centrale qui sépare les données en deux moitiés égales
        expected = round(float(np.median(valeurs_serie_A)), 4)
        assert r.get_json()['resultat']['mediane'] == expected

    def test_describe_ecart_type_correct(self, client, valeurs_serie_A):
        """L'écart-type (ddof=1) doit correspondre à celui de numpy."""
        r = client.get('/db/stats/describe?serie=serie_A')
        # ddof=1 (Delta Degrees of Freedom) : utilise n-1 au dénominateur,
        # c'est l'écart-type "échantillon" (estimation non biaisée de la
        # variance d'une population à partir d'un échantillon).
        # Par défaut, np.std utilise ddof=0 (dénominateur n) → résultat différent.
        # Ce test vérifie donc que l'API a bien choisi la bonne formule.
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
        # Important : ce test évite que le code soit "codé en dur" pour serie_A
        # uniquement. On vérifie que le paramètre 'serie' est bien générique.
        r = client.get('/db/stats/describe?serie=serie_B')
        assert r.status_code == 200

    def test_describe_serie_B_valeurs_coherentes(self, client, valeurs_serie_B):
        """Les statistiques de serie_B sont cohérentes avec les données brutes."""
        r = client.get('/db/stats/describe?serie=serie_B')
        res = r.get_json()['resultat']
        # Test de cohérence "logique" plutôt qu'une égalité stricte :
        # par définition mathématique, min ≤ moyenne ≤ max est TOUJOURS vrai.
        # Si ce n'est pas le cas, il y a forcément un bug dans le calcul.
        assert res['minimum'] <= res['moyenne'] <= res['maximum']
        # Vérifie aussi que n correspond bien au nombre de valeurs réelles
        assert res['n'] == len(valeurs_serie_B)

    # ── Erreurs client ────────────────────────
    # Tests des cas où l'utilisateur de l'API fait une erreur (paramètre
    # manquant, série inexistante...). On vérifie que l'API répond proprement
    # avec un code 4xx (erreur côté client) et un message clair, plutôt que
    # de planter avec une erreur 500 ou un comportement non défini.

    def test_describe_sans_parametre_400(self, client):
        """Absence du paramètre 'serie' → 400."""
        # Pas de "?serie=..." dans l'URL : la requête est incomplète
        r = client.get('/db/stats/describe')
        # 400 = Bad Request, code HTTP standard pour une requête mal formée
        assert r.status_code == 400

    def test_describe_sans_parametre_message(self, client):
        """Le message d'erreur mentionne le paramètre manquant."""
        r = client.get('/db/stats/describe')
        # .lower() : on met en minuscule pour rendre la comparaison
        # insensible à la casse (évite un faux échec si l'API écrit "Serie")
        assert 'serie' in r.get_json()['erreur'].lower()

    def test_describe_serie_inexistante_404(self, client):
        """Une série absente de la base → 404."""
        # 'serie_inexistante_xyz' n'existe dans aucune table/colonne de la base
        r = client.get('/db/stats/describe?serie=serie_inexistante_xyz')
        # 404 = Not Found, la ressource demandée n'existe pas
        assert r.status_code == 404

    def test_describe_serie_inexistante_message(self, client):
        """Le message d'erreur indique que la série n'a pas été trouvée."""
        r = client.get('/db/stats/describe?serie=serie_inexistante_xyz')
        erreur = r.get_json()['erreur'].lower()
        # On accepte plusieurs formulations possibles du message d'erreur
        # (le test ne dépend pas d'une phrase exacte, juste d'un mot-clé
        # pertinent), pour rester robuste si le wording change légèrement.
        assert 'aucune' in erreur or 'trouvé' in erreur or 'série' in erreur


# ══════════════════════════════════════════════
#  /db/stats/correlation
# ══════════════════════════════════════════════
# Route testée : GET /db/stats/correlation?serie_x=<nom>&serie_y=<nom>
# Comportement attendu : calcule le coefficient de corrélation de Pearson (r)
# entre deux séries, ainsi que la p-value associée et un indicateur de
# significativité statistique.

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
        series = r.get_json()['series']  # Sous-dictionnaire décrivant les séries comparées
        # Vérifie que l'API renvoie bien quelles séries ont été utilisées en entrée
        assert series['x'] == 'serie_A'
        assert series['y'] == 'serie_B'
        # n_points = nombre de paires (x, y) effectivement utilisées dans le calcul
        assert 'n_points' in series

    def test_correlation_champs_resultat(self, client):
        """Les champs r, p_value et significatif sont présents."""
        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_B')
        resultat = r.get_json()['resultat']
        # r = coefficient de corrélation, p_value = probabilité associée au test
        # d'hypothèse, significatif = interprétation booléenne de p_value
        for champ in ('r', 'p_value', 'significatif'):
            assert champ in resultat, f"Champ manquant : {champ}"

    def test_correlation_r_dans_intervalle(self, client):
        """Le coefficient r doit être compris entre -1 et 1."""
        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_B')
        r_value = r.get_json()['resultat']['r']
        # Propriété mathématique du coefficient de Pearson : il est TOUJOURS
        # dans [-1, 1]. -1 = corrélation négative parfaite, 1 = positive parfaite,
        # 0 = aucune corrélation linéaire. Un résultat hors de cet intervalle
        # indiquerait un bug de calcul.
        assert -1.0 <= r_value <= 1.0

    def test_correlation_p_value_positive(self, client):
        """La p-value doit être comprise entre 0 et 1."""
        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_B')
        p = r.get_json()['resultat']['p_value']
        # Une p-value est une probabilité par définition : forcément entre 0 et 1
        assert 0.0 <= p <= 1.0

    def test_correlation_significatif_est_bool(self, client):
        """Le champ 'significatif' doit être un booléen."""
        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_B')
        sig = r.get_json()['resultat']['significatif']
        # isinstance() vérifie le TYPE exact (True/False Python), pas juste
        # une valeur "truthy" comme 1/0 ou "true"/"false" (string), qui
        # pourraient passer un test moins strict mais casser le contrat JSON.
        assert isinstance(sig, bool)

    def test_correlation_significatif_coherent_avec_p_value(self, client):
        """'significatif' doit valoir True si et seulement si p_value < 0.05."""
        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_B')
        res = r.get_json()['resultat']
        # 0.05 = seuil de significativité standard en statistiques (5%).
        # Ce test vérifie la COHÉRENCE INTERNE de la réponse : le booléen
        # 'significatif' doit être le résultat logique exact de cette
        # comparaison, pas une valeur calculée séparément qui pourrait diverger.
        assert res['significatif'] == (res['p_value'] < 0.05)

    def test_correlation_n_points_correct(self, client, valeurs_serie_A, valeurs_serie_B):
        """n_points doit être le minimum des deux longueurs."""
        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_B')
        # Si serie_A a 100 valeurs et serie_B en a 80, on ne peut former que
        # 80 paires (x, y) complètes → le minimum des deux tailles.
        expected_n = min(len(valeurs_serie_A), len(valeurs_serie_B))
        assert r.get_json()['series']['n_points'] == expected_n

    def test_correlation_valeur_r_correcte(self, client, valeurs_serie_A, valeurs_serie_B):
        """La valeur de r doit correspondre au calcul scipy.pearsonr."""
        # Recalcul indépendant et complet du coefficient, en dehors de l'API,
        # pour s'assurer qu'elle utilise bien le bon algorithme (Pearson)
        # et la bonne troncature des données.
        n = min(len(valeurs_serie_A), len(valeurs_serie_B))
        x = np.array(valeurs_serie_A[:n])  # On tronque les deux séries à la même taille n
        y = np.array(valeurs_serie_B[:n])
        # stats.pearsonr renvoie un tuple (coefficient r, p-value)
        r_expected, _ = stats.pearsonr(x, y)  # "_" = on ignore la p-value ici
        r_expected = round(float(r_expected), 4)

        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_B')
        # Comparaison stricte entre le calcul "maison" et la réponse de l'API
        assert r.get_json()['resultat']['r'] == r_expected

    def test_correlation_avec_elle_meme_r_egal_1(self, client):
        """La corrélation d'une série avec elle-même doit être 1.0."""
        # Cas particulier/limite : comparer une série à elle-même donne
        # toujours une corrélation parfaite (r = 1.0), c'est une propriété
        # mathématique garantie, indépendamment des données réelles.
        r = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_A')
        assert r.status_code == 200
        assert r.get_json()['resultat']['r'] == 1.0

    def test_correlation_symetrie(self, client):
        """Pearson est symétrique : corr(A,B) == corr(B,A)."""
        # On appelle la route dans les deux sens (A,B) puis (B,A)
        r1 = client.get('/db/stats/correlation?serie_x=serie_A&serie_y=serie_B').get_json()
        r2 = client.get('/db/stats/correlation?serie_x=serie_B&serie_y=serie_A').get_json()
        # Propriété mathématique : la corrélation de Pearson ne dépend pas
        # de l'ordre des variables, donc les deux résultats doivent être identiques.
        assert r1['resultat']['r'] == r2['resultat']['r']

    # ── Erreurs client ────────────────────────

    def test_correlation_sans_parametres_400(self, client):
        """Absence des deux paramètres → 400."""
        # Aucun serie_x ni serie_y fourni dans l'URL
        r = client.get('/db/stats/correlation')
        assert r.status_code == 400

    def test_correlation_sans_serie_y_400(self, client):
        """Absence de serie_y seul → 400."""
        # serie_x fourni mais serie_y manquant : requête incomplète, doit échouer
        r = client.get('/db/stats/correlation?serie_x=serie_A')
        assert r.status_code == 400

    def test_correlation_sans_serie_x_400(self, client):
        """Absence de serie_x seul → 400."""
        # Symétrique du test précédent : serie_y fourni mais serie_x manquant
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
        # Test souple : accepte plusieurs formulations tant qu'au moins un
        # indice pertinent (nom de paramètre ou mot générique) est présent
        assert 'serie_x' in erreur or 'serie_y' in erreur or 'paramètre' in erreur


# ─────────────────────────────────────────────
#  Point d'entrée du script
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # Permet de lancer ce fichier directement avec "python test_routes.py"
    # en plus de la commande standard "pytest test_routes.py".
    # pytest.main() exécute pytest en interne avec les arguments donnés :
    #   - __file__ : ne lance que les tests de ce fichier précis
    #   - "-v"     : mode verbose, affiche le nom et le résultat de chaque test
    pytest.main([__file__, "-v"])