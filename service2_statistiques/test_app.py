import unittest
from app import app


class TestService2(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    # --- /stats/describe ---

    def test_describe_succes(self):
        reponse = self.client.post(
            "/stats/describe",
            json={"valeurs": [10, 12, 14, 16, 18]}
        )
        self.assertEqual(reponse.status_code, 200)
        data = reponse.get_json()
        self.assertEqual(data["n"], 5)
        self.assertEqual(data["moyenne"], 14.0)

    def test_describe_erreur_liste_vide(self):
        reponse = self.client.post(
            "/stats/describe",
            json={"valeurs": []}
        )
        self.assertEqual(reponse.status_code, 400)

    def test_describe_erreur_champ_manquant(self):
        reponse = self.client.post(
            "/stats/describe",
            json={}
        )
        self.assertEqual(reponse.status_code, 400)

    def test_describe_erreur_valeurs_non_numeriques(self):
        reponse = self.client.post(
            "/stats/describe",
            json={"valeurs": [1, 2, "abc"]}
        )
        self.assertEqual(reponse.status_code, 400)

    # --- /stats/correlation ---

    def test_correlation_succes(self):
        reponse = self.client.post(
            "/stats/correlation",
            json={"x": [1, 2, 3, 4, 5], "y": [2, 4, 6, 8, 10]}
        )
        self.assertEqual(reponse.status_code, 200)
        data = reponse.get_json()
        self.assertAlmostEqual(data["coefficient_pearson"], 1.0, places=2)

    def test_correlation_tailles_differentes(self):
        reponse = self.client.post(
            "/stats/correlation",
            json={"x": [1, 2, 3], "y": [1, 2]}
        )
        self.assertEqual(reponse.status_code, 400)

    def test_correlation_serie_trop_courte(self):
        reponse = self.client.post(
            "/stats/correlation",
            json={"x": [1], "y": [1]}
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
        self.assertIn("statistique", data)
        self.assertIn("p_value", data)
        self.assertIn("interpretation", data)

    def test_normalite_erreur_trop_peu_valeurs(self):
        reponse = self.client.post(
            "/stats/test_normalite",
            json={"valeurs": [1, 2]}
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
            json={"groupe1": [10], "groupe2": [15, 16, 14]}
        )
        self.assertEqual(reponse.status_code, 400)


if __name__ == "__main__":
    unittest.main()
