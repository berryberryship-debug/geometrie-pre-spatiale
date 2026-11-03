#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V50.3 — Mémoire de traces circonstancielles, sans rétroaction moteur."""
from dataclasses import dataclass,asdict
from pathlib import Path
import json, math
@dataclass
class Trace:
    trace_id:str; origine_step:int; contenu:object; statut:str; provenance:str
    persistance:float=1.0; taux_extinction:float=0.0
    def __post_init__(self):
        if self.statut not in {'observe','rapporte','infere'}: raise ValueError('Statut invalide')
        if not 0<=self.persistance<=1 or self.taux_extinction<0: raise ValueError('Paramètres de trace invalides')
class MemoireCirconstancielle:
    def __init__(self,path='memoire_v50_3.json'): self.path=Path(path); self.traces={}
    def ajouter(self,t):
        if t.trace_id in self.traces: raise ValueError('Identifiant déjà utilisé')
        self.traces[t.trace_id]=t
    def activation(self,trace_id,step):
        t=self.traces[trace_id]
        if step<t.origine_step: return 0.0
        return float(t.persistance*math.exp(-t.taux_extinction*(step-t.origine_step)))
    def actives(self,step,seuil=0.):
        if not 0<=seuil<=1: raise ValueError('Seuil invalide')
        return [{**asdict(t),'activation':self.activation(k,step),'step_interrogation':step} for k,t in self.traces.items() if self.activation(k,step)>seuil]
    def sauvegarder(self): self.path.write_text(json.dumps({'version':'V50.3','traces':[asdict(t) for t in self.traces.values()]},ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
    def charger(self):
        x=json.loads(self.path.read_text(encoding='utf8'))
        if x.get('version')!='V50.3': raise ValueError('Version incompatible')
        self.traces={z['trace_id']:Trace(**z) for z in x['traces']}
if __name__=='__main__':
    m=MemoireCirconstancielle(); m.ajouter(Trace('T1',0,{'event':'test'},'observe','test',1.,.01)); print(m.actives(20))
