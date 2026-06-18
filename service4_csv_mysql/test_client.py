import requests
import io

BASE_URL = "http://localhost:5004"

def executer_tests():
    print("")
    #  TEST 1 : Vérifier le cas où la clé 'file' est manquante
    print("[Test 1] Envoi d'une requête sans la clé 'file'...")
    reponse = requests.post(f"{BASE_URL}/upload/csv")
    
    assert reponse.status_code == 400, f"Erreur attendue 400, reçu {reponse.status_code}"
    assert "clé \"file\" manquante" in reponse.json()['erreur'], "Le message d'erreur ne correspond pas"
    print(" Réussite : L'API bloque bien les requêtes sans fichier (Code 400).")


    #  TEST 2 : Vérifier le cas où le nom du fichier est vide
    print("\n[Test 2] Envoi d'un fichier avec un nom vide...")
    fichiers_nom_vide = {'file': ('', b'contenu', 'text/csv')}
    reponse = requests.post(f"{BASE_URL}/upload/csv", files=fichiers_nom_vide)
    
    assert reponse.status_code == 400, f"Erreur attendue 400, reçu {reponse.status_code}"
    assert reponse.json()['erreur'] == "Nom de fichier vide", "Le message d'erreur ne correspond pas"
    print(" Réussite : L'API refuse bien les fichiers sans nom (Code 400).")


    #  TEST 3 : Vérifier le blocage des mauvaises extensions (ex: .txt)
    print("\n[Test 3] Envoi d'un fichier avec une mauvaise extension (.txt)...")
    fichiers_txt = {'file': ('rapport.txt', b'nom_serie,valeur\ntest,10', 'text/plain')}
    reponse = requests.post(f"{BASE_URL}/upload/csv", files=fichiers_txt)
    
    assert reponse.status_code == 400, f"Erreur attendue 400, reçu {reponse.status_code}"
    assert "Seuls les fichiers .csv sont acceptés" in reponse.json()['erreur'], "Le message d'erreur ne correspond pas"
    print(" Réussite : L'API rejette bien les fichiers non-CSV (Code 400).")


    #  TEST 4 : Vérifier l'erreur si des colonnes obligatoires manquent (Question Q4)
    print("\n[Test 4] Envoi d'un CSV sans la colonne obligatoire 'valeur'...")
    csv_invalide = b"nom_serie,categorie,date_mesure\nserie_test,pression,2026-01-01"
    fichiers_sans_valeur = {'file': ('test_missing.csv', io.BytesIO(csv_invalide), 'text/csv')}
    reponse = requests.post(f"{BASE_URL}/upload/csv", files=fichiers_sans_valeur)
    
    assert reponse.status_code == 400, f"Erreur attendue 400, reçu {reponse.status_code}"
    assert reponse.json()['erreur'] == "Colonnes obligatoires manquantes", "Le message d'erreur ne correspond pas"
    assert 'valeur' in reponse.json()['manquantes'], "La colonne 'valeur' devrait être listée comme manquante"
    print(" Réussite : L'API détecte l'absence de la colonne 'valeur' (Code 400).")


    #  TEST 5 : Vérifier le succès d'un upload avec un bon fichier CSV
    print("\n[Test 5] Envoi d'un CSV valide (Happy Path)...")
    csv_valide = b"nom_serie,valeur,categorie,date_mesure\nserie_unitaire,42.5,test,2026-06-18"
    fichiers_valides = {'file': ('donnees_test.csv', io.BytesIO(csv_valide), 'text/csv')}
    reponse = requests.post(f"{BASE_URL}/upload/csv", files=fichiers_valides)
    
    assert reponse.status_code == 201, f"Erreur attendue 201, reçu {reponse.status_code}"
    assert reponse.json()['statut'] == "success", "Le statut de réponse devrait être 'success'"
    assert reponse.json()['lignes_inserees'] == 1, "Il devrait y avoir 1 ligne insérée"
    print(" Réussite : Le fichier CSV valide a bien été traité et inséré (Code 201).")


    # TEST 6 : Vérifier le fonctionnement de la route GET /upload/series
    print("\n[Test 6] Test de la route GET /upload/series...")
    reponse = requests.get(f"{BASE_URL}/upload/series")
    
    assert reponse.status_code == 200, f"Erreur attendue 200, reçu {reponse.status_code}"
    data = reponse.json()
    assert 'series' in data, "La réponse doit contenir la clé 'series'"
    assert 'total' in data, "La réponse doit contenir la clé 'total'"
    print(f" Réussite : La liste des séries a été récupérée. Nombre total de séries : {data['total']} (Code 200).")

    print("")
    print(" tous les tests sont passés avec succès !")
    print("")

if __name__ == '__main__':
    try:
        executer_tests()
    except AssertionError as e:
        print(f"\n ÉCHEC DU TEST : {e}")
    except requests.exceptions.ConnectionError:
        print("\n ERREUR : Impossible de se connecter au serveur. Lance ton code Flask avant !")