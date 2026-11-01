#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V49.4 — INSTRUMENTATION FINALE ET INFÉRENCE STATISTIQUE
=======================================================
Corrections d'audit (V49.3 -> V49.4) :
- Initialisation correcte de F_min_r avec F_stress.
- Conservation des états compartimentaux (x1, x2) à la fin du stress.
- Ajout des intervalles de confiance bootstrap (IC 95%).
- Ajout des contrastes appariés (ASYM - SYM) et (Aigu - Chronique).
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
        object.__setattr__(self, 'doses_cibles', np.array([10.0])) 
        object.__setattr__(self, 'alphas', np.array([0.0, 0.10, 0.20]))

def build_W(alpha):
    W = np.array([
        [0.8 - alpha, 0.2 - alpha],
        [0.2 + alpha, 0.8 + alpha]
    ])
    assert np.allclose(W.sum(axis=0), 1.0)
    assert np.allclose(np.sort(np.linalg.eigvals(W)), [0.6, 1.0])
    assert np.all(W >= 0.0)
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
        
        F_min_s = self.etat[0] * self.etat[1]
        F_min_r = None
        F_stress = None
        x_stress = None
        
        D_realisee = 0.0
        
        for t in range(n):
            perte_demandee = np.minimum(P[t] * self.decay, 1.0)
            x_moins = np.clip(self.etat - perte_demandee, 0.0, 1.0)
            D_realisee += np.sum(self.etat - x_moins)
            
            couple = self.W @ x_moins
            besoin = np.maximum(0.0, self.seuil - couple)
            correction = self.gain * besoin
            bruit_eff = bruit[t] * self.etat * (1.0 - self.etat)
            
            self.etat = np.clip(couple + correction + bruit_eff, 0.0, 1.0)
            F = self.etat[0] * self.etat[1]
            
            # Logique temporelle stricte
            if t < self.n_stress:
                F_min_s = min(F_min_s, F)
                if t == self.n_stress - 1:
                    F_stress = F
                    x_stress = self.etat.copy()
            else:
                if t == self.n_stress:
                    F_min_r = min(F_stress, F)
                else:
                    F_min_r = min(F_min_r, F)
                
        F_final = self.etat[0] * self.etat[1]
        
        return {
            "F_min_s": F_min_s, "F_min_r": F_min_r, "F_final": F_final,
            "x1_stress": x_stress[0], "x2_stress": x_stress[1],
            "x1_final": self.etat[0], "x2_final": self.etat[1],
            "D_realisee": D_realisee
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
    
    metrics = ["F_min_s", "F_min_r", "F_final", "x1_stress", "x2_stress", "x1_final", "x2_final", "D_realisee"]
    resultats = {m: {a: {met: np.zeros(cfg.n_graines) for met in metrics} for a in cfg.alphas} for m in modes}

    for i in range(cfg.n_graines):
        rng = np.random.default_rng(int(seeds[i]))
        bruit = rng.normal(0, cfg.bruit_interne, size=(n_total, 2))
        
        for mode in modes:
            P = generer_profil(mode, cfg.n_stress, cfg.n_recup, cfg.doses_cibles[0], cfg)
            for a in cfg.alphas:
                W = build_W(a)
                sys = Defense(etat0, W, cfg.decay, cfg.seuil, cfg.gain, cfg.n_stress)
                res = sys.run(P, bruit)
                for met in metrics:
                    resultats[mode][a][met][i] = res[met]
    return resultats

def ic95_bootstrap(donnees, n_boot=2000):
    """Calcule l'IC à 95% par bootstrap sur les graines."""
    d = np.asarray(donnees)
    if len(d) < 2: return np.nan, np.nan
    rng = np.random.default_rng(42)
    means = [np.mean(rng.choice(d, size=len(d), replace=True)) for _ in range(n_boot)]
    return np.percentile(means, 2.5), np.percentile(means, 97.5)

def afficher_stats(resultats, cfg):
    print("\n" + "=" * 95)
    print("V49.4 — INFÉRENCE STATISTIQUE ET CONTINUITÉ (Dose = 10.0)")
    print("=" * 95)

    for mode in ["chronique", "aigu"]:
        print(f"\n>>> RÉGIME : {mode.upper()}")
        
        print(f"--- 1. ÉTATS COMPARTIMENTAUX (Moyennes) ---")
        print(f"  {'Alpha':>5} | {'x1 (Stress)':>11} | {'x2 (Stress)':>11} | {'x1 (Final)':>10} | {'x2 (Final)':>10}")
        print("  " + "-" * 60)
        for a in cfg.alphas:
            x1_s = np.mean(resultats[mode][a]["x1_stress"])
            x2_s = np.mean(resultats[mode][a]["x2_stress"])
            x1_f = np.mean(resultats[mode][a]["x1_final"])
            x2_f = np.mean(resultats[mode][a]["x2_final"])
            print(f"  {a:>5.2f} | {x1_s:>11.3f} | {x2_s:>11.3f} | {x1_f:>10.3f} | {x2_f:>10.3f}")

        print(f"\n--- 2. INTÉGRITÉ (Moyenne [IC 95%]) ---")
        print(f"  {'Alpha':>5} | {'F_min Stress':>20} | {'F_min Récup':>20} | {'F_final':>20}")
        print("  " + "-" * 75)
        for a in cfg.alphas:
            fmin_s = resultats[mode][a]["F_min_s"]
            fmin_r = resultats[mode][a]["F_min_r"]
            ffinal = resultats[mode][a]["F_final"]
            
            s_m, (s_lo, s_hi) = np.mean(fmin_s), ic95_bootstrap(fmin_s)
            r_m, (r_lo, r_hi) = np.mean(fmin_r), ic95_bootstrap(fmin_r)
            f_m, (f_lo, f_hi) = np.mean(ffinal), ic95_bootstrap(ffinal)
            
            print(f"  {a:>5.2f} | {s_m:.3f} [{s_lo:.2f},{s_hi:.2f}] | {r_m:.3f} [{r_lo:.2f},{r_hi:.2f}] | {f_m:.3f} [{f_lo:.2f},{f_hi:.2f}]")

    print("\n" + "=" * 95)
    print("CONTRASTES APPARIÉS (Différences et IC 95%)")
    print("=" * 95)
    
    # 1. Effet de l'asymétrie (Alpha=0.20 vs Alpha=0.0)
    print("\n--- 3. EFFET DE L'ASYMÉTRIE (ASYM - SYM sur F_final) ---")
    for mode in ["chronique", "aigu"]:
        diff = resultats[mode][0.20]["F_final"] - resultats[mode][0.0]["F_final"]
        m, (lo, hi) = np.mean(diff), ic95_bootstrap(diff)
        sig = "*" if (lo > 0 or hi < 0) else "n.s."
        print(f"  Mode {mode:<9} : Delta = {m:+.3f} [IC: {lo:+.3f}, {hi:+.3f}] {sig}")

    # 2. Effet du calendrier (Aigu vs Chronique)
    print("\n--- 4. EFFET DU CALENDRIER (Aigu - Chronique sur F_final) ---")
    for a in cfg.alphas:
        diff = resultats["aigu"][a]["F_final"] - resultats["chronique"][a]["F_final"]
        m, (lo, hi) = np.mean(diff), ic95_bootstrap(diff)
        sig = "*" if (lo > 0 or hi < 0) else "n.s."
        print(f"  Alpha={a:.2f} | Delta = {m:+.3f} [IC: {lo:+.3f}, {hi:+.3f}] {sig}")

if __name__ == "__main__":
    cfg = Config()
    print("Démarrage V49.4 — Statistiques finales...")
    debut = time.perf_counter()
    res = run_plan(cfg)
    afficher_stats(res, cfg)
    print("\n" + "=" * 95)
    print(f"FIN — Durée : {time.perf_counter() - debut:.2f} s")
    print("=" * 95)
