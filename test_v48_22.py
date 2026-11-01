#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V48.22 — MOTEUR DE MESURE DE LA CONTINUITÉ RELATIONNELLE
========================================================
Corrections d'audit :
- Préconditionnement pour trouver l'équilibre propre à chaque matrice.
- Bruit multiplicatif (proportionnel à la marge) pour éviter le biais d'écrêtage.
- Bruit apparié pour comparer SYM et ASYM_CONS sur les mêmes réalisations.
- Mesures de dérive : D_moy (amplitude) et D_signe (orientation) avec Wilcoxon.
- Conservation des séries temporelles de Omega.
"""
from __future__ import annotations
import time
from dataclasses import dataclass
import numpy as np
from scipy.stats import truncnorm, wilcoxon
import warnings
warnings.filterwarnings("ignore")

@dataclass(frozen=True)
class Config:
    n_graines: int = 100
    # Phases temporelles
    n_prechauffage: int = 50
    n_pre_choc: int = 30
    n_choc: int = 40
    n_post_choc: int = 50
    
    seed: int = 42
    mu_perturbation: float = 6.0
    sigma_perturbation: float = 2.0
    seuil: float = 0.5
    decay: float = 0.10
    
    matrices: dict = None
    etat_initial: tuple = (1.0, 1.0)
    gain: float = 0.8
    bruit_fond: float = 0.05

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

    def run_phase(self, P, bruit, record_omega=False):
        n = P.shape[0]
        flux_1_vers_2 = np.zeros(n) # C1 vers C2 (W[1,0])
        flux_2_vers_1 = np.zeros(n) # C2 vers C1 (W[0,1])
        
        for t in range(n):
            perte = np.minimum(P[t] * self.decay, 1.0)
            x_moins = np.clip(self.etat - perte, 0.0, 1.0)
            
            # Calcul des flux
            f12 = self.W[0, 1] * x_moins[1]
            f21 = self.W[1, 0] * x_moins[0]
            flux_1_vers_2[t] = f21
            flux_2_vers_1[t] = f12
            
            couple = self.W @ x_moins
            besoin = np.maximum(0.0, self.seuil - couple)
            correction = self.gain * besoin
            
            # Bruit multiplicatif (s'annule aux bornes 0 et 1)
            bruit_effectif = bruit[t] * self.etat * (1.0 - self.etat)
            self.etat = np.clip(couple + correction + bruit_effectif, 0.0, 1.0)
            
        # Calcul des Omegas temporels pour cette phase
        omega_t = np.zeros(n)
        tot = flux_1_vers_2 + flux_2_vers_1
        mask = tot > 1e-8
        omega_t[mask] = (flux_1_vers_2[mask] - flux_2_vers_1[mask]) / tot[mask]
        
        # Omega global de la phase
        tot_12 = np.sum(flux_2_vers_1)
        tot_21 = np.sum(flux_1_vers_2)
        omega_phase = (tot_21 - tot_12) / (tot_12 + tot_21) if (tot_12 + tot_21) > 1e-8 else 0.0
        
        return omega_phase, omega_t

def run_plan(cfg):
    rng_master = np.random.default_rng(cfg.seed)
    seeds = rng_master.integers(0, 2**31 - 1, size=cfg.n_graines)
    etat0 = np.asarray(cfg.etat_initial, dtype=float)
    
    resultats = {k: {
        "omega_pre": [], "omega_stress": [], "omega_post": [],
        "omega_t_post": [] # Pour voir la trajectoire de récupération
    } for k in cfg.matrices.keys()}

    for i in range(cfg.n_graines):
        rng = np.random.default_rng(int(seeds[i]))
        a = (0.0 - cfg.mu_perturbation) / cfg.sigma_perturbation
        
        # 1. Génération des bruits (Appariés)
        # On génère les bruits pour toutes les phases, on les réutilisera
        n_total = cfg.n_prechauffage + cfg.n_pre_choc + cfg.n_choc + cfg.n_post_choc
        bruit_global = rng.normal(0, cfg.bruit_fond, size=(n_total, 2))
        
        # 2. Génération des perturbations (uniquement sur C1)
        p_choc_vals = truncnorm.rvs(a, np.inf, loc=cfg.mu_perturbation, scale=cfg.sigma_perturbation, size=cfg.n_choc, random_state=rng)
        P_choc = np.column_stack((p_choc_vals, np.zeros(cfg.n_choc)))
        
        # Découpage des tableaux
        P_vide = np.zeros((cfg.n_pre_choc, 2))
        P_post = np.zeros((cfg.n_post_choc, 2))
        
        idx_prechauf = slice(0, cfg.n_prechauffage)
        idx_pre = slice(cfg.n_prechauffage, cfg.n_prechauffage + cfg.n_pre_choc)
        idx_choc = slice(cfg.n_prechauffage + cfg.n_pre_choc, cfg.n_prechauffage + cfg.n_pre_choc + cfg.n_choc)
        idx_post = slice(cfg.n_prechauffage + cfg.n_pre_choc + cfg.n_choc, n_total)

        for nom, W_tuple in cfg.matrices.items():
            W = np.asarray(W_tuple, dtype=float)
            sys = Defense(etat0, W, cfg.decay, cfg.seuil, cfg.gain)
            
            # Phase 0 : PRÉCHAUFFAGE (Équilibre de la matrice)
            sys.run_phase(np.zeros((cfg.n_prechauffage, 2)), bruit_global[idx_prechauf])
            
            # Phase 1 : PRÉ-CHOC
            omega_pre, _ = sys.run_phase(P_vide, bruit_global[idx_pre])
            
            # Phase 2 : CHOC
            omega_stress, _ = sys.run_phase(P_choc, bruit_global[idx_choc])
            
            # Phase 3 : POST-CHOC (avec enregistrement temporel)
            omega_post, omega_t_post = sys.run_phase(P_post, bruit_global[idx_post])
            
            resultats[nom]["omega_pre"].append(omega_pre)
            resultats[nom]["omega_stress"].append(omega_stress)
            resultats[nom]["omega_post"].append(omega_post)
            resultats[nom]["omega_t_post"].append(omega_t_post)
                    
    return resultats

def analyse(resultats, cfg):
    print("\n" + "=" * 95)
    print("V48.22 — MOTEUR DE MESURE DE LA CONTINUITÉ RELATIONNELLE")
    print("=" * 95)
    
    for nom in cfg.matrices.keys():
        print(f"\n>>> MATRICE : {nom}")
        
        pre = np.array(resultats[nom]["omega_pre"])
        stress = np.array(resultats[nom]["omega_stress"])
        post = np.array(resultats[nom]["omega_post"])
        
        # Dérives
        derive_signee = post - pre
        derive_absolue = np.abs(derive_signee)
        
        mean_derive_sig = np.mean(derive_signee)
        mean_derive_abs = np.mean(derive_absolue)
        
        print(f"  Omega Initial (Pré-choc)  : {np.mean(pre):+.4f} (±{np.std(pre):.4f})")
        print(f"  Omega sous Choc (Stress)  : {np.mean(stress):+.4f} (±{np.std(stress):.4f})")
        print(f"  Omega Final (Post-choc)   : {np.mean(post):+.4f} (±{np.std(post):.4f})")
        print(f"  -----------------------------------------")
        print(f"  Dérive signée moyenne (D_signe) : {mean_derive_sig:+.4f}")
        print(f"  Dérive absolue moyenne (D_moy)  : {mean_derive_abs:.4f}")
        
        # Test statistique (H0: pas de dérive)
        try:
            stat, p = wilcoxon(derive_signee)
            sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s."
            print(f"  Test Wilcoxon sur la dérive     : p = {p:.2e} {sig}")
        except ValueError:
            print("  Test Wilcoxon non applicable (toutes les dérives sont identiques).")
            
        if mean_derive_abs < 0.05:
            print("  Verdict : RÉSILIENCE STRUCTURELLE (Le système a retrouvé sa signature).")
        elif mean_derive_abs < 0.20:
            print("  Verdict : DÉFORMATION PARTIELLE (Hystérésis faible).")
        else:
            print("  Verdict : RECONFIGURATION MAJEURE (Le couplage a muté).")

    # Comparaison inter-matrices (SYM vs ASYM)
    if "SYM" in cfg.matrices and "ASYM_CONS" in cfg.matrices:
        print("\n" + "=" * 95)
        print("COMPARAISON INTER-MATRICES (Appariée par graine)")
        print("=" * 95)
        pre_sym = np.array(resultats["SYM"]["omega_pre"])
        pre_asym = np.array(resultats["ASYM_CONS"]["omega_pre"])
        post_sym = np.array(resultats["SYM"]["omega_post"])
        post_asym = np.array(resultats["ASYM_CONS"]["omega_post"])
        
        diff_post = post_asym - post_sym
        stat, p = wilcoxon(diff_post) if not np.allclose(diff_post, 0) else (0, 1.0)
        print(f"Différence de signature finale (ASYM - SYM) : {np.mean(diff_post):+.4f}")
        print(f"Test de Wilcoxon                            : p = {p:.2e}")

if __name__ == "__main__":
    cfg = Config()
    print("Démarrage V48.22 — Protocole de continuité...")
    debut = time.perf_counter()
    res = run_plan(cfg)
    analyse(res, cfg)
    print("\n" + "=" * 95)
    print(f"FIN — Durée : {time.perf_counter() - debut:.2f} s")
    print("=" * 95)
