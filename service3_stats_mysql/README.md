# Service 3 — Statistiques depuis MySQL

Microservice Flask exposant des fonctions statistiques calculées sur des données stockées en base **MySQL**, contrairement au Service 2 qui reçoit les données directement en JSON. Le service utilise **NumPy** pour les calculs descriptifs et **SciPy** pour les tests statistiques, ainsi qu'une interface web simple (Blueprint `ui`) pour visualiser les résultats.

**Port :** `5003`
**Responsable :** Bryan
**Branche de développement :** `feature/s3-init`

---

## 📦 Installation

```bash
cd service3_stats_mysql
python -m venv venv
source venv/Scripts/activate    # Windows (Git Bash)
# ou : venv\Scripts\activate    # Windows (CMD)
# ou : source venv/bin/activate # Linux/Mac

pip install flask numpy scipy mysql-connector-python python-dotenv
```

## 🔐 Configuration de la base de données

Crée un fichier `.env` à la racine du service (⚠️ **ne pas committer ce fichier**, il doit être dans `.gitignore`) :

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=flask_user
DB_PASSWORD=votre_mot_de_passe
DB_NAME=flask_stats
SECRET_KEY=une_cle_secrete
```

La table `donnees` doit déjà exister (voir `sql/init_db.sql` à la racine du projet, partagé avec le Service 4).

## ▶️ Lancement du serveur

```bash
python app.py
```

Le serveur démarre sur `http://localhost:5003`. Ouvre `http://localhost:5003/` pour accéder à l'interface web listant les séries disponibles.

---

## 📋 Routes disponibles

### `GET /`
Page d'accueil (interface web via le Blueprint `ui`) — affiche les séries disponibles (`serie_A`, `serie_B`, `serie_C`, `serie_unitaire`).

### `GET /db/stats/describe`
Calcule les statistiques descriptives d'une série stockée en base.

**Paramètre :** `serie` (nom de la série à analyser)

**Exemple :**
