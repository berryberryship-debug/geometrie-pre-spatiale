#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V48.29 — AUDIT DE RÉCUPÉRATION ET DE TRANSITION (Corrections V48.28)
====================================================================
Corrections appliquées :
- Séparation stricte des phases : choc vs récupération.
- T_def gère les observations censurées avec np.nan.
- Récupération relative : (F_post - F_choc) / (1 - F_choc).
- Effort défensif séparé : C_choc vs C_recup.
- Bootstrap apparié pour les différences entre topologies (ASYM - SYM, etc.).
- Bootstrap des graines pour l'incertitude sur mu_critique.
"""
from __future__ import annotations
import time
from dataclasses import dataclass
import numpy as np
from scipy.stats import truncnorm
import warnings

@dataclass(frozen=True)
class Config:
    n_graines: int = 50
    n_cycles_choc: int = 100
    n_cycles_recup: int = 100 # Allongé pour observer la vraie récupération
    seed: int = 42
    
    mu_values: np.ndarray = None
    sigma_perturbation: float = 1.5
    seuil: float = 0.5
    seuil_defaillance: float = 0.25
    decay: float = 0.10
    
    matrices: dict = None
    etat_initial: tuple = (1.0, 1.0)
    gain: float = 0.8
    bruit_fond: float = 0.02

    def __post_init__(self):
        object.__setattr__(self, 'mu_values', np.linspace(1.0, 10.0, 30))
        object.__setattr__(self, 'matrices', {
            "OFF": ((1.0, 0.0), (0.0, 1.0)),
            "SYM": ((0.8, 0.2), (0.2, 0.8)),
            "ASYM": ((0.7, 0.1), (0.3, 0.9))
        })

class Defense:
    def __init__(self, etat0, W, decay, seuil, gain, seuil_def):
        self.etat = np.asarray(etat0, dtype=float).copy()
        self.W = np.asarray(W, dtype=float)
        self.decay = decay
        self.seuil = seuil
        self.gain = gain
        self.seuil_def = seuil_def

    def run_phase(self, P, bruit):
        n = P.shape[0]
        F_min = 1.0
        T_def = np.nan  # NaN par défaut (censuré)
        C_cum = 0.0
        
        for t in range(n):
            perte = np.minimum(P[t] * self.decay, 1.0)
            x_moins = np.clip(self.etat - perte, 0.0, 1.0)
            
            couple = self.W @ x_moins
            besoin = np.maximum(0.0, self.seuil - couple)
            correction = self.gain * besoin
            bruit_effectif = bruit[t] * self.etat * (1.0 - self.etat)
            
            self.etat = np.clip(couple + correction + bruit_effectif, 0.0, 1.0)
            
            F = self.etat[0] * self.etat[1]
            F_min = min(F_min, F)
            
            # Si on franchit le seuil et qu'on ne l'a jamais franchi
            if np.isnan(T_def) and F < self.seuil_def:
                T_def = t
                
            C_cum += np.sum(correction)
            
        F_final = self.etat[0] * self.etat[1]
        return F_min, F_final, T_def, C_cum

def ic95_bootstrap(donnees, n_boot=2000, alpha=0.05):
    """Bootstrap sur des données indépendantes (1D)."""
    d = np.asarray(donnees)
    d = d[~np.isnan(d)]
    if len(d) < 2: return (np.nan, np.nan)
    rng = np.random.default_rng(42)
    means = [np.mean(rng.choice(d, size=len(d), replace=True)) for _ in range(n_boot)]
    return np.percentile(means, 100*alpha/2), np.percentile(means, 100*(1-alpha/2))

def run_plan(cfg):
    rng_master = np.random.default_rng(cfg.seed)
    seeds = rng_master.integers(0, 2**31 - 1, size=cfg.n_graines)
    etat0 = np.asarray(cfg.etat_initial, dtype=float)
    
    # Structure : resultats[matrice][metric] = array(n_graines, n_mu)
    resultats = {nom: {
        "F_min": np.zeros((cfg.n_graines, len(cfg.mu_values))),
        "F_choc": np.zeros((cfg.n_graines, len(cfg.mu_values))),
        "F_recup": np.zeros((cfg.n_graines, len(cfg.mu_values))),
        "T_def": np.zeros((cfg.n_graines, len(cfg.mu_values))),
        "C_choc": np.zeros((cfg.n_graines, len(cfg.mu_values))),
        "C_recup": np.zeros((cfg.n_graines, len(cfg.mu_values)))
    } for nom in cfg.matrices}

    for i in range(cfg.n_graines):
        rng = np.random.default_rng(int(seeds[i]))
        U = rng.uniform(0, 1, size=cfg.n_cycles_choc)
        bruit = rng.normal(0, cfg.bruit_fond, size=(cfg.n_cycles_choc + cfg.n_cycles_recup, 2))
        
        for j, mu in enumerate(cfg.mu_values):
            a = (0.0 - mu) / cfg.sigma_perturbation
            p_vals = truncnorm.ppf(U, a, np.inf, loc=mu, scale=cfg.sigma_perturbation)
            P_choc = np.column_stack((p_vals, np.zeros(cfg.n_cycles_choc)))
            P_vide = np.zeros((cfg.n_cycles_recup, 2))
            
            for nom, W_tuple in cfg.matrices.items():
                W = np.asarray(W_tuple, dtype=float)
                sys = Defense(etat0, W, cfg.decay, cfg.seuil, cfg.gain, cfg.seuil_defaillance)
                
                # 1. Phase de choc
                F_min, F_choc, T_def, C_choc = sys.run_phase(P_choc, bruit[:cfg.n_cycles_choc])
                
                # 2. Phase de récupération
                _, F_recup, _, C_recup = sys.run_phase(P_vide, bruit[cfg.n_cycles_choc:])
                
                resultats[nom]["F_min"][i, j] = F_min
                resultats[nom]["F_choc"][i, j] = F_choc
                resultats[nom]["F_recup"][i, j] = F_recup
                resultats[nom]["T_def"][i, j] = T_def # Contient des NaN si pas de déf
                resultats[nom]["C_choc"][i, j] = C_choc
                resultats[nom]["C_recup"][i, j] = C_recup
                
    return resultats

def trouver_mu_critique(F_min_matrix, mu_values, n_boot=1000):
    """Estime mu_critique par bootstrap sur les graines et renvoie l'IC 95%."""
    n_graines = F_min_matrix.shape[0]
    rng = np.random.default_rng(42)
    mu_crits = []
    
    for _ in range(n_boot):
        # Bootstrap des graines
        idx = rng.integers(0, n_graines, size=n_graines)
        mean_F = np.mean(F_min_matrix[idx, :], axis=0)
        pente = np.gradient(mean_F, mu_values)
        mu_c = mu_values[np.argmin(pente)]
        mu_crits.append(mu_c)
        
    mu_moy = np.mean(mu_crits)
    lo, hi = np.percentile(mu_crits, [2.5, 97.5])
    return mu_moy, lo, hi

