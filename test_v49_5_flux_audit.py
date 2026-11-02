
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V49.5.1 — AUDIT CONJOINT DES FLUX ET DU BILAN DE MASSE
======================================================

Corrections et extensions :
1. Séparation stricte stress / récupération.
2. Mesure des flux bruts J12 et J21.
3. Mesure des transferts nets positifs et négatifs.
4. Mesure des doses demandées et effectivement appliquées.
5. Bilan de masse par étape et par phase :
       ΔM = - pertes + couplage + correction + bruit + écrêtage
6. Validation des paramètres et de la matrice W.
7. Bruit commun aux conditions comparées (graines appariées).

Convention :
- Une variation positive augmente la masse de l'état.
- Une variation négative la diminue.
- Le couplage doit conserver la masse à la précision numérique.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
import numpy as np


# ============================================================
# 1. CONFIGURATION
# ============================================================

@dataclass(frozen=True)
class Config:
    n_graines: int = 100
    n_stress: int = 100
    n_recup: int = 20
    seed: int = 42

    doses_cibles: np.ndarray | None = None
    alphas: np.ndarray | None = None

    seuil: float = 0.5
    decay: float = 0.10

    etat_initial: tuple = (1.0, 1.0)
    gain: float = 0.8
    bruit_interne: float = 0.01

    tolerance: float = 1e-10

    def __post_init__(self):

        if self.n_graines < 1:
            raise ValueError("n_graines doit être >= 1.")

        if self.n_stress < 10:
            raise ValueError(
                "n_stress doit être >= 10 pour le profil aigu."
            )

        if self.n_recup < 0:
            raise ValueError("n_recup doit être >= 0.")

        if self.decay <= 0:
            raise ValueError("decay doit être strictement positif.")

        if not 0.0 <= self.seuil <= 1.0:
            raise ValueError("seuil doit appartenir à [0, 1].")

        if self.gain < 0:
            raise ValueError("gain doit être positif ou nul.")

        if self.bruit_interne < 0:
            raise ValueError(
                "bruit_interne doit être positif ou nul."
            )

        if len(self.etat_initial) != 2:
            raise ValueError(
                "etat_initial doit contenir deux composantes."
            )

        etat0 = np.asarray(self.etat_initial, dtype=float)

        if not np.all(np.isfinite(etat0)):
            raise ValueError("etat_initial contient une valeur non finie.")

        if np.any(etat0 < 0.0) or np.any(etat0 > 1.0):
            raise ValueError("etat_initial doit appartenir à [0, 1].")

        if self.doses_cibles is None:
            doses = np.array([10.0], dtype=float)
        else:
            doses = np.asarray(self.doses_cibles, dtype=float).copy()

        if self.alphas is None:
            alphas = np.array([0.0, 0.10, 0.20], dtype=float)
        else:
            alphas = np.asarray(self.alphas, dtype=float).copy()

        if doses.ndim != 1 or len(doses) == 0:
            raise ValueError("doses_cibles doit être un tableau 1D non vide.")

        if alphas.ndim != 1 or len(alphas) == 0:
            raise ValueError("alphas doit être un tableau 1D non vide.")

        if not np.all(np.isfinite(doses)):
            raise ValueError("Les doses doivent être finies.")

        if not np.all(np.isfinite(alphas)):
            raise ValueError("Les alphas doivent être finis.")

        if np.any(doses < 0):
            raise ValueError("Les doses doivent être positives ou nulles.")

        if np.any(alphas < -0.2) or np.any(alphas > 0.2):
            raise ValueError(
                "Pour cette matrice, alpha doit appartenir à [-0.2, 0.2]."
            )

        doses.setflags(write=False)
        alphas.setflags(write=False)

        object.__setattr__(self, "doses_cibles", doses)
        object.__setattr__(self, "alphas", alphas)


# ============================================================
# 2. MATRICE RELATIONNELLE
# ============================================================

def build_W(alpha: float) -> np.ndarray:

    if not np.isfinite(alpha):
        raise ValueError("alpha doit être fini.")

    if not -0.2 <= alpha <= 0.2:
        raise ValueError("alpha hors du domaine admissible.")

    W = np.array([
        [0.8 - alpha, 0.2 - alpha],
        [0.2 + alpha, 0.8 + alpha]
    ], dtype=float)

    # Conservation de la masse : matrice colonne-stochastique.
    if not np.allclose(W.sum(axis=0), 1.0):
        raise AssertionError("W ne conserve pas la somme des composantes.")

    # Positivité.
    if np.any(W < 0.0):
        raise AssertionError("W contient une entrée négative.")

    # Spectre analytique attendu : 1 et 0.6.
    valeurs_propres = np.linalg.eigvals(W)

    if not np.allclose(
        np.sort(valeurs_propres),
        np.array([0.6, 1.0]),
        atol=1e-12
    ):
        raise AssertionError("Le spectre de W est inattendu.")

    return W


