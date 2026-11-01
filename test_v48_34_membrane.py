#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V48.37 — CLÔTURE : VIABILITÉ SOUS STRESS VS CAPACITÉ DE RÉCUPÉRATION
====================================================================
Corrections finales :
- Calcul de D_realisee strictement égal à la perte appliquée (self.etat - x_moins).
- Séparation des métriques : F_min (résistance) et F_final (récupération).
- Double taux de viabilité : Survie pendant le stress vs Survie après récupération.
"""
from __future__ import annotations
import time
from dataclasses import dataclass
import numpy as np
import warnings

warnings.filterwarnings("default")

@dataclass(frozen=True)
class Config:
    n_graines: int = 100
    n_stress: int = 100
    n_recup: int = 20
    seed: int = 42
    
    doses_cibles: np.ndarray = None 
    alphas: np.ndarray = None
    
    seuil: float = 0.5
    seuil_defaillance: float = 0.25
    decay: float = 0.10
    
    etat_initial: tuple = (1.0, 1.0)
    gain: float = 0.8
    bruit_interne: float = 0.01

    def __post_init__(self):
        object.__setattr__(self, 'doses_cibles', np.linspace(1.0, 10.0, 10))
        object.__setattr__(self, 'alphas', np.array([0.0, 0.10, 0.20]))

def build_W(alpha):
    return np.array([
        [0.8 - alpha, 0.2 - alpha],
        [0.2 + alpha, 0.8 + alpha]
    ])

class Defense:
    def __init__(self, etat0, W, decay, seuil, gain):
        self.etat = np.asarray(etat0, dtype=float).copy()
        self.W = np.asarray(W, dtype=float)
        self.decay = decay
        self.seuil = seuil
        self.gain = gain

    def run(self, P, bruit):
        n = P.shape[0]
        F_min = self.etat[0] * self.etat[1]
        D_realisee = 0.0
        
        for t in range(n):
            perte_demandee = np.minimum(P[t] * self.decay, 1.0)
            x_moins = np.clip(self.etat - perte_demandee, 0.0, 1.0)
            
            # Correction : La dose réalisée est EXACTEMENT ce qu'on a perdu
            D_realisee += np.sum(self.etat - x_moins)
            
            couple = self.W @ x_moins
            besoin = np.maximum(0.0, self.seuil - couple)
            correction = self.gain * besoin
            
            bruit_eff = bruit[t] * self.etat * (1.0 - self.etat)
            self.etat = np.clip(couple + correction + bruit_eff, 0.0, 1.0)
            
            F = self.etat[0] * self.etat[1]
            F_min = min(F_min, F)
            
        F_final = self.etat[0] * self.etat[1]
        return F_min, F_final, D_realisee

def generer_profil(mode, n_stress, n_recup, dose_cible, cfg):
    n_total = n_stress + n_recup
    P = np.zeros((n_total, 2))
    k = dose_cible / 10.0
    
    if mode == "chronique":
        P[:n_stress, 0] = 1.0 * k
    elif mode == "aigu":
        idx = np.linspace(0, n_stress - 1, 10, dtype=int)
        P[idx, 0] = 10.0 * k
        
    return P

def wilson_interval(k, n, z=1.96):
    if n == 0: return 0.0, 0.0
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2*n)) / denom
    marge = (z / denom) * np.sqrt(p*(1-p)/n + z**2/(4*n**2))
    return max(0, centre - marge), min(1, centre + marge)

def run_plan(cfg):
    rng_master = np.random.default_rng(cfg.seed)
    seeds = rng_master.integers(0, 2**31 - 1, size=cfg.n_graines)
    etat0 = np.asarray(cfg.etat_initial, dtype=float)
    
    modes = ["chronique", "aigu"]
    n_total = cfg.n_stress + cfg.n_recup
    
    # On stocke F_min, F_final et D_realisee
    resultats = {m: {a: {"F_min": np.zeros((cfg.n_graines, len(cfg.doses_cibles))),
                        "F_final": np.zeros((cfg.n_graines, len(cfg.doses_cibles))),
                        "D_real": np.zeros((cfg.n_graines, len(cfg.doses_cibles)))} 
                     for a in cfg.alphas} for m in modes}

    for i in range(cfg.n_graines):
        rng = np.random.default_rng(int(seeds[i]))
        bruit = rng.normal(0, cfg.bruit_interne, size=(n_total, 2))
        
        for j, dose in enumerate(cfg.doses_cibles):
            for mode in modes:
                P = generer_profil(mode, cfg.n_stress, cfg.n_recup, dose, cfg)
                
                for a in cfg.alphas:
                    W = build_W(a)
                    sys = Defense(etat0, W, cfg.decay, cfg.seuil, cfg.gain)
                    fmin, ffinal, d_real = sys.run(P, bruit)
                    
                    resultats[mode][a]["F_min"][i, j] = fmin
                    resultats[mode][a]["F_final"][i, j] = ffinal
                    resultats[mode][a]["D_real"][i, j] = d_real
                    
    return resultats

def afficher_matrice(resultats, cfg):
    print("\n" + "=" * 95)
    print("V48.37 — FRONTIÈRE DE VIABILITÉ (La Membrane)")
    print("=" * 95)
    
    for mode in ["chronique", "aigu"]:
        print(f"\n>>> STRESS {mode.upper()}")
        
        # En-tête
        header = f"  {'Dose':>4} | " + " | ".join([f"  Alpha={a:.2f} [Stress | Récup] " for a in cfg.alphas])
        print(header)
        print("  " + "-" * (len(header) - 2))
        
        for j, dose in enumerate(cfg.doses_cibles):
            row = f"  {dose:>4.1f} | "
            for a in cfg.alphas:
                F_min_data = resultats[mode][a]["F_min"][:, j]
                F_final_data = resultats[mode][a]["F_final"][:, j]
                
                # Taux de survie pendant le stress
                survie_stress = np.mean(F_min_data >= cfg.seuil_defaillance) * 100
                # Taux de survie après récupération
                survie_recup = np.mean(F_final_data >= cfg.seuil_defaillance) * 100
                
                # Symbole pour le stress
                sym_stress = "░" if survie_stress < 50 else "▒" if survie_stress < 100 else "█"
                # Symbole pour la récupération
                sym_recup = "░" if survie_recup < 50 else "▒" if survie_recup < 100 else "█"
                
                row += f"   {survie_stress:>3.0f}%{sym_stress} | {survie_recup:>3.0f}%{sym_recup}  |"
            print(row)

    print("\n--- VÉRIFICATION DE LA DOSE RÉALISÉE (Moyenne) ---")
    for mode in ["chronique", "aigu"]:
        d_imp = cfg.doses_cibles[-1]
        d_real = np.mean(resultats[mode][0.0]["D_real"][:, -1])
        print(f"  Mode {mode:<9} (Dose imposée={d_imp:.1f}) : Dose réalisée = {d_real:.2f}")

if __name__ == "__main__":
    cfg = Config()
    print("Démarrage V48.37 — Conclusion...")
    debut = time.perf_counter()
    res = run_plan(cfg)
    afficher_matrice(res, cfg)
    print("\n" + "=" * 95)
    print(f"FIN — Durée : {time.perf_counter() - debut:.2f} s")
    print("=" * 95)
