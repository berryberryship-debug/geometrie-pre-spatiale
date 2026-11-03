#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V50.5 — Tests d'intégration et de non-interférence."""
import tempfile
import numpy as np
from v50_1_noyau import Config,build_W,construire_profil,simuler
from v50_2_mcc import MCCJournal,verifier_journal
from v50_3_memoire import MemoireCirconstancielle,Trace
from v50_4_couplage import CouplageCirconstanciel,RegleCouplage

def test_non_interference():
    c=Config(n_graines=1,n_stress=20,n_recup=5); p=construire_profil('chronique',20,5); b=np.random.default_rng(123).normal(0,c.bruit_interne,(25,2)); W=build_W(0.)
    a=simuler(c,W,.8,p,2.,b); captures=[]
    z=simuler(c,W,.8,p,2.,b,observer=lambda *x:captures.append(x))
    keys=('dose_reelle','F_min','F_final','x1_final','x2_final','distance_stress','distance_finale','max_residu','max_erreur_couplage')
    return len(captures)==25 and all(a[k]==z[k] for k in keys)
def test_journal():
    with tempfile.TemporaryDirectory() as d:
        j=MCCJournal(f'{d}/j.jsonl','TEST'); j.capturer(0,{'x':.5}); j.capturer(1,{'x':.4}); a=verifier_journal(j.path); return a['valide'] and a['nombre']==2
def test_memoire():
    m=MemoireCirconstancielle(); m.ajouter(Trace('T',0,{},'observe','test',1.,.01)); return m.activation('T',0)==1. and m.activation('T',100)<m.activation('T',10)
def test_couplage():
    r=RegleCouplage('r','f','decay',.02,.1,0.,.5); x=CouplageCirconstanciel([r],False).evaluer({'f':.5}); return x['parametres_proposes']=={}
def main():
    tests={'non_interference':test_non_interference(),'integrite_journal':test_journal(),'memoire':test_memoire(),'couplage_inactif':test_couplage()}
    for k,v in tests.items(): print(f'{k}: {"PASS" if v else "FAIL"}')
    print('GLOBAL:', 'PASS' if all(tests.values()) else 'FAIL')
    if not all(tests.values()): raise SystemExit(1)
if __name__=='__main__': main()
