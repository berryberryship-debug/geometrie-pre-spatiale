#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V51.4 — VÉRIFICATEUR STRICT FORENSIQUE (verifier_journal.py)
"""
import os
import json
import math
import hashlib
from typing import Dict, Any, List, Optional, Union

def verifier_valeurs_numeriques(obj: Any, chemin_champ: str = "") -> Union[None, str]:
    if isinstance(obj, float):
        if math.isnan(obj): return f"NaN détecté dans '{chemin_champ}'"
        if math.isinf(obj): return f"Inf détecté dans '{chemin_champ}'"
    elif isinstance(obj, dict):
        for k, v in obj.items():
            err = verifier_valeurs_numeriques(v, f"{chemin_champ}.{k}" if chemin_champ else str(k))
            if err: return err
    elif isinstance(obj, (list, tuple)):
        for idx, item in enumerate(obj):
            err = verifier_valeurs_numeriques(item, f"{chemin_champ}[{idx}]")
            if err: return err
    return None

def verifier_journal(chemin_journal: str, etapes_attendues: int = 24) -> Dict[str, Any]:
    if not os.path.exists(chemin_journal):
        return {'valide': False, 'erreur': f"Fichier inexistant : {chemin_journal}"}

    enregistrements: List[Dict[str, Any]] = []
    metadata: Optional[Dict[str, Any]] = None
    seal: Optional[Dict[str, Any]] = None
    sha256_calc = hashlib.sha256()

    with open(chemin_journal, 'r', encoding='utf-8') as f:
        lignes = f.readlines()

    if not lignes:
        return {'valide': False, 'erreur': "Journal vide (0 octet)."}

    for num_ligne, ligne_brute in enumerate(lignes, start=1):
        if not ligne_brute.endswith('\n'):
            return {'valide': False, 'erreur': f"Ligne {num_ligne} incomplète (pas de '\\n')."}
        ligne = ligne_brute.rstrip('\r\n')
        if len(ligne.strip()) == 0:
            return {'valide': False, 'erreur': f"Ligne vide interdite (ligne {num_ligne})."}

        try:
            element = json.loads(ligne)
        except json.JSONDecodeError as err:
            return {'valide': False, 'erreur': f"Ligne {num_ligne} : JSON invalide ({err})."}

        if not isinstance(element, dict):
            return {'valide': False, 'erreur': f"Ligne {num_ligne} : attendu 'dict', reçu '{type(element).__name__}'."}

        err_num = verifier_valeurs_numeriques(element)
        if err_num:
            return {'valide': False, 'erreur': f"Ligne {num_ligne} : anomalie numérique -> {err_num}."}

        type_bloc = element.get('__type__')
        if num_ligne == 1:
            if type_bloc != 'METADATA':
                return {'valide': False, 'erreur': f"Ligne 1 : attendu '__type__': 'METADATA', reçu '{type_bloc}'."}
            metadata = element
            sha256_calc.update(ligne_brute.encode('utf-8'))
            continue

        if num_ligne == len(lignes):
            if type_bloc != 'SEAL':
                return {'valide': False, 'erreur': f"Dernière ligne : attendu '__type__': 'SEAL', reçu '{type_bloc}'."}
            seal = element
            break

        if type_bloc in ('METADATA', 'SEAL'):
            return {'valide': False, 'erreur': f"Bloc réservé illégal '{type_bloc}' à la ligne {num_ligne}."}

        if 'step' not in element:
            return {'valide': False, 'erreur': f"Ligne {num_ligne} : champ 'step' manquant."}

        enregistrements.append(element)
        sha256_calc.update(ligne_brute.encode('utf-8'))

    digest_pre_seal = sha256_calc.hexdigest()
    if seal.get('sha256_pre_seal') != digest_pre_seal:
        return {
            'valide': False,
            'erreur': f"Corruption d'intégrité SHA-256 : attendu {seal.get('sha256_pre_seal')}, calculé {digest_pre_seal}."
        }

    n = len(enregistrements)
    if n != etapes_attendues or seal.get('total_etapes') != n:
        return {'valide': False, 'nombre': n, 'erreur': f"Volumétrie incorrecte : {n} étapes (attendu {etapes_attendues})."}

    for i, rec in enumerate(enregistrements):
        if rec['step'] != i:
            return {'valide': False, 'erreur': f"Rupture de séquence à l'index {i} (step={rec['step']})."}

    return {
        'valide': True,
        'nombre': n,
        'premiere_etape': enregistrements[0]['step'],
        'derniere_etape': enregistrements[-1]['step'],
        'metadata': metadata,
        'seal': seal,
        'sha256_valide': True
    }
