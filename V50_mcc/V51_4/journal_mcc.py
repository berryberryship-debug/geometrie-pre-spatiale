#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V51.4 — MODULE JOURNAL FORENSIQUE (journal_mcc.py)
"""
import os
import json
import hashlib
from typing import Dict, Any, Optional

class JournalMCC:
    def __init__(self, chemin_fichier: str, metadata: Optional[Dict[str, Any]] = None, autoriser_ecrasement: bool = False):
        self.chemin = os.path.abspath(chemin_fichier)
        self.compteur_etapes = 0
        self.ferme = False
        self.sha256 = hashlib.sha256()

        if os.path.exists(self.chemin) and not autoriser_ecrasement:
            raise FileExistsError(f"Protection anti-écrasement activée : '{self.chemin}' existe déjà.")

        os.makedirs(os.path.dirname(self.chemin), exist_ok=True)
        mode = 'w' if autoriser_ecrasement else 'x'
        with open(self.chemin, mode, encoding='utf-8') as f:
            meta = metadata.copy() if metadata else {}
            ligne_meta = json.dumps({'__type__': 'METADATA', **meta}, ensure_ascii=False) + '\n'
            f.write(ligne_meta)
            self.sha256.update(ligne_meta.encode('utf-8'))

    def enregistrer(self, step: int, donnees: Dict[str, Any]) -> None:
        if self.ferme:
            raise RuntimeError(f"Tentative d'enregistrement sur un journal scellé : {self.chemin}")
        entree = {'step': int(step), **donnees}
        ligne = json.dumps(entree, ensure_ascii=False) + '\n'
        with open(self.chemin, 'a', encoding='utf-8') as f:
            f.write(ligne)
        self.sha256.update(ligne.encode('utf-8'))
        self.compteur_etapes += 1

    def clore(self) -> Dict[str, Any]:
        if self.ferme:
            return {'chemin': self.chemin, 'deja_ferme': True}
        digest_pre_seal = self.sha256.hexdigest()
        ligne_seal = json.dumps({
            '__type__': 'SEAL',
            'total_etapes': self.compteur_etapes,
            'sha256_pre_seal': digest_pre_seal
        }, ensure_ascii=False) + '\n'
        with open(self.chemin, 'a', encoding='utf-8') as f:
            f.write(ligne_seal)
        self.sha256.update(ligne_seal.encode('utf-8'))
        self.ferme = True
        return {
            'chemin': self.chemin,
            'sha256_global': self.sha256.hexdigest(),
            'sha256_pre_seal': digest_pre_seal,
            'total_etapes': self.compteur_etapes
        }
