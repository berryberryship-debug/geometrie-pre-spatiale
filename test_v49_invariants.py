#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V49.2 — CIRCULATION RELATIONNELLE ET DÉCOMPOSITION DES FLUX
===========================================================
Corrections d'audit :
- Séparation des flux (stress vs récupération).
- Conservation des états x1 et x2 (stress et finaux).
- Décomposition du transfert net : T_net, T_positif, T_négatif (détection d'inversions).
- Vérification explicite du spectre (np.linalg.eigvals).
- Comparaison rétablie : Chronique vs Aigu.
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
    decay: float = 0.10
    
    etat_initial: tuple = (1.0, 1.0)
    gain: float = 0.8
    bruit_interne: float = 0.01

    def __post_init__(self):
        object.__setattr__(self, 'doses_cibles', np.array([1.0, 10.0])) 
        object.__setattr__(self, 'alphas', np.array([0.0, 0.10, 0.20]))

def build_W(alpha):
    W = np.array([
        [0.8 - alpha, 0.2 - alpha],
        [0.2 + alpha, 0.8 + alpha]
    ])
    assert np.allclose(W.sum(axis=0), 1.0), "Somme des colonnes != 1"
    assert np.allclose(np.sort(np.linalg.eigvals(W)), [0.6, 1.0]), "Spectre != {0.6, 1.0}"
    return W

class Defense:
    def __init__(self, etat0, W, decay, seuil, gain, n_stress):
        self.etat = np.asarray(etat0, dtype=float).copy()
        self.W = np.asarray(W, dtype=float)
        self.decay = decay
        self.seuil = seuil
        self.gain = gain
        self.n_stress = n_stress

    def run(self, P, bruit):
        n = P.shape[0]
        F_min = self.etat[0] * self.etat[1]
        
        # Séparation des flux
        J_12_stress = 0.0; J_21_stress = 0.0
        J_12_rec = 0.0; J_21_rec = 0.0
        
        # Décomposition du transfert (T_positif et T_négatif)
        T_pos = 0.0; T_neg = 0.0
        
        x_stress = None; F_stress = None
        
        for t in range(n):
            perte_demandee = np.minimum(P[t] * self.decay, 1.0)
            x_moins = np.clip(self.etat - perte_demandee, 0.0, 1.0)
            
            j12 = self.W[1, 0] * x_moins[0]
            j21 = self.W[0, 1] * x_moins[1]
            t_net = j12 - j21
            
            if t < self.n_stress:
                J_12_stress += j12
                J_21_stress += j21
            else:
                J_12_rec += j12
                J_21_rec += j21
                
            T_pos += max(0.0, t_net)
            T_neg += max(0.0, -t_net)
            
            couple = self.W @ x_moins
            besoin = np.maximum(0.0, self.seuil - couple)
            correction = self.gain * besoin
            bruit_eff = bruit[t] * self.etat * (1.0 - self.etat)
            
            self.etat = np.clip(couple + correction + bruit_eff, 0.0, 1.0)
            F = self.etat[0] * self.etat[1]
            F_min = min(F_min, F)
            
            if t == self.n_stress - 1:
                F_stress = F
                x_stress = self.etat.copy()
                
        return {
            "F_min": F_min, "F_stress": F_stress, "F_final": self.etat[0]*self.etat[1],
            "x1_stress": x_stress[0], "x2_stress": x_stress[1],
            "x1_final": self.etat[0], "x2_final": self.etat[1],
            "J_12_s": J_12_stress, "J_21_s": J_21_stress,
            "J_12_r": J_12_rec, "J_21_r": J_21_rec,
            "T_pos": T_pos, "T_neg": T_neg
        }

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

def run_plan(cfg):
    rng_master = np.random.default_rng(cfg.seed)
    seeds = rng_master.integers(0, 2**31 - 1, size=cfg.n_graines)
    etat0 = np.asarray(cfg.etat_initial, dtype=float)
    
    modes = ["chronique", "aigu"]
    n_total = cfg.n_stress + cfg.n_recup
    metrics = ["F_min", "F_stress", "F_final", "x1_stress", "x2_stress", "x1_final", "x2_final", 
               "J_12_s", "J_21_s", "J_12_r", "J_21_r", "T_pos", "T_neg"]
               
    resultats = {m: {a: {met: np.zeros((cfg.n_graines, len(cfg.doses_cibles))) for met in metrics} 
                     for a in cfg.alphas} for m in modes}

    for i in range(cfg.n_graines):
        rng = np.random.default_rng(int(seeds[i]))
        bruit = rng.normal(0, cfg.bruit_interne, size=(n_total, 2))
        
        for j, dose in enumerate(cfg.doses_cibles):
            for mode in modes:
                P = generer_profil(mode, cfg.n_stress, cfg.n_recup, dose, cfg)
                for a in cfg.alphas:
                    W = build_W(a)
                    sys = Defense(etat0, W, cfg.decay, cfg.seuil, cfg.gain, cfg.n_stress)
                    res = sys.run(P, bruit)
                    for k, met in enumerate(metrics):
                        resultats[mode][a][met][i, j] = res[met]
    return resultats

def afficher_audit(resultats, cfg):
    print("\n" + "=" * 95)
    print("V49.2 — CIRCULATION RELATIONNELLE ET DÉCOMPOSITION DES FLUX")
    print("=" * 95)

    for mode in ["chronique", "aigu"]:
        print(f"\n>>> RÉGIME : {mode.upper()} | DOSE MAX (10.0)")
        print(f"  {'Alpha':>5} | {'J_12 (Stress)':>13} | {'J_21 (Stress)':>13} | {'T_net (Stress)':>14} | {'T_pos / T_neg':>15}")
        print("  " + "-" * 70)
        
        for a in cfg.alphas:
            j12_s = np.mean(resultats[mode][a]["J_12_s"][:, -1])
            j21_s = np.mean(resultats[mode][a]["J_21_s"][:, -1])
            t_net = j12_s - j21_s
            
            t_pos = np.mean(resultats[mode][a]["T_pos"][:, -1])
            t_neg = np.mean(resultats[mode][a]["T_neg"][:, -1])
            
            print(f"  {a:>5.2f} | {j12_s:>13.2f} | {j21_s:>13.2f} | {t_net:>+14.2f} | {t_pos:.0f} / {t_neg:.0f}")

        print(f"\n  --- ÉTATS COMPARTIMENTAUX (Stress vs Final) ---")
        print(f"  {'Alpha':>5} | {'x1_stress':>9} | {'x2_stress':>9} | {'x1_final':>9} | {'x2_final':>9}")
        print("  " + "-" * 55)
        for a in cfg.alphas:
            x1_s = np.mean(resultats[mode][a]["x1_stress"][:, -1])
            x2_s = np.mean(resultats[mode][a]["x2_stress"][:, -1])
            x1_f = np.mean(resultats[mode][a]["x1_final"][:, -1])
            x2_f = np.mean(resultats[mode][a]["x2_final"][:, -1])
            print(f"  {a:>5.2f} | {x1_s:>9.3f} | {x2_s:>9.3f} | {x1_f:>9.3f} | {x2_f:>9.3f}")

if __name__ == "__main__":
    cfg = Config()
    print("Démarrage V49.2 — Audit de circulation...")
    debut = time.perf_counter()
    res = run_plan(cfg)
    afficher_audit(res, cfg)
    print("\n" + "=" * 95)
    print(f"FIN — Durée : {time.perf_counter() - debut:.2f} s")
    print("=" * 95)