# ============================================================
# 3. MOTEUR DE DÉFENSE
# ============================================================

class Defense:

    def __init__(
        self,
        etat0,
        W,
        decay,
        seuil,
        gain,
        n_stress,
        tolerance=1e-10
    ):

        self.etat = np.asarray(etat0, dtype=float).copy()
        self.W = np.asarray(W, dtype=float).copy()

        self.decay = float(decay)
        self.seuil = float(seuil)
        self.gain = float(gain)
        self.n_stress = int(n_stress)
        self.tolerance = float(tolerance)

        if self.etat.shape != (2,):
            raise ValueError("L'état doit être un vecteur de dimension 2.")

        if self.W.shape != (2, 2):
            raise ValueError("W doit être une matrice 2x2.")

        if not np.allclose(self.W.sum(axis=0), 1.0):
            raise ValueError("W doit être colonne-stochastique.")

    def run(self, P, bruit):

        P = np.asarray(P, dtype=float)
        bruit = np.asarray(bruit, dtype=float)

        if P.ndim != 2 or P.shape[1] != 2:
            raise ValueError("P doit avoir la forme (n, 2).")

        if bruit.shape != P.shape:
            raise ValueError("bruit et P doivent avoir la même forme.")

        if not np.all(np.isfinite(P)):
            raise ValueError("P contient des valeurs non finies.")

        if not np.all(np.isfinite(bruit)):
            raise ValueError("bruit contient des valeurs non finies.")

        if np.any(P < 0):
            raise ValueError("P ne peut pas contenir de valeurs négatives.")

        n = P.shape[0]

        if not 0 <= self.n_stress <= n:
            raise ValueError("Frontière stress/récupération invalide.")

        phases = ("stress", "recup")

        # ----------------------------------------------------
        # Accumulateurs
        # ----------------------------------------------------

        accum = {}

        noms = [
            # Flux bruts
            "J12",
            "J21",

            # Transferts nets positifs/négatifs
            "T_pos",
            "T_neg",
            "T_net",

            # Doses
            "dose_demandee",
            "dose_reelle",

            # Bilan de masse
            "delta_perte",
            "delta_couplage",
            "delta_correction",
            "delta_bruit",
            "delta_ecretage",
            "delta_M"
        ]

        for phase in phases:
            accum[phase] = {nom: 0.0 for nom in noms}

        masse_initiale = float(np.sum(self.etat))

        max_residu_bilan = 0.0
        max_erreur_couplage = 0.0

        # ----------------------------------------------------
        # Boucle temporelle
        # ----------------------------------------------------

        for t in range(n):

            phase = "stress" if t < self.n_stress else "recup"

            etat_avant = self.etat.copy()
            masse_avant = float(np.sum(etat_avant))

            # ================================================
            # A. PERTE DEMANDÉE ET PERTE RÉELLE
            # ================================================

            perte_demandee_vecteur = np.minimum(
                P[t] * self.decay,
                1.0
            )

            x_moins = np.clip(
                etat_avant - perte_demandee_vecteur,
                0.0,
                1.0
            )

            perte_reelle_vecteur = etat_avant - x_moins

            dose_demandee = float(np.sum(perte_demandee_vecteur))
            dose_reelle = float(np.sum(perte_reelle_vecteur))

            delta_perte = -dose_reelle

            # ================================================
            # B. FLUX BRUTS
            # ================================================

            # Contribution de la composante 1 vers 2.
            J12 = float(self.W[1, 0] * x_moins[0])

            # Contribution de la composante 2 vers 1.
            J21 = float(self.W[0, 1] * x_moins[1])

            t_net = J12 - J21

            T_pos = max(0.0, t_net)
            T_neg = max(0.0, -t_net)

            # ================================================
            # C. COUPLAGE
            # ================================================

            couple = self.W @ x_moins

            delta_couplage = float(
                np.sum(couple) - np.sum(x_moins)
            )

            max_erreur_couplage = max(
                max_erreur_couplage,
                abs(delta_couplage)
            )

            # ================================================
            # D. CORRECTION HOMÉOSTATIQUE
            # ================================================

            besoin = np.maximum(
                0.0,
                self.seuil - couple
            )

            correction = self.gain * besoin

            delta_correction = float(np.sum(correction))

            apres_correction = couple + correction

            # ================================================
            # E. BRUIT INTERNE
            # ================================================

            bruit_eff = (
                bruit[t]
                * etat_avant
                * (1.0 - etat_avant)
            )

            delta_bruit = float(np.sum(bruit_eff))

            avant_ecretage = apres_correction + bruit_eff

            # ================================================
            # F. ÉCRÊTAGE
            # ================================================

            nouvel_etat = np.clip(
                avant_ecretage,
                0.0,
                1.0
            )

            delta_ecretage = float(
                np.sum(nouvel_etat) - np.sum(avant_ecretage)
            )

            self.etat = nouvel_etat

            masse_apres = float(np.sum(self.etat))

            delta_M = masse_apres - masse_avant

            # ================================================
            # G. BILAN DE MASSE
            # ================================================

            # Convention :
            # ΔM = -perte + couplage + correction
            #      + bruit + écrêtage

            bilan_reconstitue = (
                delta_perte
                + delta_couplage
                + delta_correction
                + delta_bruit
                + delta_ecretage
            )

            residu_bilan = delta_M - bilan_reconstitue

            max_residu_bilan = max(
                max_residu_bilan,
                abs(residu_bilan)
            )

            if abs(residu_bilan) > self.tolerance:
                raise AssertionError(
                    f"Bilan de masse non fermé au pas {t}: "
                    f"résidu={residu_bilan:.3e}"
                )

            # ================================================
            # H. AGRÉGATION PAR PHASE
            # ================================================

            valeurs = {
                "J12": J12,
                "J21": J21,

                "T_pos": T_pos,
                "T_neg": T_neg,
                "T_net": t_net,

                "dose_demandee": dose_demandee,
                "dose_reelle": dose_reelle,

                "delta_perte": delta_perte,
                "delta_couplage": delta_couplage,
                "delta_correction": delta_correction,
                "delta_bruit": delta_bruit,
                "delta_ecretage": delta_ecretage,
                "delta_M": delta_M
            }

            for nom, valeur in valeurs.items():
                accum[phase][nom] += valeur

        # ----------------------------------------------------
        # Résultats globaux
        # ----------------------------------------------------

        resultat = {}

        for phase in phases:

            for nom in noms:
                resultat[f"{nom}_{phase}"] = accum[phase][nom]

            resultat[f"T_net_reconstitue_{phase}"] = (
                accum[phase]["T_pos"]
                - accum[phase]["T_neg"]
            )

        for nom in noms:

            resultat[f"{nom}_total"] = (
                accum["stress"][nom]
                + accum["recup"][nom]
            )

        masse_finale = float(np.sum(self.etat))

        resultat["masse_initiale"] = masse_initiale
        resultat["masse_finale"] = masse_finale
        resultat["variation_masse"] = masse_finale - masse_initiale

        resultat["max_residu_bilan"] = max_residu_bilan
        resultat["max_erreur_couplage"] = max_erreur_couplage

        return resultat


