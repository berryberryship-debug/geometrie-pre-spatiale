#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
V49.6.1-H — VARIANTE HYPERBOLIQUE AVEC CALIBRATION ROBUSTE
==========================================================
Corrections d'audit :
- Renommage en V49.6.1-H (variante hyperbolique).
- Remplacement de la dichotomie naïve par un balayage fin (grille) 
  suivi d'un raffinement local pour gérer la non-monotonie.
- Signalement explicite des échecs de calibration.
- Retour de etat_stress dans les résultats.
"""

from __future__ import annotations
import time
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class Config:
    n_graines: int = 10  # Ajuster pour le test
    n_stress: int = 100
    n_recup: int = 20
    seed: int = 42
    dose_reelle_cible: float = 0.50
    tolerance_dose: float = 1e-6
    alphas: tuple = (0.0, 0.20)
    gains: tuple = (0.0, 0.8)
    seuil: float = 0.5
    decay: float = 0.10
    etat_initial: tuple = (1.0, 1.0)
    bruit_interne: float = 0.01
    tolerance_bilan: float = 1e-10
    
    # Paramètres de la grille de calibration
    calibration_grille_points: int = 100
    calibration_max_amplitude: float = 1000.0

    def __post_init__(self):
        if self.n_graines < 1: raise ValueError("n_graines doit être >= 1.")
        if self.n_stress < 10: raise ValueError("n_stress doit être >= 10.")

def build_W(alpha: float) -> np.ndarray:
    W = np.array([
        [0.8 - alpha, 0.2 - alpha],
        [0.2 + alpha, 0.8 + alpha]
    ], dtype=float)
    if not np.allclose(W.sum(axis=0), 1.0):
        raise AssertionError("W n'est pas colonne-stochastique.")
    return W

def construire_profil(mode: str, n_stress: int, n_recup: int) -> np.ndarray:
    n_total = n_stress + n_recup
    profil = np.zeros(n_total, dtype=float)
    if mode == "chronique":
        profil[:n_stress] = 1.0 / n_stress
    elif mode == "aigu":
        n_impulsions = 10
        indices = np.linspace(0, n_stress - 1, n_impulsions, dtype=int)
        profil[indices] = 1.0 / n_impulsions
    return profil

def simuler(cfg: Config, W: np.ndarray, gain: float, profil: np.ndarray, amplitude: float, bruit: np.ndarray) -> dict:
    etat = np.asarray(cfg.etat_initial, dtype=float).copy()
    reference = etat.copy()
    n_total = len(profil)
    
    phases = {
        "stress": {"dose_demandee": 0.0, "dose_reelle": 0.0, "delta_perte": 0.0, 
                   "delta_couplage": 0.0, "correction_brute": 0.0, "delta_bruit": 0.0, 
                   "delta_ecretage": 0.0, "delta_M": 0.0},
        "recup": {"dose_demandee": 0.0, "dose_reelle": 0.0, "delta_perte": 0.0, 
                  "delta_couplage": 0.0, "correction_brute": 0.0, "delta_bruit": 0.0, 
                  "delta_ecretage": 0.0, "delta_M": 0.0}
    }

    F_min = float(np.prod(etat))
    distance_stress = None
    max_residu = 0.0
    max_erreur_couplage = 0.0
    etat_stress = None

    for t in range(n_total):
        phase = "stress" if t < cfg.n_stress else "recup"
        avant = etat.copy()
        masse_avant = float(np.sum(avant))

        # A. Perturbation demandée (Saturation Hyperbolique)
        demande = np.tanh(profil[t] * amplitude * cfg.decay)
        perte_demandee = np.array([demande, 0.0], dtype=float)
        
        apres_perte = np.clip(avant - perte_demandee, 0.0, 1.0)
        perte_reelle = avant - apres_perte
        dose_demandee = float(np.sum(perte_demandee))
        dose_reelle = float(np.sum(perte_reelle))
        delta_perte = -dose_reelle

        # B. Couplage relationnel
        couple = W @ apres_perte
        delta_couplage = float(np.sum(couple) - np.sum(apres_perte))
        max_erreur_couplage = max(max_erreur_couplage, abs(delta_couplage))

        # C. Correction homéostatique (Saturation Hyperbolique)
        besoin = np.maximum(0.0, cfg.seuil - couple)
        correction = gain * np.tanh(besoin * 2.0)
        correction_brute = float(np.sum(correction))

        # D. Bruit multiplicatif
        bruit_eff = bruit[t] * avant * (1.0 - avant)
        delta_bruit = float(np.sum(bruit_eff))

        # E. Écrêtage global (physique)
        avant_ecretage = couple + correction + bruit_eff
        nouvel_etat = np.clip(avant_ecretage, 0.0, 1.0)
        delta_ecretage = float(np.sum(nouvel_etat) - np.sum(avant_ecretage))
        etat = nouvel_etat

        # F. Bilan de masse
        delta_M = float(np.sum(etat)) - masse_avant
        bilan = (delta_perte + delta_couplage + correction_brute + 
                 delta_bruit + delta_ecretage)
        residu = delta_M - bilan
        max_residu = max(max_residu, abs(residu))
        
        if abs(residu) > cfg.tolerance_bilan:
            raise AssertionError(f"Bilan non fermé au pas {t}: résidu={residu:.3e}")

        # G. Agrégation
        valeurs = {
            "dose_demandee": dose_demandee, "dose_reelle": dose_reelle,
            "delta_perte": delta_perte, "delta_couplage": delta_couplage,
            "correction_brute": correction_brute, "delta_bruit": delta_bruit,
            "delta_ecretage": delta_ecretage, "delta_M": delta_M
        }
        for nom, v in valeurs.items():
            phases[phase][nom] += v

        # H. Distance
        distance = float(np.linalg.norm(etat - reference))
        F = float(etat[0] * etat[1])
        F_min = min(F_min, F)
        
        if t == cfg.n_stress - 1:
            distance_stress = distance
            etat_stress = etat.copy() # Sauvegarde de l'état critique

    distance_finale = float(np.linalg.norm(etat - reference))
    if distance_stress is None: distance_stress = distance_finale

    return {
        "dose_demandee": phases["stress"]["dose_demandee"] + phases["recup"]["dose_demandee"],
        "dose_reelle": phases["stress"]["dose_reelle"] + phases["recup"]["dose_reelle"],
        "F_min": F_min, "F_final": float(etat[0] * etat[1]),
        "x1_final": float(etat[0]), "x2_final": float(etat[1]),
        "distance_stress": distance_stress, "distance_finale": distance_finale,
        "amelioration_recuperation": distance_stress - distance_finale,
        "phases": phases, 
        "max_residu": max_residu, 
        "max_erreur_couplage": max_erreur_couplage,
        "etat_stress": etat_stress # Ajout demandé par l'audit
    }

def calibrer_dose(cfg, W, gain, profil, bruit):
    """
    Calibration robuste : 
    1. Balayage fin (grille) pour repérer les croisements.
    2. Raffinement par dichotomie locale.
    3. Signalement explicite en cas d'échec ou de non-monotonie.
    """
    cible = cfg.dose_reelle_cible
    
    # 1. Évaluation grossière sur la grille
    a_grid = np.linspace(0, cfg.calibration_max_amplitude, cfg.calibration_grille_points)
    doses = []
    for a in a_grid:
        res = simuler(cfg, W, gain, profil, a, bruit)
        doses.append(res["dose_reelle"])
    
    doses = np.array(doses)
    
    # Détection de la non-monotonie
    if np.any(np.diff(doses) < -cfg.tolerance_dose):
        print("Attention : La fonction dose-amplitude n'est pas strictement monotone.")

    # 2. Recherche des croisements
    croisements = []
    for i in range(len(doses) - 1):
        if (doses[i] - cible) * (doses[i+1] - cible) <= 0:
            croisements.append((a_grid[i], a_grid[i+1]))
    
    if not croisements:
        raise RuntimeError(f"Échec de calibration : dose cible {cible} non atteinte pour amplitude max {cfg.calibration_max_amplitude}.")
    
    # On prend le premier croisement (ou on pourrait prendre le croisement montant)
    a_min, a_max = croisements[0]
    
    # 3. Raffinement local par dichotomie
    for _ in range(50):
        a_mid = 0.5 * (a_min + a_max)
        res_mid = simuler(cfg, W, gain, profil, a_mid, bruit)
        dose_mid = res_mid["dose_reelle"]
        
        if abs(dose_mid - cible) <= cfg.tolerance_dose:
            return a_mid, res_mid
            
        if (dose_mid - cible) * (doses[0] - cible) > 0: # Simple heuristique
            a_min = a_mid
        else:
            a_max = a_mid
            
    # Si la boucle échoue, on retourne le meilleur résultat trouvé avec un warning
    print("Avertissement : Calibration terminée sans atteindre la tolérance exacte.")
    return a_mid, res_mid

def run_plan(cfg):
    rng_master = np.random.default_rng(cfg.seed)
    seeds = rng_master.integers(0, 2**31 - 1, size=cfg.n_graines)
    modes = ("chronique", "aigu")
    resultats = {m: {g: {a: {"amplitude": np.zeros(cfg.n_graines), "dose_reelle": np.zeros(cfg.n_graines),
                           "F_min": np.zeros(cfg.n_graines), "F_final": np.zeros(cfg.n_graines),
                           "distance_stress": np.zeros(cfg.n_graines), "distance_finale": np.zeros(cfg.n_graines),
                           "amelioration_recuperation": np.zeros(cfg.n_graines),
                           "max_residu": np.zeros(cfg.n_graines), "max_erreur_couplage": np.zeros(cfg.n_graines)}
                    for a in cfg.alphas} for g in cfg.gains} for m in modes}

    for i, seed in enumerate(seeds):
        rng = np.random.default_rng(int(seed))
        bruit = rng.normal(0.0, cfg.bruit_interne, size=(cfg.n_stress + cfg.n_recup, 2))
        
        for mode in modes:
            profil = construire_profil(mode, cfg.n_stress, cfg.n_recup)
            for alpha in cfg.alphas:
                W = build_W(alpha)
                for gain in cfg.gains:
                    amp, res = calibrer_dose(cfg, W, gain, profil, bruit)
                    cible = resultats[mode][gain][alpha]
                    cible["amplitude"][i] = amp
                    for nom in ("dose_reelle", "F_min", "F_final", "distance_stress", "distance_finale", "amelioration_recuperation", "max_residu", "max_erreur_couplage"):
                        cible[nom][i] = res[nom]
    return resultats

def main():
    cfg = Config()
    print("=" * 100)
    print("DÉMARRAGE V49.6.1-H (CALIBRATION ROBUSTE)")
    print("=" * 100)
    
    debut = time.perf_counter()
    res = run_plan(cfg)
    
    for mode in ("chronique", "aigu"):
        print(f"\nRÉGIME : {mode.upper()}")
        print(f"{'Gain':>8} | {'Alpha':>5} | {'Dose':>9} | {'Ampl.':>8} | {'F_min':>7} | {'F_fin':>7} | {'Gain récup.':>11}")
        print("-" * 75)
        for gain in cfg.gains:
            for alpha in cfg.alphas:
                r = res[mode][gain][alpha]
                label = "Témoin" if gain == 0.0 else f"Actif {gain:.2f}"
                print(f"{label:>8} | {alpha:>5.2f} | {np.mean(r['dose_reelle']):>9.6f} | "
                      f"{np.mean(r['amplitude']):>8.4f} | {np.mean(r['F_min']):>7.4f} | "
                      f"{np.mean(r['F_final']):>7.4f} | {np.mean(r['amelioration_recuperation']):>+11.5f}")

    print(f"\nDurée : {time.perf_counter() - debut:.2f} s")

if __name__ == "__main__":
    main()
