#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V50.1 — Noyau dynamique, héritage V49.6.1-H fourni par l'utilisateur."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional
import numpy as np

@dataclass(frozen=True)
class Config:
    n_graines:int=10; n_stress:int=100; n_recup:int=20; seed:int=42
    dose_reelle_cible:float=.50; tolerance_dose:float=1e-6
    alphas:tuple=(0.,.20); gains:tuple=(0.,.8); seuil:float=.5
    decay:float=.10; etat_initial:tuple=(1.,1.); bruit_interne:float=.01
    tolerance_bilan:float=1e-10; calibration_grille_points:int=100
    calibration_max_amplitude:float=1000.; calibration_iterations:int=80
    def __post_init__(self):
        if self.n_graines<1 or self.n_stress<10 or self.n_recup<0: raise ValueError('Dimensions invalides.')
        if self.tolerance_dose<=0 or self.calibration_grille_points<2 or self.calibration_max_amplitude<=0: raise ValueError('Calibration invalide.')
        if len(self.etat_initial)!=2 or any(not 0<=float(x)<=1 for x in self.etat_initial): raise ValueError('État initial invalide.')
        if any(not -.2<=float(a)<=.2 for a in self.alphas): raise ValueError('Alpha hors [-.2,.2].')

def build_W(alpha):
    W=np.array([[.8-alpha,.2-alpha],[.2+alpha,.8+alpha]],float)
    if np.any(W<0) or not np.allclose(W.sum(axis=0),1.): raise ValueError('W invalide.')
    return W

def construire_profil(mode,n_stress,n_recup):
    p=np.zeros(n_stress+n_recup)
    if mode=='chronique': p[:n_stress]=1/n_stress
    elif mode=='aigu': p[np.linspace(0,n_stress-1,10,dtype=int)]=.1
    else: raise ValueError(f'Mode inconnu: {mode}')
    return p

def simuler(cfg,W,gain,profil,amplitude,bruit,observer:Optional[Callable]=None):
    etat=np.asarray(cfg.etat_initial,float).copy(); ref=etat.copy()
    profil=np.asarray(profil,float); bruit=np.asarray(bruit,float); n=len(profil)
    if bruit.shape!=(n,2): raise ValueError('Forme de bruit invalide.')
    phases={p:{k:0. for k in ('dose_demandee','dose_reelle','delta_perte','delta_couplage','correction_brute','delta_bruit','delta_ecretage','delta_M')} for p in ('stress','recup')}
    Fmin=float(np.prod(etat)); dstress=None; estress=None; mr=0.; mc=0.
    for t in range(n):
        phase='stress' if t<cfg.n_stress else 'recup'; avant=etat.copy(); masse=float(avant.sum())
        demande=np.tanh(profil[t]*amplitude*cfg.decay); pd=np.array([demande,0.])
        apres=np.clip(avant-pd,0,1); perte=avant-apres; dr=float(perte.sum()); dd=float(pd.sum())
        couple=W@apres; dc=float(couple.sum()-apres.sum()); mc=max(mc,abs(dc))
        correction=gain*np.tanh(2*np.maximum(0,cfg.seuil-couple)); cr=float(correction.sum())
        be=bruit[t]*avant*(1-avant); db=float(be.sum())
        avant_clip=couple+correction+be; nouvel=np.clip(avant_clip,0,1); de=float(nouvel.sum()-avant_clip.sum()); etat=nouvel
        dm=float(etat.sum()-masse); residu=dm-(-dr+dc+cr+db+de); mr=max(mr,abs(residu))
        if abs(residu)>cfg.tolerance_bilan: raise AssertionError(f'Bilan non fermé t={t}: {residu}')
        vals={'dose_demandee':dd,'dose_reelle':dr,'delta_perte':-dr,'delta_couplage':dc,'correction_brute':cr,'delta_bruit':db,'delta_ecretage':de,'delta_M':dm}
        for k,v in vals.items(): phases[phase][k]+=v
        dist=float(np.linalg.norm(etat-ref)); F=float(etat[0]*etat[1]); Fmin=min(Fmin,F)
        if t==cfg.n_stress-1: dstress=dist; estress=etat.copy()
        if observer is not None:
            observer(t,{'x1':float(etat[0]),'x2':float(etat[1]),'F':F,'distance_reference':dist},
                     {**vals,'residu_bilan':residu,'erreur_couplage':dc,
                      'delta_net_correction_apres_ecretage':float(np.sum(nouvel-couple-be))},
                     {'phase':phase,'profil_t':float(profil[t]),'amplitude':float(amplitude),'gain':float(gain),'W':W.tolist()})
    df=float(np.linalg.norm(etat-ref)); dstress=df if dstress is None else dstress
    return {'dose_demandee':sum(x['dose_demandee'] for x in phases.values()),'dose_reelle':sum(x['dose_reelle'] for x in phases.values()),'F_min':Fmin,'F_final':float(np.prod(etat)),'x1_final':float(etat[0]),'x2_final':float(etat[1]),'distance_stress':dstress,'distance_finale':df,'amelioration_recuperation':dstress-df,'phases':phases,'max_residu':mr,'max_erreur_couplage':mc,'etat_stress':estress}

