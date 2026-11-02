#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import itertools
import networkx as nx
from collections import Counter

def beta1(H):
    if H.number_of_nodes() == 0: return 0
    return H.number_of_edges() - H.number_of_nodes() + nx.number_connected_components(H)

def mobius_beta1(edges_subset):
    total = 0
    for r in range(len(edges_subset) + 1):
        sign = (-1) ** (len(edges_subset) - r)
        for subset in itertools.combinations(edges_subset, r):
            H = nx.Graph()
            H.add_edges_from(subset)
            total += sign * beta1(H)
    return total

def main():
    print("V44.10 — ISOMORPHISME DES FAUX POSITIFS")
    N_NODES, N_GRAINES, P, K = 8, 5, 0.5, 7
    faux_positifs = []
    
    for seed in range(N_GRAINES):
        G = nx.gnp_random_graph(N_NODES, P, seed=seed)
        for subset in itertools.combinations(list(G.edges()), K):
            H = nx.Graph()
            H.add_edges_from(subset)
            if beta1(H) > 0 and mobius_beta1(subset) == 1 and max(dict(H.degree()).values()) > 2:
                faux_positifs.append(H)
                
    classes = []
    for H in faux_positifs:
        trouve = False
        for cls in classes:
            if nx.is_isomorphic(H, cls['graphe']):
                cls['count'] += 1
                trouve = True
                break
        if not trouve:
            classes.append({'graphe': H, 'count': 1})
            
    for i, cls in enumerate(classes):
        H = cls['graphe']
        deg = sorted([d for n, d in H.degree()], reverse=True)
        print(f"Classe {i+1} ({cls['count']} occurrences) : Degrés={tuple(deg)}, Arêtes={list(H.edges())}")

if __name__ == "__main__":
    main()
