#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V48.19 — INVARIANTS RELATIONNELS & SIGNATURE GÉOMÉTRIQUE
=========================================================
Objectif : Observer la persistance ou la reconfiguration de la structure
des échanges (transferts dirigés) sous perturbation.
"""
from __future__ import annotations
import time
from dataclasses import dataclass
import numpy as np
from scipy.stats import truncnorm
import warnings
warnings.filterwarnings("ignore")

@dataclass(frozen=True)
class Config:
    n_graines: int = 100
    n_cycles: int = 100
    seed: int = 42
    mu_perturbation: float = 5.0
    sigma_perturbation: float = 2.0
    seuil: float = 0.5
    
    # On teste 3 états : sans couplage, couplage symétrique, couplage asymétrique
    W_off: tuple = ((1.0, 0.0), (0.0, 1.0))
    W_sym: tuple = ((0.8, 0.2), (0.2, 0.8))
    W_asym: tuple = ((0.9, 0.1), (0.3, 0.7))
    
    etat_initial: tuple = (1.0, 0.6)
    
    # On teste 2 régimes de compensation
    gains: tuple = (0.0, 0.8)

class Defense:
    def __init__(self, etat0, W, decay, seuil, gain):
        self.etat = np.asarray(etat0, dtype=float).copy()
        self.W = np.asarray(W, dtype=float)
        self.decay = decay
        self.seuil = seuil
        self.gain = gain

    def run(self, perturbations):
        n = perturbations.shape[0]
        
        # Traçabilité de la signature relationnelle dans le temps
        flux_1_vers_2 = np.zeros(n)
        flux_2_vers_1 = np.zeros(n)
        omega_t = np.zeros(n)
        
        for t in range(n):
            perte = np.minimum(perturbations[t] * self.decay, 1.0)
            x_moins = np.clip(self.etat - perte, 0.0, 1.0)
            
            # Calcul des flux dirigés AVANT la compensation
            if not np.array_equal(self.W, np.eye(2)):
                f12 = self.W[0, 1] * x_moins[1] # 2 donne à 1
                f21 = self.W[1, 0] * x_moins[0] # 1 donne à 2
                flux_1_vers_2[t] = f12
                flux_2_vers_1[t] = f21
                
                total = f12 + f21
                if total > 1e-8:
                    omega_t[t] = (f21 - f12) / total # Positif = 1 pompe vers 2
                else:
                    omega_t[t] = 0.0
            
            couple = self.W @ x_moins
            besoin = np.maximum(0.0, self.seuil - couple)
            correction = self.gain * besoin
            self.etat = np.clip(couple + correction, 0.0, 1.0)

        # Bilan global sur les 100 cycles
        total_12 = np.sum(flux_1_vers_2)
        total_21 = np.sum(flux_2_vers_1)
        
        if (total_12 + total_21) > 1e-8:
            omega_global = (total_21 - total_12) / (total_12 + total_21)
        else:
            omega_global = 0.0
            
        # Mesure de la persistance de l'invariant (est-ce que Omega varie ?)
        omega_std = np.std(omega_t) if np.any(omega_t != 0) else 0.0

        return {
            "Omega_global": omega_global,
            "Omega_std": omega_std,
            "Flux_12": total_12,
            "Flux_21": total_21
        }

def run_plan(cfg):
    rng_master = np.random.default_rng(cfg.seed)
    seeds = rng_master.integers(0, 2**31 - 1, size=cfg.n_graines)
    
    matrices = {
        "OFF": np.asarray(cfg.W_off, dtype=float),
        "SYM": np.asarray(cfg.W_sym, dtype=float),
        "ASYM": np.asarray(cfg.W_asym, dtype=float)
    }
    
    etat0 = np.asarray(cfg.etat_initial, dtype=float)
    
    resultats = {k: {g: [] for g in cfg.gains} for k in matrices.keys()}

    for i in range(cfg.n_graines):
        rng = np.random.default_rng(int(seeds[i]))
        a = (0.0 - cfg.mu_perturbation) / cfg.sigma_perturbation
        
        # Perturbation sur le compartiment 1 (asymétrie de la source)
        p1 = truncnorm.rvs(a, np.inf, loc=cfg.mu_perturbation, scale=cfg.sigma_perturbation, size=cfg.n_cycles, random_state=rng)
        P = np.column_stack((p1, np.zeros(cfg.n_cycles))) 
        
        for d in [0.10]: # On fixe un decay modéré
            for g in cfg.gains:
                for nom, W in matrices.items():
                    sys = Defense(etat0, W, d, cfg.seuil, g)
                    res = sys.run(P)
                    resultats[nom][g].append(res)
                    
    return resultats

def analyse(resultats, cfg):
    print("\n" + "=" * 85)
    print("V48.19 — SIGNATURES RELATIONNELLES ET INVARIANTS GÉOMÉTRIQUES")
    print("(Perturbation concentrée sur Compartiment 1, Decay=0.10)")
    print("=" * 85)
    
    for g in cfg.gains:
        print(f"\n>>> RÉGIME DE COMPENSATION : Gain = {g}")
        print(f"{'MATRICE':>8} | {'Omega (Moy)':>11} | {'Omega (Std)':>11} | {'Flux 1->2':>10} | {'Flux 2->1':>10}")
        print("-" * 65)
        
        for nom in ["OFF", "SYM", "ASYM"]:
            metrics = resultats[nom][g]
            omega_m = np.mean([m["Omega_global"] for m in metrics])
            omega_s = np.mean([m["Omega_std"] for m in metrics])
            f12 = np.mean([m["Flux_12"] for m in metrics])
            f21 = np.mean([m["Flux_21"] for m in metrics])
            
            print(f"{nom:>8} | {omega_m:>+11.3f} | {omega_s:>11.3f} | {f12:>10.2f} | {f21:>10.2f}")

if __name__ == "__main__":
    cfg = Config()
    print("Démarrage V48.19 — Analyse des invariants...")
    debut = time.perf_counter()
    res = run_plan(cfg)
    analyse(res, cfg)
    print("\n" + "=" * 85)
    print(f"FIN — Durée : {time.perf_counter() - debut:.2f} s")
    print("=" * 85)
