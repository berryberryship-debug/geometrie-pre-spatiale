#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V51.3b — MCC PHYSIOLOGIE BOOSTÉE (CORRIGÉE) : PROTECTION RÉELLE
===============================================================
- Correction du signe et de l'ancrage de la règle de couplage.
- La mémoire augmente le seuil proportionnellement au stress vécu.
- Validation d'une réduction de 17.4% du stress global.
"""

import numpy as np
import math
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Trace:
    trace_id: str; origine_step: int; contenu: Dict[str, float]; persistance: float; taux_extinction: float

class MemoireCirconstancielle:
    def __init__(self): self.traces: List[Trace] = []
    def ajouter(self, trace: Trace): self.traces.append(trace)
    def actives(self, t_actuel: int) -> List[Dict[str, Any]]:
        traces = []
        for tr in self.traces:
            dt = max(0, t_actuel - tr.origine_step)
            activation = tr.persistance * np.exp(-tr.taux_extinction * dt)
            if activation > 1e-4:
                traces.append({'activation': float(activation), 'contenu': tr.contenu})
        return traces

@dataclass
class RegleCouplage:
    nom: str; facteur: str; parametre_cible: str; coefficient: float; valeur_reference: float; minimum: float; maximum: float

class CouplageCirconstanciel:
    def __init__(self, regles: List[RegleCouplage], actif: bool = True):
        self.regles = regles; self.actif = actif
    def evaluer(self, indicateurs: Dict[str, float]) -> Dict[str, Any]:
        params = {}
        if not self.actif: return {'parametres_proposes': params}
        for regle in self.regles:
            val = indicateurs.get(regle.facteur, 0.0)
            correction = regle.coefficient * val 
            cible = float(np.clip(regle.valeur_reference + correction, regle.minimum, regle.maximum))
            params[regle.parametre_cible] = cible
        return {'parametres_proposes': params}

def courbe_activite(heure_locale):
    d_matin = min(abs(heure_locale - 9.5), 24 - abs(heure_locale - 9.5))
    act_matin = 0.6 * math.exp(-(d_matin**2) / (2 * 1.2**2))
    d_soir = min(abs(heure_locale - 19.5), 24 - abs(heure_locale - 19.5))
    act_soir = 1.0 * math.exp(-(d_soir**2) / (2 * 1.8**2))
    d_nuit = min(abs(heure_locale - 22.5), 24 - abs(heure_locale - 22.5))
    act_nuit = 0.5 * math.exp(-(d_nuit**2) / (2 * 1.0**2))
    return min(1.0, act_matin + act_soir + act_nuit)

class OrchestrateurContextualise:
    def __init__(self, decalage_horaire: int):
        self.decalage = decalage_horaire
        self.regle = RegleCouplage('memoire_stress', 'indicateur_memoriel', 'seuil_reponse', 0.8, 0.5, 0.0, 1.0)

    def simuler_journee(self, activer_memoire: bool):
        memoire = MemoireCirconstancielle()
        couplage = CouplageCirconstanciel([self.regle], actif=activer_memoire)
        historique = []
        
        for t in range(24):
            heure_A = t
            heure_B = (t + self.decalage) % 24
            act_A = courbe_activite(heure_A)
            act_B = courbe_activite(heure_B)
            friction = abs(act_A - act_B)
            
            traces = memoire.actives(t)
            if traces:
                num = sum(tr['activation'] * tr['contenu']['friction'] for tr in traces)
                den = sum(tr['activation'] for tr in traces) + 1e-9
                indicateur_memoriel = num / den
            else:
                indicateur_memoriel = 0.0

            params = {}
            if activer_memoire:
                params = couplage.evaluer({'indicateur_memoriel': indicateur_memoriel})['parametres_proposes']
            
            seuil_reponse = params.get('seuil_reponse', 0.5)
            stress_effectif = friction * (1.0 - 0.8 * seuil_reponse)
            
            trace = Trace(f"T_{t}", t, {'friction': stress_effectif}, 1.0, 0.2)
            memoire.ajouter(trace)
            
            historique.append({
                'heure_A': heure_A, 'heure_B': heure_B,
                'friction': friction, 'indicateur_mem': indicateur_memoriel,
                'seuil_reponse': seuil_reponse, 'stress_effectif': stress_effectif
            })
        return historique

def afficher_comparaison():
    print("=" * 110)
    print("V51.3b — MCC PHYSIOLOGIE BOOSTÉE (CORRIGÉE)")
    print("=" * 110)
    decalage = 13
    orc = OrchestrateurContextualise(decalage)
    hist_sans = orc.simuler_journee(activer_memoire=False)
    hist_avec = orc.simuler_journee(activer_memoire=True)
    
    print(f"{'H(A)':>4} | {'H(B)':>4} | {'Friction':>9} | {'Seuil(Actif)':>13} | {'Stress(Sans)':>12} | {'Stress(Avec)':>12} | {'Écart':>10}")
    print("-" * 95)
    total_sans = 0
    total_avec = 0
    for h_sans, h_avec in zip(hist_sans, hist_avec):
        ecart = h_avec['stress_effectif'] - h_sans['stress_effectif']
        print(f"{h_sans['heure_A']:>4}h | {h_sans['heure_B']:>3}h | {h_sans['friction']:>9.2f} | {h_avec['seuil_reponse']:>13.3f} | {h_sans['stress_effectif']:>12.3f} | {h_avec['stress_effectif']:>12.3f} | {ecart:>+10.3f}")
        total_sans += h_sans['stress_effectif']
        total_avec += h_avec['stress_effectif']
    print("-" * 95)
    print(f"Stress total SANS mémoire : {total_sans:.3f}")
    print(f"Stress total AVEC mémoire : {total_avec:.3f}")
    print(f"Réduction du stress : {(1 - total_avec/total_sans)*100:.1f}%")

if __name__ == "__main__":
    afficher_comparaison()
