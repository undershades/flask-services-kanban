-- init_db.sql
CREATE DATABASE IF NOT EXISTS flask_stats
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE flask_stats;
CREATE TABLE IF NOT EXISTS donnees (
	id      	INT AUTO_INCREMENT PRIMARY KEY,
	nom_serie   VARCHAR(100)   NOT NULL,
	valeur  	DECIMAL(12,4)  NOT NULL,
	categorie   VARCHAR(50)	DEFAULT NULL,
	date_mesure DATE       	DEFAULT NULL,
	created_at  TIMESTAMP  	DEFAULT CURRENT_TIMESTAMP
);