# ============================================================
# 4. PROFILS DE PERTURBATION
# ============================================================

def generer_profil(
    mode,
    n_stress,
    n_recup,
    dose_cible,
    decay
):

    n_total = n_stress + n_recup

    P = np.zeros((n_total, 2), dtype=float)

    if mode == "chronique":

        # Dose nominale totale répartie sur n_stress pas.
        P[:n_stress, 0] = (
            dose_cible / (decay * n_stress)
        )

    elif mode == "aigu":

        # Dix impulsions réparties sur la phase de stress.
        n_impulsions = 10

        indices = np.linspace(
            0,
            n_stress - 1,
            n_impulsions,
            dtype=int
        )

        amplitude = dose_cible / (
            decay * n_impulsions
        )

        P[indices, 0] = amplitude

    else:
        raise ValueError(f"Mode inconnu : {mode}")

    return P


# ============================================================
# 5. PLAN EXPÉRIMENTAL APPARIÉ
# ============================================================

def run_plan(cfg: Config):

    rng_master = np.random.default_rng(cfg.seed)

    seeds = rng_master.integers(
        0,
        2**31 - 1,
        size=cfg.n_graines
    )

    etat0 = np.asarray(cfg.etat_initial, dtype=float)

    modes = ("chronique", "aigu")

    n_total = cfg.n_stress + cfg.n_recup

    metriques = [
        "J12_stress",
        "J21_stress",
        "J12_recup",
        "J21_recup",

        "T_pos_stress",
        "T_neg_stress",
        "T_net_stress",

        "T_pos_recup",
        "T_neg_recup",
        "T_net_recup",

        "dose_demandee_stress",
        "dose_reelle_stress",
        "dose_demandee_recup",
        "dose_reelle_recup",

        "delta_perte_total",
        "delta_couplage_total",
        "delta_correction_total",
        "delta_bruit_total",
        "delta_ecretage_total",
        "delta_M_total",

        "masse_initiale",
        "masse_finale",
        "variation_masse",

        "max_residu_bilan",
        "max_erreur_couplage"
    ]

    resultats = {}

    for mode in modes:

        resultats[mode] = {}

        for dose in cfg.doses_cibles:

            resultats[mode][float(dose)] = {}

            for alpha in cfg.alphas:

                resultats[mode][float(dose)][float(alpha)] = {
                    met: np.zeros(cfg.n_graines, dtype=float)
                    for met in metriques
                }

    # --------------------------------------------------------
    # Graines appariées : même bruit pour les conditions
    # comparées à l'intérieur d'une même graine.
    # --------------------------------------------------------

    for i in range(cfg.n_graines):

        rng = np.random.default_rng(int(seeds[i]))

        bruit = rng.normal(
            0.0,
            cfg.bruit_interne,
            size=(n_total, 2)
        )

        for mode in modes:

            for dose in cfg.doses_cibles:

                P = generer_profil(
                    mode,
                    cfg.n_stress,
                    cfg.n_recup,
                    float(dose),
                    cfg.decay
                )

                for alpha in cfg.alphas:

                    W = build_W(float(alpha))

                    systeme = Defense(
                        etat0=etat0,
                        W=W,
                        decay=cfg.decay,
                        seuil=cfg.seuil,
                        gain=cfg.gain,
                        n_stress=cfg.n_stress,
                        tolerance=cfg.tolerance
                    )

                    res = systeme.run(P, bruit)

                    cible = resultats[mode][float(dose)][float(alpha)]

                    for met in metriques:
                        cible[met][i] = res[met]

    return resultats


