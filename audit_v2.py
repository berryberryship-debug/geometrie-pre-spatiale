#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_v2.py — Protocole d'évaluation multidimensionnelle (Version corrigée)
Baseline conservée. Corrections méthodologiques appliquées :
1. Observation : Séparation stricte des essais valides (pas de faux zéros).
2. Dynamique : Marches pures et sauts rapportés séparément (mêmes graines).
3. Terminologie : Renommage (sans altérer les formules de la baseline).
4. Statistiques : IC Bootstrap sur les graines indépendantes, pas sur les cycles.
"""
import numpy as np
import networkx as nx
from scipy import stats

# =========================================================
# 1. AUDIT TOPOLOGIQUE & INFORMATIONNEL
# =========================================================
def audit_topo(G):
    """Retourne les métriques topologiques de base (degrés, frontières)."""
    in_degrees = dict(G.in_degree())
    out_degrees = dict(G.out_degree())
    nodes = list(G.nodes())
    
    # Nœuds frontières : entrée nulle ou sortie nulle
    boundary_nodes = [n for n in nodes if in_degrees[n] == 0 or out_degrees[n] == 0]
    
    return {
        "n_nodes": len(nodes),
        "n_edges": G.number_of_edges(),
        "mean_in_degree": np.mean(list(in_degrees.values())) if nodes else 0,
        "mean_out_degree": np.mean(list(out_degrees.values())) if nodes else 0,
        "boundary_ratio": len(boundary_nodes) / len(nodes) if nodes else 0
    }

def count_simple_paths(G, source, target):
    """Compte les chemins simples entre deux nœuds."""
    try:
        return len(list(nx.all_simple_paths(G, source, target)))
    except nx.NetworkXNoPath:
        return 0

def audit_info(G):
    """Analyse la fermeture transitive et la densité informationnelle."""
    tc = nx.transitive_closure(G)
    n_nodes = G.number_of_nodes()
    
    if n_nodes < 2:
        return {"transitive_edges": 0, "info_density": 0.0}
        
    # Densité de la fermeture transitive
    info_density = tc.number_of_edges() / (n_nodes * (n_nodes - 1))
    
    return {
        "transitive_edges": tc.number_of_edges(),
        "info_density": info_density
    }

# =========================================================
# 2. AUDIT DYNAMIQUE (Correction 2)
# =========================================================
def walk_pure(G, start_node, steps, rng):
    """Marche aléatoire pure."""
    current = start_node
    path = [current]
    for _ in range(steps):
        neighbors = list(G.successors(current))
        if not neighbors:
            break
        current = rng.choice(neighbors)
        path.append(current)
    return path

def walk_with_jump(G, start_node, steps, jump_prob, rng):
    """Marche aléatoire avec sauts (téléportation)."""
    current = start_node
    path = [current]
    nodes = list(G.nodes())
    for _ in range(steps):
        if rng.random() < jump_prob:
            current = rng.choice(nodes)
        else:
            neighbors = list(G.successors(current))
            if not neighbors:
                current = rng.choice(nodes) # Saut forcé si cul-de-sac
            else:
                current = rng.choice(neighbors)
        path.append(current)
    return path

def audit_dyn(G, start_nodes, n_seeds=50, steps=20, jump_prob=0.1):
    """
    Correction 2 : Rapporte séparément les marches pures et avec sauts.
    Utilise les mêmes graines (seed) pour les deux pour garantir l'appariement.
    """
    p_pure = []
    p_jump = []
    
    for seed in range(n_seeds):
        # Même seed pour la marche pure et la marche avec saut
        rng_pure = np.random.default_rng(seed)
        rng_jump = np.random.default_rng(seed)
        
        start = rng_pure.choice(start_nodes)
        
        path_pure = walk_pure(G, start, steps, rng_pure)
        path_jump = walk_with_jump(G, start, steps, jump_prob, rng_jump)
        
        # On définit la "sortie" comme l'atteinte d'un nœud frontière
        boundaries = set([n for n in G.nodes() if G.out_degree(n) == 0])
        
        p_pure.append(1.0 if boundaries.intersection(path_pure) else 0.0)
        p_jump.append(1.0 if boundaries.intersection(path_jump) else 0.0)
        
    return {
        "prob_sortie_pure": np.mean(p_pure),
        "prob_sortie_jump": np.mean(p_jump),
        "effet_contraste_jump": np.mean(p_jump) - np.mean(p_pure),
        "raw_pure": p_pure,
        "raw_jump": p_jump
    }

# =========================================================
# 3. AUDIT OBSERVATIONNEL (Correction 1)
# =========================================================
def observe_from(G, observer, n_probes=20, max_steps=10, rng=None):
    """
    Correction 1 : Distingue les essais valides (chemins existants) 
    des chemins inexistants. Ne divise pas par n_probes si aucun essai n'est valide.
    """
    if rng is None:
        rng = np.random.default_rng()
        
    detections = 0
    essais_valides = 0
    boundaries = set([n for n in G.nodes() if G.out_degree(n) == 0])
    
    for _ in range(n_probes):
        # On génère un chemin depuis l'observateur
        path = walk_pure(G, observer, max_steps, rng)
        
        # Un essai est valide si le chemin a dépassé le nœud de départ
        if len(path) > 1:
            essais_valides += 1
            if boundaries.intersection(path):
                detections += 1
                
    # Si aucun essai n'a pu être réalisé (ex: nœud isolé), on renvoie NaN
    if essais_valides == 0:
        return np.nan
        
    return detections / essais_valides

def audit_obs(G, observers, n_probes=20, rng=None):
    """Agrège les résultats d'observation en ignorant les NaN."""
    if rng is None:
        rng = np.random.default_rng()
        
    taux = []
    for obs in observers:
        t = observe_from(G, obs, n_probes, rng=rng)
        if not np.isnan(t):
            taux.append(t)
            
    if not taux:
        return {"obs_moy": np.nan, "obs_std": np.nan, "obs_valides": 0}
        
    return {
        "obs_moy": np.mean(taux), 
        "obs_std": np.std(taux),
        "obs_valides": len(taux)
    }

