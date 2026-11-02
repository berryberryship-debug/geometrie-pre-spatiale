#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import networkx as nx
import itertools
import time

def est_cycle_simple_strict(H):
    V = H.number_of_nodes()
    E = H.number_of_edges()
    if V == 0 or V != E: return False
    if nx.number_connected_components(H) != 1: return False
    for node, degree in H.degree():
        if degree != 2: return False
    return True

def analyser_ordre_k(edges, k):
    vrais_cycles = 0
    faux_positifs = 0
    for subset in itertools.combinations(edges, k):
        H = nx.Graph()
        H.add_edges_from(subset)
        V = H.number_of_nodes()
        C = nx.number_connected_components(H) 
        beta_1 = k - V + C
        if beta_1 == 1:
            if est_cycle_simple_strict(H): vrais_cycles += 1
            else: faux_positifs += 1
    return vrais_cycles, faux_positifs

def main():
    print("V44.7 — AUDIT DE L'ORDRE 7 (BETA1)")
    N_NODES = 8
    N_GRAINES = 5
    mu = 0.5
    total_vrais, total_faux = 0, 0
    for seed in range(N_GRAINES):
        G = nx.gnp_random_graph(N_NODES, mu, seed=seed)
        v7, f7 = analyser_ordre_k(list(G.edges()), 7)
        total_vrais += v7
        total_faux += f7
    print(f"Vrais cycles C7 : {total_vrais}")
    print(f"Faux positifs (beta1=1) : {total_faux}")

if __name__ == "__main__":
    main()
