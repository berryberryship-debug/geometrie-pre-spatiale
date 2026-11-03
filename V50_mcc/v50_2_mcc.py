#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V50.2 — Collecteur passif et journal append-only chaîné SHA-256."""
import copy, hashlib, json, math
from pathlib import Path
from datetime import datetime, timezone
DIMENSIONS=('acteurs','relations','situation','environnement','traces_historiques','facteurs_momentanes')
STATUTS={'observe','rapporte','infere'}
def normaliser(v):
    if v is None or isinstance(v,(str,bool,int)): return v
    if isinstance(v,float):
        if not math.isfinite(v): raise ValueError('NaN/inf interdits')
        return v
    if hasattr(v,'tolist'): return normaliser(v.tolist())
    if hasattr(v,'item'): return normaliser(v.item())
    if isinstance(v,dict): return {str(k):normaliser(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [normaliser(x) for x in v]
    raise TypeError(type(v).__name__)
def canonique(x): return json.dumps(normaliser(x),sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def digest(x): return hashlib.sha256(canonique(x).encode()).hexdigest()
def verifier_journal(path):
    p=Path(path); prev='0'*64; seq=1; rid=None; last=-1
    if not p.exists(): return {'valide':True,'nombre':0,'dernier_hash':prev,'run_id':None,'derniere_etape':-1}
    with p.open(encoding='utf8') as f:
        for n,line in enumerate(f,1):
            if not line.strip(): continue
            rec=json.loads(line); h=rec.pop('hash',None)
            if h is None or rec.get('sequence')!=seq or rec.get('previous_hash')!=prev or digest(rec)!=h: raise ValueError(f'Chaîne invalide ligne {n}')
            if rid is None: rid=rec['run_id']
            elif rid!=rec['run_id']: raise ValueError('run_id incohérent')
            last=rec['step']; prev=h; seq+=1
    return {'valide':True,'nombre':seq-1,'dernier_hash':prev,'run_id':rid,'derniere_etape':last}
def valider_evenement(e):
    req={'categorie','contenu','statut','provenance'}
    if not isinstance(e,dict) or not req.issubset(e): raise ValueError(f'Événement incomplet: {req}')
    x=normaliser(e)
    if x['statut'] not in STATUTS: raise ValueError('Statut épistémique invalide')
    if not x['categorie'] or x['provenance'] in ('',None,{},[]): raise ValueError('Catégorie/provenance obligatoire')
    inc=x.get('incertitude')
    if inc is not None and (not isinstance(inc,(int,float)) or not 0<=inc<=1): raise ValueError('Incertitude hors [0,1]')
    x.setdefault('incertitude',None); x.setdefault('liens',[]); x.setdefault('validite_debut',None); x.setdefault('validite_fin',None)
    return x
class MCCJournal:
    def __init__(self,path,run_id):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True); self.run_id=str(run_id)
        a=verifier_journal(self.path)
        if a['run_id'] not in (None,self.run_id): raise ValueError('Journal d’un autre run')
        self.seq=a['nombre']+1; self.prev=a['dernier_hash']; self.last=a['derniere_etape']; self.event_seq=0
        if self.path.exists():
            with self.path.open(encoding='utf8') as f:
                self.event_seq=sum(len(json.loads(x).get('events',[])) for x in f if x.strip())
    def capturer(self,step,system_state,configuration=None,evenements=None,metadata=None):
        if isinstance(step,bool) or not isinstance(step,int) or step<0 or step<=self.last: raise ValueError('Étape invalide/non croissante')
        cfg=configuration or {}; events=[]
        for e in evenements or []:
            x=valider_evenement(e); self.event_seq+=1; x['event_id']=f'{self.run_id}:E{self.event_seq:08d}'; events.append(x)
        payload={'version':'V50.2','run_id':self.run_id,'sequence':self.seq,'step':step,'timestamp_utc':datetime.now(timezone.utc).isoformat(),'system_state':normaliser(copy.deepcopy(system_state)),'configuration':{d:normaliser(copy.deepcopy(cfg.get(d))) for d in DIMENSIONS},'events':events,'metadata':normaliser(metadata or {}),'previous_hash':self.prev}
        h=digest(payload); rec=dict(payload,hash=h)
        with self.path.open('a',encoding='utf8') as f: f.write(canonique(rec)+'\n'); f.flush()
        self.prev=h; self.seq+=1; self.last=step; return h
if __name__=='__main__':
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        j=MCCJournal(Path(d)/'test.jsonl','TEST'); j.capturer(0,{'x':1.0}); print(verifier_journal(j.path))