def calibrer_dose(cfg,W,gain,profil,bruit):
    """Grille + encadrements vérifiés + dichotomie. Grille non exhaustive."""
    cible=cfg.dose_reelle_cible; ag=np.linspace(0,cfg.calibration_max_amplitude,cfg.calibration_grille_points)
    dg=np.array([simuler(cfg,W,gain,profil,float(a),bruit)['dose_reelle'] for a in ag]); eg=dg-cible
    nonmono=bool(np.any(np.diff(dg)<-cfg.tolerance_dose)); brackets=[]
    for i in range(len(ag)):
        if abs(eg[i])<=cfg.tolerance_dose: brackets.append((float(ag[i]),float(ag[i]),0))
        if i<len(ag)-1 and eg[i]*eg[i+1]<0: brackets.append((float(ag[i]),float(ag[i+1]),1))
    if not brackets: raise RuntimeError(f'Cible non encadrée sur la grille: min={dg.min():.8g}, max={dg.max():.8g}, cible={cible:.8g}')
    sols=[]
    for lo,hi,kind in brackets:
        if not kind:
            r=simuler(cfg,W,gain,profil,lo,bruit); sols.append((lo,r)); continue
        flo=simuler(cfg,W,gain,profil,lo,bruit)['dose_reelle']-cible
        fhi=simuler(cfg,W,gain,profil,hi,bruit)['dose_reelle']-cible
        if flo*fhi>=0: continue
        best=None
        for _ in range(cfg.calibration_iterations):
            mid=(lo+hi)/2; r=simuler(cfg,W,gain,profil,mid,bruit); fm=r['dose_reelle']-cible; best=(mid,r)
            if abs(fm)<=cfg.tolerance_dose: break
            if flo*fm<=0: hi=mid; fhi=fm
            else: lo=mid; flo=fm
        if best and abs(best[1]['dose_reelle']-cible)<=cfg.tolerance_dose: sols.append(best)
    if not sols: raise RuntimeError('Aucun intervalle détecté n’a convergé à la tolérance.')
    sols.sort(key=lambda x:x[0]); a,r=sols[0]
    r['calibration']={'statut':'convergee','non_monotone_sur_grille':nonmono,'solutions_detectees':len(sols),'selection':'plus_petite_amplitude_detectee'}
    return a,r

def run_plan(cfg):
    master=np.random.default_rng(cfg.seed); seeds=master.integers(0,2**31-1,size=cfg.n_graines); out={}
    for mode in ('chronique','aigu'):
        out[mode]={}
        profil=construire_profil(mode,cfg.n_stress,cfg.n_recup)
        for gain in cfg.gains:
            out[mode][gain]={}
            for alpha in cfg.alphas:
                vals=[]
                for seed in seeds:
                    rng=np.random.default_rng(int(seed)); bruit=rng.normal(0,cfg.bruit_interne,size=(len(profil),2))
                    a,r=calibrer_dose(cfg,build_W(alpha),gain,profil,bruit); vals.append({'amplitude':a,**{k:r[k] for k in ('dose_reelle','F_min','F_final','distance_stress','distance_finale','amelioration_recuperation','max_residu','max_erreur_couplage')}})
                out[mode][gain][alpha]=vals
    return out

if __name__=='__main__':
    import time
    c=Config(); t=time.perf_counter(); r=run_plan(c)
    for mode in r:
        print('\n',mode.upper())
        for gain in r[mode]:
            for alpha,rows in r[mode][gain].items():
                print('gain',gain,'alpha',alpha,'dose',np.mean([x['dose_reelle'] for x in rows]),'Fmin',np.mean([x['F_min'] for x in rows]))
    print('Durée:',time.perf_counter()-t)