def analyse(resultats, cfg):
    print("\n" + "=" * 95)
    print("V48.29 — AUDIT DE RÉCUPÉRATION ET DE TRANSITION")
    print("=" * 95)
    
    # 1. Point critique et incertitude
    print("\n--- 1. POINT CRITIQUE (Bascule de F_min) ---")
    for nom in cfg.matrices.keys():
        mu_moy, lo, hi = trouver_mu_critique(resultats[nom]["F_min"], cfg.mu_values)
        print(f"  Matrice {nom:>4} : mu_critique = {mu_moy:.2f} [IC 95%: {lo:.2f}, {hi:.2f}]")

    # 2. Comparaison appariée (Bootstrap sur les différences)
    print("\n--- 2. EFFET TOPOLOGIQUE (ASYM vs SYM) ---")
    diff_Fmin = resultats["ASYM"]["F_min"] - resultats["SYM"]["F_min"]
    # Moyenne de la différence sur tous les mu et toutes les graines
    mean_diff = np.mean(diff_Fmin)
    lo, hi = ic95_bootstrap(diff_Fmin.flatten()) # On bootstrap les différences individuelles
    print(f"  Différence moyenne de F_min (ASYM - SYM) : {mean_diff:+.4f} [IC 95%: {lo:+.4f}, {hi:+.4f}]")
    if lo > 0 or hi < 0:
        print("  -> Différence SIGNIFICATIVE : l'asymétrie protège mieux que la symétrie.")
    else:
        print("  -> Différence NON SIGNIFICATIVE.")

    # 3. Récupération relative
    print("\n--- 3. CAPACITÉ DE RÉCUPÉRATION RELATIVE ---")
    for nom in cfg.matrices.keys():
        F_choc = resultats[nom]["F_choc"]
        F_recup = resultats[nom]["F_recup"]
        
        # R_relatif = (F_recup - F_choc) / (1 - F_choc)
        # On évite la division par zéro si F_choc = 1
        denom = 1.0 - F_choc
        with np.errstate(divide='ignore', invalid='ignore'):
            R_rel = np.where(denom > 1e-6, (F_recup - F_choc) / denom, np.nan)
        
        mean_R = np.nanmean(R_rel)
        lo, hi = ic95_bootstrap(R_rel.flatten())
        print(f"  Matrice {nom:>4} : Récupération relative moyenne = {mean_R*100:>6.2f}% [IC: {lo*100:.1f}%, {hi*100:.1f}%]")

    # 4. Défaillance censurée
    print("\n--- 4. DÉFAILLANCE (T_def) [Seuil F < 0.25] ---")
    for nom in cfg.matrices.keys():
        T_def = resultats[nom]["T_def"]
        # Compter combien de simulations ont échoué (T_def non NaN)
        taux_defaillance = np.mean(~np.isnan(T_def)) * 100
        print(f"  Matrice {nom:>4} : Taux de défaillance global = {taux_defaillance:.1f}% des cas.")

if __name__ == "__main__":
    cfg = Config()
    print("Démarrage V48.29 — Audit finalisé...")
    debut = time.perf_counter()
    res = run_plan(cfg)
    analyse(res, cfg)
    print("\n" + "=" * 95)
    print(f"FIN — Durée : {time.perf_counter() - debut:.2f} s")
    print("=" * 95)