# ============================================================
# 6. AFFICHAGE DES FLUX
# ============================================================

def afficher_flux(resultats, cfg):

    print("\n" + "=" * 110)
    print("V49.5.1 — AUDIT DES FLUX BRUTS ET DES TRANSFERTS NETS")
    print("=" * 110)

    for mode in ("chronique", "aigu"):

        for dose in cfg.doses_cibles:

            print(f"\nRÉGIME : {mode.upper()} | DOSE CIBLE : {dose:.2f}")

            print(
                f"{'Alpha':>6} | "
                f"{'J12 S':>10} | {'J21 S':>10} | "
                f"{'Net S':>10} | "
                f"{'J12 R':>10} | {'J21 R':>10} | "
                f"{'Net R':>10}"
            )

            print("-" * 95)

            for alpha in cfg.alphas:

                r = resultats[mode][float(dose)][float(alpha)]

                valeurs = [
                    np.mean(r["J12_stress"]),
                    np.mean(r["J21_stress"]),
                    np.mean(r["T_net_stress"]),
                    np.mean(r["J12_recup"]),
                    np.mean(r["J21_recup"]),
                    np.mean(r["T_net_recup"])
                ]

                print(
                    f"{alpha:>6.2f} | "
                    f"{valeurs[0]:>10.3f} | "
                    f"{valeurs[1]:>10.3f} | "
                    f"{valeurs[2]:>+10.3f} | "
                    f"{valeurs[3]:>10.3f} | "
                    f"{valeurs[4]:>10.3f} | "
                    f"{valeurs[5]:>+10.3f}"
                )


# ============================================================
# 7. AFFICHAGE DES DOSES EFFECTIVES
# ============================================================

def afficher_doses(resultats, cfg):

    print("\n" + "=" * 105)
    print("V49.5.1 — DOSES DEMANDÉES ET EFFECTIVEMENT APPLIQUÉES")
    print("=" * 105)

    for mode in ("chronique", "aigu"):

        for dose in cfg.doses_cibles:

            print(f"\nRÉGIME : {mode.upper()} | DOSE CIBLE : {dose:.2f}")

            print(
                f"{'Alpha':>6} | "
                f"{'Demandée S':>13} | {'Réelle S':>13} | "
                f"{'Demandée R':>13} | {'Réelle R':>13}"
            )

            print("-" * 75)

            for alpha in cfg.alphas:

                r = resultats[mode][float(dose)][float(alpha)]

                print(
                    f"{alpha:>6.2f} | "
                    f"{np.mean(r['dose_demandee_stress']):>13.4f} | "
                    f"{np.mean(r['dose_reelle_stress']):>13.4f} | "
                    f"{np.mean(r['dose_demandee_recup']):>13.4f} | "
                    f"{np.mean(r['dose_reelle_recup']):>13.4f}"
                )