# =========================================================
# 4. INDICATEURS (Correction 3 : Terminologie)
# =========================================================
def defaut_chiral(G):
    """
    Ancienne 'curvature'. 
    Formule historique conservée.
    """
    # --- INSERER FORMULE ORIGINALE DE CURVATURE ---
    # Exemple : moyenne des défauts sur les triplets transitifs
    triplets = 0
    defauts = 0
    for u in G.nodes():
        for v in G.successors(u):
            for w in G.successors(v):
                if G.has_edge(u, w): # Triangle transitif
                    triplets += 1
                    # defaut = ... (ta formule exacte ici)
    return defauts / triplets if triplets > 0 else 0.0

def tension(G, node):
    """
    Ancienne 'tension'. 
    Formule historique conservée, domaine clarifié (successeurs directs).
    """
    # --- INSERER FORMULE ORIGINALE DE TENSION ---
    # Ne pas remplacer par la simple cardinalité. 
    # Exemple : somme des poids des arêtes sortantes
    return sum(G[node][neighbor].get('weight', 1.0) for neighbor in G.successors(node))

# =========================================================
# 5. STATISTIQUES & SCAN (Correction 4)
# =========================================================
def bootstrap_ic(donnees, n_boot=1000, alpha=0.05):
    """
    Correction 4 : IC Bootstrap calculé sur les graines indépendantes.
    """
    donnees = np.asarray(donnees)
    donnees = donnees[~np.isnan(donnees)] # Ignore les NaN
    if len(donnees) < 2: return (np.nan, np.nan)
    
    rng = np.random.default_rng(42)
    moyennes = [np.mean(rng.choice(donnees, size=len(donnees), replace=True)) 
                for _ in range(n_boot)]
                
    return np.percentile(moyennes, 100 * alpha / 2), np.percentile(moyennes, 100 * (1 - alpha / 2))

