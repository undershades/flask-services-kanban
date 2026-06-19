import unittest
from app import app  # on importe l'application Flask pour pouvoir la tester


class TestService2(unittest.TestCase):  # hérite de unittest.TestCase pour avoir accès aux méthodes assert*

    def setUp(self):  # s'exécute automatiquement AVANT chaque test
        self.client = app.test_client()  # faux navigateur : envoie des requêtes sans lancer de vrai serveur HTTP

    # --- /stats/describe ---

    def test_describe_succes(self):
        reponse = self.client.post(
            "/stats/describe",
            json={"valeurs": [10, 12, 14, 16, 18]}  # json= envoie automatiquement le bon Content-Type
        )
        self.assertEqual(reponse.status_code, 200)  # vérifie que les deux valeurs sont égales
        data = reponse.get_json()  # convertit la réponse JSON en dictionnaire Python
        self.assertEqual(data["n"], 5)
        self.assertEqual(data["moyenne"], 14.0)

    def test_describe_erreur_liste_vide(self):
        reponse = self.client.post(
            "/stats/describe",
            json={"valeurs": []}  # liste vide → 400 attendu
        )
        self.assertEqual(reponse.status_code, 400)

    def test_describe_erreur_champ_manquant(self):
        reponse = self.client.post(
            "/stats/describe",
            json={}  # champ "valeurs" absent → 400 attendu
        )
        self.assertEqual(reponse.status_code, 400)

    def test_describe_erreur_valeurs_non_numeriques(self):
        reponse = self.client.post(
            "/stats/describe",
            json={"valeurs": [1, 2, "abc"]}  # texte non convertible en float → 400 attendu
        )
        self.assertEqual(reponse.status_code, 400)

    # --- /stats/correlation ---

    def test_correlation_succes(self):
        reponse = self.client.post(
            "/stats/correlation",
            json={"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]}  # relation linéaire parfaite → r = 1.0
        )
        self.assertEqual(reponse.status_code, 200)
        data = reponse.get_json()
        self.assertAlmostEqual(data["coefficient_pearson"], 1.0, places=2)  # assertAlmostEqual car les flottants ont des imprécisions, places=2 = précision à 2 décimales

    def test_correlation_tailles_differentes(self):
        reponse = self.client.post(
            "/stats/correlation",
            json={"x": [1, 2, 3], "y": [1, 2]}  # x=3 valeurs, y=2 valeurs → 400 attendu
        )
        self.assertEqual(reponse.status_code, 400)

    def test_correlation_serie_trop_courte(self):
        reponse = self.client.post(
            "/stats/correlation",
            json={"x": [1], "y": [1]}  # 1 seule valeur par série → corrélation impossible → 400 attendu
        )
        self.assertEqual(reponse.status_code, 400)

    # --- /stats/test_normalite ---

    def test_normalite_succes(self):
        reponse = self.client.post(
            "/stats/test_normalite",
            json={"valeurs": [12.5, 14.2, 13.8, 15.1, 11.9, 13.0, 14.5]}
        )
        self.assertEqual(reponse.status_code, 200)
        data = reponse.get_json()
        self.assertIn("statistique", data)    # assertIn vérifie qu'une clé est présente dans le dictionnaire
        self.assertIn("p_value", data)
        self.assertIn("interpretation", data)

    def test_normalite_erreur_trop_peu_valeurs(self):
        reponse = self.client.post(
            "/stats/test_normalite",
            json={"valeurs": [1, 2]}  # moins de 3 valeurs → Shapiro invalide → 400 attendu
        )
        self.assertEqual(reponse.status_code, 400)

    # --- /stats/test_student ---

    def test_student_succes(self):
        reponse = self.client.post(
            "/stats/test_student",
            json={"groupe1": [10, 12, 11, 13, 9], "groupe2": [15, 16, 14, 17, 15]}
        )
        self.assertEqual(reponse.status_code, 200)
        data = reponse.get_json()
        self.assertIn("t_statistique", data)
        self.assertIn("p_value", data)
        self.assertIn("interpretation", data)
        self.assertIn("moyenne_groupe1", data)
        self.assertIn("moyenne_groupe2", data)

    def test_student_erreur_groupe_trop_petit(self):
        reponse = self.client.post(
            "/stats/test_student",
            json={"groupe1": [10], "groupe2": [15, 16, 14]}  # groupe1 a 1 seule valeur → 400 attendu
        )
        self.assertEqual(reponse.status_code, 400)


if __name__ == "__main__":  # s'exécute seulement si on lance directement "python test_app.py"
    unittest.main()  # lance tous les tests automatiquement
