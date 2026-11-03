#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V50.2.1 — Calibre puis journalise un seul run nominal."""
import argparse, json
from datetime import datetime, timezone
import numpy as np
from v50_1_noyau import Config, build_W, construire_profil, calibrer_dose, simuler
from v50_2_mcc import MCCJournal

def executer(cfg,mode,alpha,gain,seed,dossier='journaux'):
    rng=np.random.default_rng(int(seed)); profil=construire_profil(mode,cfg.n_stress,cfg.n_recup)
    bruit=rng.normal(0,cfg.bruit_interne,size=(len(profil),2)); W=build_W(alpha)
    amplitude,calibration=calibrer_dose(cfg,W,gain,profil,bruit) # aucune écriture pendant calibration
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    run_id=f'{mode}-a{alpha:.3f}-g{gain:.3f}-seed{int(seed)}-{stamp}'
    journal=MCCJournal(f'{dossier}/{run_id}.jsonl',run_id)
    def observer(step,state,bilan,ctx):
        conf={'situation':{'phase':ctx['phase'],'mode':mode},'relations':{'matrice_W':ctx['W']},'facteurs_momentanes':{'profil_t':ctx['profil_t'],'amplitude':amplitude,'gain':gain,'alpha':alpha},'acteurs':None,'environnement':None,'traces_historiques':None}
        events=[]
        if step==0:
            events=[{'categorie':'demarrage_run','contenu':{'mode':mode,'alpha':alpha,'gain':gain,'seed':int(seed),'amplitude':amplitude,'dose_calibree':calibration['dose_reelle']},'statut':'observe','provenance':'paramètres et résultat du calibrateur','incertitude':0.0}]
        journal.capturer(step,state,conf,events,{'bilan':bilan,'version_noyau':'V50.1 / V49.6.1-H'})
    result=simuler(cfg,W,gain,profil,amplitude,bruit,observer=observer)
    result.update({'amplitude_calibree':float(amplitude),'seed':int(seed),'run_id':run_id,'journal':f'{dossier}/{run_id}.jsonl'})
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--seed',type=int,default=42); p.add_argument('--mode',choices=['chronique','aigu'],default='chronique'); p.add_argument('--alpha',type=float,default=0.); p.add_argument('--gain',type=float,default=.8); a=p.parse_args()
    r=executer(Config(n_graines=1),a.mode,a.alpha,a.gain,a.seed)
    print(json.dumps({k:v for k,v in r.items() if k not in ('phases','etat_stress')},indent=2,ensure_ascii=False))
