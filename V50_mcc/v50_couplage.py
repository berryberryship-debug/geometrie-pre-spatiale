#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V50.4 — Propositions de couplage causal, désactivées par défaut."""
from dataclasses import dataclass,asdict
@dataclass(frozen=True)
class RegleCouplage:
    nom:str; facteur:str; parametre_cible:str; coefficient:float
    valeur_reference:float; minimum:float; maximum:float
    statut:str='hypothese_a_tester'
    def __post_init__(self):
        if self.minimum>self.maximum or not self.minimum<=self.valeur_reference<=self.maximum: raise ValueError('Bornes invalides')
        if self.statut!='hypothese_a_tester': raise ValueError('Statut causal doit rester hypothétique')
class CouplageCirconstanciel:
    def __init__(self,regles=(),actif=False): self.regles=tuple(regles); self.actif=bool(actif)
    def evaluer(self,facteurs):
        props={}; audit=[]
        for r in self.regles:
            if r.facteur not in facteurs: audit.append({'regle':r.nom,'statut':'facteur_absent'}); continue
            x=float(facteurs[r.facteur])
            if not 0<=x<=1: raise ValueError(f'{r.facteur} doit être normalisé dans [0,1]')
            y=min(r.maximum,max(r.minimum,r.valeur_reference+r.coefficient*x))
            audit.append({**asdict(r),'facteur':x,'valeur_proposee':y,'applique':self.actif})
            if self.actif: props[r.parametre_cible]=y
        return {'couplage_actif':self.actif,'parametres_proposes':props,'audit':audit,'statut':'hypothèses à tester, non causalité démontrée'}
if __name__=='__main__':
    rule=RegleCouplage('exposition_decay','exposition','decay',.02,.1,0.,.5)
    print(CouplageCirconstanciel([rule]).evaluer({'exposition':.7}))
