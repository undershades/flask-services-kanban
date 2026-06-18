# db.py 
import mysql.connector 
from dotenv import load_dotenv 
import os 
load_dotenv()
def get_connection():    
    """Retourne une connexion MySQL à partir des variables d'environnement."""     
    return mysql.connector.connect( host=os.getenv('DB_HOST', 'localhost'), 
                                    port=int(os.getenv('DB_PORT', 3306)),    
                                    user=os.getenv('DB_USER'),        
                                    password=os.getenv('DB_PASSWORD'),    
                                    database=os.getenv('DB_NAME')    
                                )

def fetch_series(nom_serie):    
    """Récupère toutes les valeurs d'une série depuis la table donnees."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
                 'SELECT valeur FROM donnees WHERE nom_serie = %s ORDER BY date_mesure',
        (nom_serie,)
                  )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    if not rows:
        raise ValueError(f"Aucune donnée trouvée pour la série '{nom_serie}'")
    return [float(row[0]) for row in rows]
