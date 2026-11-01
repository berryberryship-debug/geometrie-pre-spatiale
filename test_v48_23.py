#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V48.24 — HYSTÉRÉSIS QUASI-STATIQUE VS DYNAMIQUE
===============================================
Objectif : Tester si la boucle d'hystérésis persiste quand on augmente 
le temps de stabilisation (T).
Note sur la perturbation : mu est le paramètre de position de la loi normale.
La moyenne effective après troncature à 0 est supérieure à mu.
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
    n_graines: int = 50
    # Liste des temps de stabilisation (T) à tester
    T_list: tuple = (10, 50, 200) 
    
    seed: int = 42
    
    # Balayage paramétrique
    mu_min: float = 1.0
    mu_max: float = 8.0
    mu_pas: float = 0.5
    sigma_perturbation: float = 2.0
    
    seuil: float = 0.5
    decay: float = 0.10
    
    matrices: dict = None
    etat_initial: tuple = (1.0, 1.0)
    gain: float = 0.8
    bruit_fond: float = 0.02

    def __post_init__(self):
        object.__setattr__(self, 'matrices', {
            "SYM": ((0.8, 0.2), (0.2, 0.8)),
            "ASYM_CONS": ((0.7, 0.1), (0.3, 0.9))
        })

class Defense:
    def __init__(self, etat0, W, decay, seuil, gain):
        self.etat = np.asarray(etat0, dtype=float).copy()
        self.W = np.asarray(W, dtype=float)
        self.decay = decay
        self.seuil = seuil
        self.gain = gain
        self.clip_count = 0 # Compteur d'écrêtage

    def run_step(self, P, bruit):
        n = P.shape[0]
        flux_1_vers_2 = np.zeros(n)
        flux_2_vers_1 = np.zeros(n)
        
        for t in range(n):
            perte = np.minimum(P[t] * self.decay, 1.0)
            x_moins = np.clip(self.etat - perte, 0.0, 1.0)
            
            f12 = self.W[0, 1] * x_moins[1]
            f21 = self.W[1, 0] * x_moins[0]
            flux_1_vers_2[t] = f21
            flux_2_vers_1[t] = f12
            
            couple = self.W @ x_moins
            besoin = np.maximum(0.0, self.seuil - couple)
            correction = self.gain * besoin
            
            bruit_effectif = bruit[t] * self.etat * (1.0 - self.etat)
            etat_brut = couple + correction + bruit_effectif
            
            # Détection d'écrêtage
            if np.any(etat_brut < 0) or np.any(etat_brut > 1):
                self.clip_count += np.sum((etat_brut < 0) | (etat_brut > 1))
                
            self.etat = np.clip(etat_brut, 0.0, 1.0)
            
        tot_12 = np.sum(flux_2_vers_1)
        tot_21 = np.sum(flux_1_vers_2)
        omega = (tot_21 - tot_12) / (tot_12 + tot_21) if (tot_12 + tot_21) > 1e-8 else 0.0
        return omega

def run_plan(cfg):
    rng_master = np.random.default_rng(cfg.seed)
    seeds = rng_master.integers(0, 2**31 - 1, size=cfg.n_graines)
    
    mu_values = np.arange(cfg.mu_min, cfg.mu_max + cfg.mu_pas/2, cfg.mu_pas)
    n_mu = len(mu_values)
    
    # Résultats : resultats[T][matrice] = {"up": [], "down": [], "clips": []}
    resultats = {T: {nom: {"up": [], "down": [], "clips": []} for nom in cfg.matrices} for T in cfg.T_list}
    
    for i in range(cfg.n_graines):
        rng = np.random.default_rng(int(seeds[i]))
        
        for T in cfg.T_list:
            # 1. Génération de TOUS les bruits et perturbations (Appariement)
            P_master = []
            B_master = []
            for mu in mu_values:
                a = (0.0 - mu) / cfg.sigma_perturbation
                p_vals = truncnorm.rvs(a, np.inf, loc=mu, scale=cfg.sigma_perturbation, size=T, random_state=rng)
                P_master.append(np.column_stack((p_vals, np.zeros(T))))
                B_master.append(rng.normal(0, cfg.bruit_fond, size=(T, 2)))
            
            for nom, W_tuple in cfg.matrices.items():
                W = np.asarray(W_tuple, dtype=float)
                
                # --- MONTÉE ---
                sys_up = Defense(cfg.etat_initial, W, cfg.decay, cfg.seuil, cfg.gain)
                omega_up = []
                for j in range(n_mu):
                    omega_up.append(sys_up.run_step(P_master[j], B_master[j]))
                
                # --- DESCENTE (Utilisation stricte des mêmes tirages) ---
                sys_down = Defense(sys_up.etat, W, cfg.decay, cfg.seuil, cfg.gain)
                omega_down = []
                for j in range(n_mu - 1, -1, -1):
                    omega_down.append(sys_down.run_step(P_master[j], B_master[j]))
                
                # Réalignement de la descente
                omega_down.reverse()
                
                resultats[T][nom]["up"].append(omega_up)
                resultats[T][nom]["down"].append(omega_down)
                resultats[T][nom]["clips"].append(sys_up.clip_count + sys_down.clip_count)
                
    return resultats, mu_values

def analyse(resultats, mu_values, cfg):
    print("\n" + "=" * 95)
    print("V48.24 — HYSTÉRÉSIS QUASI-STATIQUE VS DYNAMIQUE")
    print("=" * 95)
    
    for nom in cfg.matrices.keys():
        print(f"\n>>> MATRICE : {nom}")
        print(f"  {'T (Stab)':>8} | {'Aire Abs':>8} | {'Aire Signée':>11} | {'Écrêtage Moy':>12} | {'Verdict':>25}")
        print("  " + "-" * 75)
        
        for T in cfg.T_list:
            up = np.array(resultats[T][nom]["up"])
            down = np.array(resultats[T][nom]["down"])
            clips = np.mean(resultats[T][nom]["clips"])
            
            up_mean = np.mean(up, axis=0)
            down_mean = np.mean(down, axis=0)
            diff = up_mean - down_mean
            
            # Aire absolue : intégrale de |diff|
            aire_abs = np.sum(np.abs(diff)) * cfg.mu_pas
            
            # Aire signée : intégrale de diff (via la règle des trapèzes)
            aire_sig = np.trapz(diff, mu_values)
            
            if aire_abs < 0.05:
                verdict = "Réversibilité"
            elif T == cfg.T_list[-1] and aire_abs > 0.10:
                verdict = "HYSTÉRÉSIS VRAIE"
            else:
                verdict = "Retard dynamique"
                
            print(f"  {T:>8} | {aire_abs:>8.4f} | {aire_sig:>+11.4f} | {clips:>12.1f} | {verdict:>25}")

    print("\n[Note] : Si l'aire diminue fortement quand T augmente, c'est un retard dynamique.")
    print("Si elle reste stable, c'est une véritable hystérésis structurelle.")

if __name__ == "__main__":
    cfg = Config()
    print("Démarrage V48.24 — Protocole d'hystérésis rigoureux...")
    debut = time.perf_counter()
    res, muv = run_plan(cfg)
    analyse(res, muv, cfg)
    print("\n" + "=" * 95)
    print(f"FIN — Durée : {time.perf_counter() - debut:.2f} s")
    print("=" * 95)
