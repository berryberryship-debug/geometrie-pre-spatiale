# VALIDATION STRICTE (Bloquante)
for j_path in journaux_attendus:
    if not os.path.exists(j_path):
        raise RuntimeError(f"CRITIQUE : Journal manquant ! {j_path}")
    
    v = verifier_journal(j_path)
    if not v['valide']:
        raise RuntimeError(f"CRITIQUE : Journal corrompu ! {j_path}")
    
    # Vérification du nombre exact d'étapes
    etapes_attendues = self.cfg_base.n_stress + self.cfg_base.n_recup
    
    if v['nombre'] != etapes_attendues:
        raise RuntimeError(
            f"CRITIQUE : Nombre d'enregistrements incorrect ! "
            f"{j_path} (Trouvé : {v['nombre']}, attendu : {etapes_attendues})"
        )
        
    if v['derniere_etape'] != etapes_attendues - 1:
        raise RuntimeError(
            f"CRITIQUE : Dernière étape incorrecte ! "
            f"{j_path} (Trouvé : {v['derniere_etape']}, attendu : {etapes_attendues - 1})"
        )
        
return historique
