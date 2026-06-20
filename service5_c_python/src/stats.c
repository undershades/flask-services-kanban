#include <math.h>

// Calcule la moyenne d'un tableau de doubles
double moyenne(double* valeurs, int n) {
    double somme = 0.0;
    for (int i = 0; i < n; i++) {
        somme += valeurs[i];
    }
    return somme / n;
}

// Calcule l'écart-type (population, ddof=0)
double ecart_type(double* valeurs, int n) {
    double m = moyenne(valeurs, n);
    double somme_carres = 0.0;
    for (int i = 0; i < n; i++) {
        somme_carres += (valeurs[i] - m) * (valeurs[i] - m);
    }
    return sqrt(somme_carres / n);
}

// Trouve le minimum d'un tableau
double minimum(double* valeurs, int n) {
    double min_val = valeurs[0];
    for (int i = 1; i < n; i++) {
        if (valeurs[i] < min_val) {
            min_val = valeurs[i];
        }
    }
    return min_val;
}

// Trouve le maximum d'un tableau
double maximum(double* valeurs, int n) {
    double max_val = valeurs[0];
    for (int i = 1; i < n; i++) {
        if (valeurs[i] > max_val) {
            max_val = valeurs[i];
        }
    }
    return max_val;
}

// Calcule le produit scalaire (dot product) entre deux vecteurs
double dot_product(double* a, double* b, int n) {
    double resultat = 0.0;
    for (int i = 0; i < n; i++) {
        resultat += a[i] * b[i];
    }
    return resultat;
}