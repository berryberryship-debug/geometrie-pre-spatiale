#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V48.26 — PLASTICITÉ : RENFORCEMENT VS FATIGUE & DISTANCES STRUCTURELLES
======================================================================
Corrections d'audit :
- Séparation des phases dans les paramètres de Config.
- Deux modes explicites : "renforcement" (les liens forts grossissent) 
  et "fatigue" (les liens forts s'usent).
- Mesure des 4 distances : D_pré, D_choc, D_post, D_résiduel.
- IC Bootstrap à 95% sur les graines pour les distances.
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
    n_pre: int = 20
    n_choc: int = 40
    n_post: int = 40
    
    seed: int = 42
    mu_perturbation: float = 6.0
    sigma_perturbation: float = 2.0
    seuil: float = 0.5
    decay: float = 0.10
    
    W_init: tuple = ((0.8, 0.2), (0.2, 0.8))
    etat_initial: tuple = (1.0, 1.0)
    gain: float = 0.8
    bruit_fond: float = 0.02
    
    # Mode de plasticité : "renforcement" ou "fatigue"
    mode_plasticite: str = "renforcement"
    
    eta_adaptation: float = 0.005
    relaxation_lien: float = 0.001

class DefensePlastiqueV2:
    def __init__(self, etat0, W_init, decay, seuil, gain, cfg):
        self.etat = np.asarray(etat0, dtype=float).copy()
        self.W = np.asarray(W_init, dtype=float).copy()
        self.W_initial = self.W.copy()
        self.decay = decay
        self.seuil = seuil
        self.gain = gain
        self.cfg = cfg

    def update_W(self, f12, f21):
        # Matrice des flux (0->1 et 1->0)
        F = np.array([[0.0, f12], [f21, 0.0]])
        
        # Définition du signe selon l'hypothèse
        if self.cfg.mode_plasticite == "renforcement":
            delta_W = self.cfg.eta_adaptation * F
        elif self.cfg.mode_plasticite == "fatigue":
            delta_W = -self.cfg.eta_adaptation * F
        else:
            raise ValueError("Mode de plasticité inconnu.")
            
        # Relaxation vers l'état initial
        delta_W -= self.cfg.relaxation_lien * (self.W - self.W_initial)
        
        # Mise à jour et contraintes
        self.W += delta_W
        self.W = np.clip(self.W, 0.01, 0.99)
        self.W /= self.W.sum(axis=0, keepdims=True) # Normalisation stricte

    def _step(self, P_t, bruit_t):
        perte = np.minimum(P_t * self.decay, 1.0)
        x_moins = np.clip(self.etat - perte, 0.0, 1.0)
        
        f12 = self.W[0, 1] * x_moins[1]
        f21 = self.W[1, 0] * x_moins[0]
        
        # Mise à jour de W
        self.update_W(f12, f21)
        
        # Dynamique des états
        couple = self.W @ x_moins
        besoin = np.maximum(0.0, self.seuil - couple)
        correction = self.gain * besoin
        bruit_effectif = bruit_t * self.etat * (1.0 - self.etat)
        self.etat = np.clip(couple + correction + bruit_effectif, 0.0, 1.0)

    def run(self, P_pre, P_choc, P_post, bruit):
        # Phase 1 : Pré-choc
        for t in range(len(P_pre)):
            self._step(P_pre[t], bruit[t])
        W_avant = self.W.copy()
        
        # Phase 2 : Choc
        for t in range(len(P_choc)):
            self._step(P_choc[t], bruit[len(P_pre) + t])
        W_fin_choc = self.W.copy()
        
        # Phase 3 : Post-choc
        for t in range(len(P_post)):
            self._step(P_post[t], bruit[len(P_pre) + len(P_choc) + t])
        W_final = self.W.copy()
        
        # Calcul des 4 distances structurelles
        D_pre = np.linalg.norm(W_avant - self.W_initial)
        D_choc = np.linalg.norm(W_fin_choc - W_avant)
        D_post = np.linalg.norm(W_final - W_fin_choc)
        D_residuel = np.linalg.norm(W_final - self.W_initial)
        
        return {
            "D_pre": D_pre,
            "D_choc": D_choc,
            "D_post": D_post,
            "D_residuel": D_residuel,
            "W_final": W_final
        }

def ic95_bootstrap(donnees, n_boot=1000, alpha=0.05):
    donnees = np.asarray(donnees)
    if len(donnees) < 2: return (np.nan, np.nan)
    rng = np.random.default_rng(42)
    moyennes = [np.mean(rng.choice(donnees, size=len(donnees), replace=True)) for _ in range(n_boot)]
    return np.percentile(moyennes, 100*alpha/2), np.percentile(moyennes, 100*(1-alpha/2))

def run_plan(cfg):
    rng_master = np.random.default_rng(cfg.seed)
    seeds = rng_master.integers(0, 2**31 - 1, size=cfg.n_graines)
    etat0 = np.asarray(cfg.etat_initial, dtype=float)
    
    resultats = []

    for i in range(cfg.n_graines):
        rng = np.random.default_rng(int(seeds[i]))
        a = (0.0 - cfg.mu_perturbation) / cfg.sigma_perturbation
        
        P_vide = np.zeros((cfg.n_pre, 2))
        P_choc_vals = truncnorm.rvs(a, np.inf, loc=cfg.mu_perturbation, scale=cfg.sigma_perturbation, size=cfg.n_choc, random_state=rng)
        P_choc = np.column_stack((P_choc_vals, np.zeros(cfg.n_choc)))
        P_post = np.zeros((cfg.n_post, 2))
        
        bruit = rng.normal(0, cfg.bruit_fond, size=(cfg.n_pre + cfg.n_choc + cfg.n_post, 2))
        
        sys = DefensePlastiqueV2(etat0, cfg.W_init, cfg.decay, cfg.seuil, cfg.gain, cfg)
        res = sys.run(P_vide, P_choc, P_post, bruit)
        resultats.append(res)
        
    return resultats

def analyse(resultats, cfg):
    print("\n" + "=" * 95)
    print(f"V48.26 — PLASTICITÉ : MODE '{cfg.mode_plasticite.upper()}'")
    print("=" * 95)
    
    d_pre = [r["D_pre"] for r in resultats]
    d_choc = [r["D_choc"] for r in resultats]
    d_post = [r["D_post"] for r in resultats]
    d_res = [r["D_residuel"] for r in resultats]
    
    metriques = [
        ("D_pré (Adaptation spontanée)", d_pre),
        ("D_choc (Déformation sous stress)", d_choc),
        ("D_post (Relaxation)", d_post),
        ("D_résiduel (Mémoire structurelle)", d_res)
    ]
    
    for nom, data in metriques:
        mean = np.mean(data)
        lo, hi = ic95_bootstrap(data)
        print(f"  {nom:<35} : {mean:>7.4f}  [IC95: {lo:>7.4f}, {hi:>7.4f}]")
        
    print("\nMatrice de couplage W finale (moyenne sur les graines) :")
    W_moy = np.mean([r["W_final"] for r in resultats], axis=0)
    print(f"  [[{W_moy[0,0]:.3f}, {W_moy[0,1]:.3f}],")
    print(f"   [{W_moy[1,0]:.3f}, {W_moy[1,1]:.3f}]]")
    print("Rappel : W_init était [[0.800, 0.200], [0.200, 0.800]]")

    if np.mean(d_res) > 0.05:
        print("\nVerdict : MÉMOIRE STRUCTURELLE FORTE. Le système a une plasticité résiduelle.")
    else:
        print("\nVerdict : RÉSILIENCE ÉLASTIQUE. La structure a oublié le choc.")

if __name__ == "__main__":
    # Test 1 : Hypothèse de Renforcement
    print("Démarrage V48.26 — Test de Renforcement...")
    cfg_renf = Config(mode_plasticite="renforcement")
    res_renf = run_plan(cfg_renf)
    analyse(res_renf, cfg_renf)
    
    # Test 2 : Hypothèse de Fatigue
    print("\n\nDémarrage V48.26 — Test de Fatigue...")
    cfg_fatigue = Config(mode_plasticite="fatigue")
    res_fatigue = run_plan(cfg_fatigue)
    analyse(res_fatigue, cfg_fatigue)