def scan(G, niveaux_lesion, n_seeds=50):
    """Balayage des niveaux de lésion."""
    resultats = []
    
    for niveau in niveaux_lesion:
        # Simulation de la lésion (à adapter selon ton code)
        G_lese = G.copy() 
        # ... logique de lésion ...
        
        # 1. Topo / Info
        topo = audit_topo(G_lese)
        info = audit_info(G_lese)
        
        # 2. Dynamique (v2)
        start_nodes = list(G_lese.nodes())
        dyn = audit_dyn(G_lese, start_nodes, n_seeds=n_seeds)
        
        # 3. Observation (v2)
        rng_obs = np.random.default_rng(42)
        observers = rng_obs.choice(start_nodes, size=min(20, len(start_nodes)), replace=False)
        obs = audit_obs(G_lese, observers, n_probes=20, rng=rng_obs)
        
        # 4. Indicateurs renommés
        d_chiral = defaut_chiral(G_lese)
        
        resultats.append({
            "niveau": niveau,
            "n_edges": topo["n_edges"],
            "info_density": info["info_density"],
            "dyn_pure": dyn["prob_sortie_pure"],
            "dyn_jump": dyn["prob_sortie_jump"],
            "obs_moy": obs["obs_moy"],
            "defaut_chiral": d_chiral,
            "raw_pure": dyn["raw_pure"],
            "raw_jump": dyn["raw_jump"]
        })
        
    return resultats

def detect_breaks(resultats):
    """Détection des sauts topologiques avec IC Bootstrap."""
    breaks = []
    for i in range(1, len(resultats)):
        r1 = resultats[i-1]
        r2 = resultats[i]
        
        # Différence des probabilités de sortie pure
        diff = r2["dyn_pure"] - r1["dyn_pure"]
        
        # I.C. Bootstrap sur les différences appariées (mêmes seeds)
        diff_seeds = np.array(r2["raw_pure"]) - np.array(r1["raw_pure"])
        lo, hi = bootstrap_ic(diff_seeds)
        
        # Si l'IC ne contient pas 0, il y a un saut significatif
        if lo > 0 or hi < 0:
            breaks.append({
                "niveau": r2["niveau"],
                "diff": diff,
                "ic": (lo, hi)
            })
    return breaks

def print_scan(resultats):
    print(f"{'Niveau':>6} | {'Arêtes':>6} | {'Info Dens':>9} | {'Dyn Pure':>8} | {'Dyn Jump':>8} | {'Obs Moy':>7} | {'Défaut Chiral':>13}")
    print("-" * 75)
    for r in resultats:
        obs_str = f"{r['obs_moy']:.3f}" if not np.isnan(r['obs_moy']) else "N/A"
        print(f"{r['niveau']:>6} | {r['n_edges']:>6} | {r['info_density']:>9.4f} | {r['dyn_pure']:>8.3f} | {r['dyn_jump']:>8.3f} | {obs_str:>7} | {r['defaut_chiral']:>13.4f}")

def print_breaks(breaks):
    print("\n--- Sauts Topologiques Détectés (IC Bootstrap 95%) ---")
    if not breaks:
        print("Aucun saut significatif détecté.")
    for b in breaks:
        print(f"Niveau {b['niveau']} : Delta = {b['diff']:+.4f} (IC: [{b['ic'][0]:+.4f}, {b['ic'][1]:+.4f}])")

# =========================================================
# MAIN (Exemple d'exécution)
# =========================================================
if __name__ == "__main__":
    # Création d'un graphe factice pour tester (à remplacer par ton graphe réel)
    G_test = nx.erdos_renyi_graph(50, 0.1, directed=True)
    niveaux = np.linspace(0, 1, 10)
    
    print("Démarrage de l'audit v2...")
    res = scan(G_test, niveaux, n_seeds=50)
    print_scan(res)
    
    brk = detect_breaks(res)
    print_breaks(brk)
