import numpy as np

def build_curie_weiss(n, beta, h=0.0):
    """
    Construit la matrice de transition (tridiagonale) pour la chaîne de Curie-Weiss.
    N = n + 1 états (k = 0 à n).
    """
    N = n + 1
    W = np.zeros((N, N))
    
    for k in range(N):
        # État k (nombre de spins "haut")
        # Probabilité d'aller vers k+1 (spin bas -> haut)
        if k < n:
            f_up = (2*k - n + 1) / n + h
            p_up = ((n - k) / n) * (1 / (1 + np.exp(-2 * beta * f_up)))
            W[k+1, k] = p_up
            
        # Probabilité d'aller vers k-1 (spin haut -> bas)
        if k > 0:
            f_down = (2*k - n - 1) / n + h
            p_down = (k / n) * (1 - 1 / (1 + np.exp(-2 * beta * f_down)))
            W[k-1, k] = p_down
            
        # Probabilité de rester sur place
        W[k, k] = 1.0 - np.sum(W[:, k])
        
    return W

def test_isospectrality(N, alpha_max=0.1, steps=5):
    n = N - 1
    beta = 1.0 # Point critique de Curie-Weiss
    W0 = build_curie_weiss(n, beta)
    
    print(f"--- Test de Curie-Weiss (N={N} états, beta={beta}) ---")
    
    for alpha in np.linspace(0, alpha_max, steps):
        # Similitude diagonale : S = I + alpha * diag(perturbation)
        # On choisit une perturbation qui modifie les poids sans casser la structure
        pert = np.linspace(-1, 1, N)
        S = np.diag(1 + alpha * pert)
        
        # Application de la transformation
        S_inv = np.linalg.inv(S)
        W_alpha = S @ W0 @ S_inv
        
        # 1. Vérification de la positivité (physique)
        min_val = np.min(W_alpha)
        is_positive = min_val >= 0
        
        # 2. Vérification de la conservation de la masse
        col_sums = np.sum(W_alpha, axis=0)
        is_stochastic = np.allclose(col_sums, 1.0, atol=1e-8)
        
        # 3. Calcul du gap spectral et de pi
        eigvals = np.linalg.eigvals(W_alpha)
        eigvals_sorted = sorted(np.abs(eigvals), reverse=True)
        gap = 1.0 - eigvals_sorted[1] # Le gap critique
        
        # Calcul de pi (vecteur propre pour lambda=1)
        _, eigvecs = np.linalg.eig(W_alpha)
        idx = np.argmin(np.abs(eigvals - 1))
        pi = np.real(eigvecs[:, idx])
        pi = pi / np.sum(pi)
        
        print(f"Alpha = {alpha:.3f} | Positif ? {is_positive} (min={min_val:.4f}) | Stochastique ? {is_stochastic}")
        print(f"  Gap critique = {gap:.5f} | pi(max) = {np.max(pi):.3f}")
        
        if not is_positive or not is_stochastic:
            print("  -> ECHEC : Matrice invalide.")
            break
    print("-" * 50)

if __name__ == "__main__":
    test_isospectrality(N=32)
    test_isospectrality(N=64)
