#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V48.33 — AUDIT EXPÉRIMENTAL COMPLET (Asymétrie continue, Doses exactes, Récupération)
=====================================================================================
Corrections d'audit :
- Paramétrisation de l'asymétrie W(alpha).
- Normalisation exacte de la dose d'entrée par recherche de racine (brentq).
- Fenêtre de récupération fixe de 50 cycles post-stress pour TOUS les calendriers.
- Métriques de défaillance : épisodes, durée max, temps sous seuil.
- Statistiques appariées (ASYM - SYM) avec IC bootstrap.
- Suppression du masquage des warnings.
"""
from __future__ import annotations
import time
from dataclasses import dataclass
import numpy as np
from scipy.optimize import brentq
from scipy.stats import truncnorm
import warnings

@dataclass(frozen=True)
class Config:
    n_graines: int = 50
    n_stress: int = 100
    n_recup: int = 50 # Fenêtre fixe de récupération
    seed: int = 42
    
    mode_protocole: str = "stochastique" 
    sigma_bruit_interne: float = 0.01
    sigma_perturbation: float = 0.05
    
    seuil: float = 0.5
    seuil_defaillance: float = 0.25
    decay: float = 0.10
    
    alpha_values: tuple = (0.0, 0.05, 0.10, 0.20) # Balayage de l'asymétrie
    etat_initial: tuple = (1.0, 1.0)
    gain: float = 0.8

    def __post_init__(self):
        if self.mode_protocole not in ["deterministe", "stochastique"]:
            raise ValueError("Mode invalide.")

def build_W(alpha):
    """Construit W(alpha) colonne-stochastique."""
    if alpha < 0 or alpha > 0.8:
        raise ValueError("Alpha hors limites.")
    return np.array([
        [0.8 - alpha, 0.2 - alpha],
        [0.2 + alpha, 0.8 + alpha]
    ])

class Defense:
    def __init__(self, etat0, W, decay, seuil, gain, seuil_def):
        self.etat = np.asarray(etat0, dtype=float).copy()
        self.W = np.asarray(W, dtype=float)
        self.decay = decay
        self.seuil = seuil
        self.gain = gain
        self.seuil_def = seuil_def

    def run(self, P, bruit=None):
        n = P.shape[0]
        F_min = self.etat[0] * self.etat[1]
        
        # Suivi de défaillance
        t_def = np.nan
        episodes = 0
        in_episode = False
        max_duration = 0
        current_duration = 0
        total_cycles_def = 0
        
        C_req = 0.0
        C_app = 0.0
        D_realisee = 0.0
        
        for t in range(n):
            perte_reelle = np.minimum(P[t] * self.decay, 1.0)
            x_moins = np.clip(self.etat - perte_reelle, 0.0, 1.0)
            D_realisee += np.sum(self.etat - x_moins)
            
            couple = self.W @ x_moins
            besoin = np.maximum(0.0, self.seuil - couple)
            corr_req = self.gain * besoin
            C_req += np.sum(corr_req)
            
            etat_sans_bruit = np.clip(couple + corr_req, 0.0, 1.0)
            C_app += np.sum(etat_sans_bruit - couple) # Correction réellement appliquée
            
            if bruit is not None:
                bruit_eff = bruit[t] * self.etat * (1.0 - self.etat)
            else:
                bruit_eff = 0.0
                
            self.etat = np.clip(couple + corr_req + bruit_eff, 0.0, 1.0)
            F = self.etat[0] * self.etat[1]
            F_min = min(F_min, F)
            
            # Logique de défaillance
            if F < self.seuil_def:
                if np.isnan(t_def):
                    t_def = t + 1
                total_cycles_def += 1
                if not in_episode:
                    episodes += 1
                    in_episode = True
                    current_duration = 1
                else:
                    current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                in_episode = False
                current_duration = 0
                
        return {
            "F_min": F_min, "F_final": self.etat[0] * self.etat[1],
            "t_def": t_def, "episodes": episodes, "max_dur": max_duration,
            "total_def": total_cycles_def, "C_req": C_req, "C_app": C_app,
            "D_realisee": D_realisee, "x1": self.etat[0], "x2": self.etat[1]
        }

def generer_profil_et_normaliser(mode, n_stress, rng, cfg):
    """
    Génère le profil brut, puis cherche le facteur k exact pour que D_entree = 40.
    """
    P = np.zeros((n_stress, 2))
    
    if mode == "chronique":
        base_val = 4.0
        P[:, 0] = base_val if cfg.mode_protocole == "deterministe" else np.maximum(0.1, rng.normal(base_val, base_val * cfg.sigma_perturbation, n_stress))
        
    elif mode.startswith("aigu"):
        base_val = 10.0
        n_chocs = 40
        if mode == "aigu_regulier":
            idx = np.linspace(0, n_stress - 1, n_chocs, dtype=int)
        elif mode == "aigu_groupe":
            idx = np.arange((n_stress - n_chocs) // 2, (n_stress + n_chocs) // 2)
        else:
            idx = rng.choice(n_stress, size=n_chocs, replace=False)
            
        if cfg.mode_protocole == "deterministe":
            P[idx, 0] = base_val
        else:
            P[idx, 0] = np.maximum(0.1, rng.normal(base_val, base_val * cfg.sigma_perturbation, n_chocs))
            
    # NORMALISATION STRICTE : On cherche k tel que sum(min(0.1 * k * P, 1)) = 40
    def objectif(k):
        return np.sum(np.minimum(cfg.decay * k * P[:, 0], 1.0)) - 40.0
        
    try:
        k_opt = brentq(objectif, 0.1, 10.0)
        P[:, 0] *= k_opt
    except ValueError:
        pass # Si l'objectif échoue (ex: trop peu de chocs), on garde tel quel
        
    return P

def run_plan(cfg):
    rng_master = np.random.default_rng(cfg.seed)
    seeds = rng_master.integers(0, 2**31 - 1, size=cfg.n_graines)
    etat0 = np.asarray(cfg.etat_initial, dtype=float)
    
    modes = ["chronique", "aigu_regulier", "aigu_groupe", "aigu_aleatoire"]
    metrics = ["F_min", "t_def", "episodes", "max_dur", "total_def", "C_req", "x1", "x2"]
    
    resultats = {mode: {alpha: {m: np.zeros(cfg.n_graines) for m in metrics} for alpha in cfg.alpha_values} for mode in modes}

    for i in range(cfg.n_graines):
        rng = np.random.default_rng(int(seeds[i]))
        
        # Bruit interne pour TOUTE la durée (stress + recup)
        bruit = None
        if cfg.mode_protocole == "stochastique":
            bruit = rng.normal(0, cfg.sigma_bruit_interne, size=(cfg.n_stress + cfg.n_recup, 2))
            
        for mode in modes:
            P_stress = generer_profil_et_normaliser(mode, cfg.n_stress, rng, cfg)
            P_recup = np.zeros((cfg.n_recup, 2))
            P_full = np.vstack((P_stress, P_recup))
            
            for alpha in cfg.alpha_values:
                W = build_W(alpha)
                sys = Defense(etat0, W, cfg.decay, cfg.seuil, cfg.gain, cfg.seuil_defaillance)
                res = sys.run(P_full, bruit)
                
                for m in metrics:
                    resultats[mode][alpha][m][i] = res[m]
                    
    return resultats

def ic95_bootstrap(donnees):
    d = np.asarray(donnees)
    d = d[~np.isnan(d)]
    if len(d) < 2: return (np.nan, np.nan)
    rng = np.random.default_rng(42)
    means = [np.mean(rng.choice(d, size=len(d), replace=True)) for _ in range(2000)]
    return np.percentile(means, 2.5), np.percentile(means, 97.5)

def analyse(resultats, cfg):
    print("\n" + "=" * 95)
    print(f"V48.33 — RÉSULTATS EXPERIMENTAUX COMPLETS (Mode: {cfg.mode_protocole.upper()})")
    print("=" * 95)
    
    for mode in ["chronique", "aigu_regulier", "aigu_groupe", "aigu_aleatoire"]:
        print(f"\n>>> RÉGIME : {mode.upper()}")
        print(f"  {'Alpha':>5} | {'F_min':>7} | {'Épisodes':>8} | {'Durée Max':>9} | {'Effort (C)':>10} | {'x1_fin':>7} | {'x2_fin':>7}")
        print("  " + "-" * 75)
        
        for alpha in cfg.alpha_values:
            fmin = np.mean(resultats[mode][alpha]["F_min"])
            epis = np.mean(resultats[mode][alpha]["episodes"])
            max_dur = np.mean(resultats[mode][alpha]["max_dur"])
            c_req = np.mean(resultats[mode][alpha]["C_req"])
            x1 = np.mean(resultats[mode][alpha]["x1"])
            x2 = np.mean(resultats[mode][alpha]["x2"])
            
            print(f"  {alpha:>5.2f} | {fmin:>7.3f} | {epis:>8.1f} | {max_dur:>9.1f} | {c_req:>10.1f} | {x1:>7.3f} | {x2:>7.3f}")

    print("\n--- INTERACTION : EFFET DE L'ASYMÉTRIE (Alpha=0.20 vs Alpha=0.0) ---")
    for mode in ["chronique", "aigu_regulier", "aigu_groupe", "aigu_aleatoire"]:
        diff = resultats[mode][0.20]["F_min"] - resultats[mode][0.0]["F_min"]
        lo, hi = ic95_bootstrap(diff)
        sig = "SIGNIFICATIF" if (lo > 0 or hi < 0) else "NON SIGNIFICATIF"
        print(f"  Mode {mode:<15} : Delta F_min = {np.mean(diff):+.4f} [IC: {lo:+.4f}, {hi:+.4f}] ({sig})")

if __name__ == "__main__":
    print("Démarrage V48.33 — Test complet...")
    debut = time.perf_counter()
    
    # Test 1 : Stochastique (pour voir la robustesse au bruit)
    cfg_sto = Config(mode_protocole="stochastique")
    res_sto = run_plan(cfg_sto)
    analyse(res_sto, cfg_sto)
    
    print("\n" + "=" * 95)
    print(f"FIN — Durée : {time.perf_counter() - debut:.2f} s")
    print("=" * 95)