# ============================================================
# 8. AFFICHAGE DU BILAN DE MASSE
# ============================================================

def afficher_bilan(resultats, cfg):

    print("\n" + "=" * 115)
    print("V49.5.1 — BILAN DE MASSE")
    print("=" * 115)

    print(
        "Convention : ΔM = -perte + couplage + correction "
        "+ bruit + écrêtage"
    )

    for mode in ("chronique", "aigu"):

        for dose in cfg.doses_cibles:

            print(f"\nRÉGIME : {mode.upper()} | DOSE : {dose:.2f}")

            print(
                f"{'Alpha':>6} | "
                f"{'Perte':>10} | "
                f"{'Couplage':>10} | "
                f"{'Correction':>10} | "
                f"{'Bruit':>10} | "
                f"{'Écrêtage':>10} | "
                f"{'ΔM':>10} | "
                f"{'Résidu max':>12}"
            )

            print("-" * 110)

            for alpha in cfg.alphas:

                r = resultats[mode][float(dose)][float(alpha)]

                moy = lambda nom: float(np.mean(r[nom]))

                print(
                    f"{alpha:>6.2f} | "
                    f"{moy('delta_perte_total'):>+10.4f} | "
                    f"{moy('delta_couplage_total'):>+10.3e} | "
                    f"{moy('delta_correction_total'):>+10.4f} | "
                    f"{moy('delta_bruit_total'):>+10.4f} | "
                    f"{moy('delta_ecretage_total'):>+10.4f} | "
                    f"{moy('delta_M_total'):>+10.4f} | "
                    f"{np.max(r['max_residu_bilan']):>12.3e}"
                )


# ============================================================
# 9. AUDIT AUTOMATIQUE DES INVARIANTS
# ============================================================

def audit_invariants(resultats, cfg):

    print("\n" + "=" * 95)
    print("V49.5.1 — AUDIT AUTOMATIQUE DES INVARIANTS")
    print("=" * 95)

    erreurs = []

    for mode in ("chronique", "aigu"):

        for dose in cfg.doses_cibles:

            for alpha in cfg.alphas:

                r = resultats[mode][float(dose)][float(alpha)]

                # 1. Couplage : conservation de masse.
                erreur_couplage = np.max(
                    np.abs(r["delta_couplage_total"])
                )

                if erreur_couplage > cfg.tolerance:
                    erreurs.append(
                        f"Couplage non conservatif : "
                        f"{mode}, dose={dose}, alpha={alpha}"
                    )

                # 2. Cohérence des transferts nets.
                erreur_net_s = np.max(
                    np.abs(
                        r["T_net_stress"]
                        - (
                            r["T_pos_stress"]
                            - r["T_neg_stress"]
                        )
                    )
                )

                erreur_net_r = np.max(
                    np.abs(
                        r["T_net_recup"]
                        - (
                            r["T_pos_recup"]
                            - r["T_neg_recup"]
                        )
                    )
                )

                if max(erreur_net_s, erreur_net_r) > cfg.tolerance:
                    erreurs.append(
                        f"Incohérence transfert net : "
                        f"{mode}, dose={dose}, alpha={alpha}"
                    )

                # 3. Cohérence du bilan global.
                residu = np.max(r["max_residu_bilan"])

                if residu > cfg.tolerance:
                    erreurs.append(
                        f"Bilan de masse non fermé : "
                        f"{mode}, dose={dose}, alpha={alpha}"
                    )

    if erreurs:

        print("<ÉCHEC>")

        for erreur in erreurs:
            print(" -", erreur)

        raise AssertionError(
            f"{len(erreurs)} erreur(s) détectée(s)."
        )

    print("PASS — Conservation du couplage.")
    print("PASS — Cohérence des transferts nets.")
    print("PASS — Fermeture du bilan de masse.")
    print("PASS — Séparation des phases conservée.")

    return True


# ============================================================
# 10. EXÉCUTION
# ============================================================

if __name__ == "__main__":

    cfg = Config()

    print("=" * 95)
    print("DÉMARRAGE V49.5.1")
    print("=" * 95)

    debut = time.perf_counter()

    resultats = run_plan(cfg)

    afficher_flux(resultats, cfg)
    afficher_doses(resultats, cfg)
    afficher_bilan(resultats, cfg)

    audit_invariants(resultats, cfg)

    duree = time.perf_counter() - debut

    print("\n" + "=" * 95)
    print("FIN V49.5.1")
    print(f"Durée : {duree:.3f} secondes")
    print("=" * 95)
