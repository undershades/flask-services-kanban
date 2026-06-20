import time
import random
from c_bridge import calculer_describe

N = 1_000_000


def moyenne_python(valeurs):
    return sum(valeurs) / len(valeurs)


def ecart_type_python(valeurs):
    m = moyenne_python(valeurs)
    variance = sum((v - m) ** 2 for v in valeurs) / len(valeurs)
    return variance ** 0.5


def benchmark():
    print("=" * 50)
    print(f"Génération de {N:,} valeurs aléatoires...")
    valeurs = [random.uniform(0, 1000) for _ in range(N)]
    print("Données prêtes.\n")

    # --- Python pur ---
    print("[Python pur] Calcul en cours...")
    debut = time.perf_counter()
    moyenne_py = moyenne_python(valeurs)
    ecart_py = ecart_type_python(valeurs)
    temps_python = time.perf_counter() - debut
    print(f"  Moyenne     : {moyenne_py:.4f}")
    print(f"  Écart-type  : {ecart_py:.4f}")
    print(f"  Temps       : {temps_python:.4f} secondes\n")

    # --- C / ctypes ---
    print("[C / ctypes] Calcul en cours...")
    debut = time.perf_counter()
    resultat_c = calculer_describe(valeurs)
    temps_c = time.perf_counter() - debut
    print(f"  Moyenne     : {resultat_c['moyenne']:.4f}")
    print(f"  Écart-type  : {resultat_c['ecart_type']:.4f}")
    print(f"  Temps       : {temps_c:.4f} secondes\n")

    # --- Comparaison ---
    gain = temps_python / temps_c if temps_c > 0 else float('inf')
    print("=" * 50)
    print(f"RÉSULTAT : le moteur C est {gain:.1f}x plus rapide que Python pur")
    print("=" * 50)


if __name__ == '__main__':
    benchmark()