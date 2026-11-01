#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V48.20 — INVARIANTS RELATIONNELS ET PROTOCOLE MIROIR
====================================================
Objectif : Séparer l'effet de la structure de couplage de l'effet de la 
direction de la perturbation. Mesurer la persistance de la signature.
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
    decay: float = 0.10
    
    # 3 Matrices : OFF (identité), SYM (conservative), ASYM_CONS (conservative)
    # Pour ASYM_CONS : colonnes somment à 1.0. W[0,1]=0.1 (flux 2->1), W[1,0]=0.3 (flux 1->2)
    matrices: dict = None
    
    etat_initial: tuple = (1.0, 0.6)
    gain: float = 0.8 # On fixe le gain à 0.8 pour voir la structure sous compensation forte

    def __post_init__(self):
        # On ne peut pas définir de dict dans un frozen dataclass, on le fait ici
        object.__setattr__(self, 'matrices', {
            "OFF": ((1.0, 0.0), (0.0, 1.0)),
            "SYM": ((0.8, 0.2), (0.2, 0.8)),
            "ASYM_CONS": ((0.7, 0.1), (0.3, 0.9)) # Matrice conservative asymétrique
        })

class Defense:
    def __init__(self, etat0, W, decay, seuil, gain):
        self.etat = np.asarray(etat0, dtype=float).copy()
        self.W = np.asarray(W, dtype=float)
        self.decay = decay
        self.seuil = seuil
        self.gain = gain

    def run(self, perturbations):
        n = perturbations.shape[0]
        flux_1_vers_2 = np.zeros(n) # W[1,0]
        flux_2_vers_1 = np.zeros(n) # W[0,1]
        omega_t = np.zeros(n)
        
        for t in range(n):
            perte = np.minimum(perturbations[t] * self.decay, 1.0)
            x_moins = np.clip(self.etat - perte, 0.0, 1.0)
            
            if not np.array_equal(self.W, np.eye(2)):
                f12 = self.W[0, 1] * x_moins[1]
                f21 = self.W[1, 0] * x_moins[0]
                flux_1_vers_2[t] = f21
                flux_2_vers_1[t] = f12
                
                total = f21 + f12
                if total > 1e-8:
                    omega_t[t] = (f21 - f12) / total
            
            couple = self.W @ x_moins
            besoin = np.maximum(0.0, self.seuil - couple)
            correction = self.gain * besoin
            self.etat = np.clip(couple + correction, 0.0, 1.0)

        # 1. Asymétrie Cumulée Globale (Omega_G)
        total_12 = np.sum(flux_2_vers_1)
        total_21 = np.sum(flux_1_vers_2)
        if (total_12 + total_21) > 1e-8:
            omega_G = (total_21 - total_12) / (total_12 + total_21)
        else:
            omega_G = 0.0
            
        # 2. Asymétrie Temporelle Moyenne (Omega_T)
        omega_T = np.mean(omega_t)
        
        # 3. Persistance (fraction de temps où le signe instantané = signe global)
        # On ignore les cycles où le flux total est nul ou trop faible
        valid_cycles = (flux_1_vers_2 + flux_2_vers_1) > 1e-8
        if np.any(valid_cycles) and omega_G != 0:
            sign_global = np.sign(omega_G)
            sign_instant = np.sign(omega_t[valid_cycles])
            persistance = np.mean(sign_instant == sign_global)
        else:
            persistance = np.nan

        return {
            "Omega_G": omega_G,
            "Omega_T": omega_T,
            "Persistance": persistance,
            "Omega_Std": np.std(omega_t[valid_cycles]) if np.any(valid_cycles) else 0.0
        }

def run_plan(cfg):
    rng_master = np.random.default_rng(cfg.seed)
    seeds = rng_master.integers(0, 2**31 - 1, size=cfg.n_graines)
    etat0 = np.asarray(cfg.etat_initial, dtype=float)
    
    # resultats[matrice][cible_perturbation] = liste de dicts
    resultats = {k: {1: [], 2: []} for k in cfg.matrices.keys()}

    for i in range(cfg.n_graines):
        rng = np.random.default_rng(int(seeds[i]))
        a = (0.0 - cfg.mu_perturbation) / cfg.sigma_perturbation
        
        p_base = truncnorm.rvs(a, np.inf, loc=cfg.mu_perturbation, scale=cfg.sigma_perturbation, size=cfg.n_cycles, random_state=rng)
        
        # Perturbation 1 (frappe le compartiment 1)
        P1 = np.column_stack((p_base, np.zeros(cfg.n_cycles)))
        # Perturbation 2 (frappe le compartiment 2)
        P2 = np.column_stack((np.zeros(cfg.n_cycles), p_base))

        for nom, W_tuple in cfg.matrices.items():
            W = np.asarray(W_tuple, dtype=float)
            
            # Test Perturbation 1
            sys1 = Defense(etat0, W, cfg.decay, cfg.seuil, cfg.gain)
            resultats[nom][1].append(sys1.run(P1))
            
            # Test Perturbation 2
            sys2 = Defense(etat0, W, cfg.decay, cfg.seuil, cfg.gain)
            resultats[nom][2].append(sys2.run(P2))
                    
    return resultats

def analyse(resultats, cfg):
    print("\n" + "=" * 95)
    print("V48.20 — PROTOCOLE MIROIR ET INVARIANTS RELATIONNELS")
    print(f"(Gain = {cfg.gain}, Decay = {cfg.decay}, Etat Initial = {cfg.etat_initial})")
    print("=" * 95)
    
    for nom in cfg.matrices.keys():
        print(f"\n>>> MATRICE : {nom}")
        if nom != "OFF":
            W = np.array(cfg.matrices[nom])
            print(f"    (W = {W.tolist()})")
        
        print(f"{'Perturbation':>14} | {'Omega_G (Cumul)':>15} | {'Omega_T (Moy)':>13} | {'Persistance':>11} | {'Std Dev':>8}")
        print("-" * 75)
        
        for cible, label in [(1, "P1 (sur C1)"), (2, "P2 (sur C2)")]:
            metrics = resultats[nom][cible]
            og = np.mean([m["Omega_G"] for m in metrics])
            ot = np.mean([m["Omega_T"] for m in metrics])
            pers = np.nanmean([m["Persistance"] for m in metrics])
            std = np.mean([m["Omega_Std"] for m in metrics])
            
            # Si la matrice est OFF, on affiche N/A pour les flux
            if nom == "OFF":
                print(f"{label:>14} | {'N/A':>15} | {'N/A':>13} | {'N/A':>11} | {'N/A':>8}")
            else:
                print(f"{label:>14} | {og:>+15.3f} | {ot:>+13.3f} | {pers:>11.2%} | {std:>8.3f}")
                
    print("\nInterprétation :")
    print("- Omega_G et Omega_T > 0 : Flux dominant de C1 vers C2.")
    print("- Persistance : % de cycles où le flux instantané respecte la direction globale.")
    print("- Le protocole miroir (P1 vs P2) permet de voir si l'asymétrie vient de la perturbation ou de la matrice.")

if __name__ == "__main__":
    cfg = Config()
    print("Démarrage V48.20 — Protocole Miroir...")
    debut = time.perf_counter()
    res = run_plan(cfg)
    analyse(res, cfg)
    print("\n" + "=" * 95)
    print(f"FIN — Durée : {time.perf_counter() - debut:.2f} s")
    print("=" * 95)
