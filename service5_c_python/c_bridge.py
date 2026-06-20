import ctypes
import os
import numpy as np


# Chemin vers la bibliothèque compilée
LIB_PATH = os.path.join(os.path.dirname(__file__), 'lib', 'stats.so')

# Charger la bibliothèque C
lib = ctypes.CDLL(LIB_PATH)

# --- Déclaration des types pour chaque fonction C ---
# argtypes = types des paramètres d'entrée
# restype  = type de la valeur de retour

# double moyenne(double* valeurs, int n)
lib.moyenne.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
lib.moyenne.restype = ctypes.c_double

# double ecart_type(double* valeurs, int n)
lib.ecart_type.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
lib.ecart_type.restype = ctypes.c_double

# double minimum(double* valeurs, int n)
lib.minimum.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
lib.minimum.restype = ctypes.c_double

# double maximum(double* valeurs, int n)
lib.maximum.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
lib.maximum.restype = ctypes.c_double

# double dot_product(double* a, double* b, int n)
lib.dot_product.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int]
lib.dot_product.restype = ctypes.c_double


def _to_c_array(valeurs):
    """Convertit une liste/array en tableau C de doubles via numpy (rapide)."""
    arr = np.asarray(valeurs, dtype=np.float64)
    n = len(arr)
    tableau = arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
    return tableau, n


def calculer_describe(valeurs):
    """Calcule moyenne, écart-type, min, max via le moteur C."""
    tableau, n = _to_c_array(valeurs)
    return {
        'n': n,
        'moyenne': round(lib.moyenne(tableau, n), 4),
        'ecart_type': round(lib.ecart_type(tableau, n), 4),
        'minimum': round(lib.minimum(tableau, n), 4),
        'maximum': round(lib.maximum(tableau, n), 4),
    }


def calculer_dot_product(a, b):
    """Calcule le produit scalaire entre deux vecteurs via le moteur C."""
    if len(a) != len(b):
        raise ValueError("Les deux vecteurs doivent avoir la même longueur")
    tableau_a, n = _to_c_array(a)
    tableau_b, _ = _to_c_array(b)
    return round(lib.dot_product(tableau_a, tableau_b, n), 4)