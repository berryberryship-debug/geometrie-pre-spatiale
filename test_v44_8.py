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
    n = len(edges_subset)
    for r in range(n + 1):
        sign = (-1) ** (n - r)
        for subset in itertools.combinations(edges_subset, r):
            H = nx.Graph()
            H.add_edges_from(subset)
            total += sign * beta1(H)
    return total

def est_cycle_simple(H):
    if H.number_of_nodes() != H.number_of_edges(): return False
    if H.number_of_nodes() == 0: return False
    if nx.number_connected_components(H) != 1: return False
    return all(degree == 2 for _, degree in H.degree())

def main():
    print("V44.8 — COMPARAISON BETA1 / MOBIUS / C7")
    N_NODES, N_GRAINES, P, K = 8, 5, 0.5, 7
    totals = Counter()
    
    for seed in range(N_GRAINES):
        G = nx.gnp_random_graph(N_NODES, P, seed=seed)
        for subset in itertools.combinations(list(G.edges()), K):
            H = nx.Graph()
            H.add_edges_from(subset)
            b = beta1(H)
            mu = mobius_beta1(subset)
            cycle = est_cycle_simple(H)
            
            if b == 1: totals['beta1_1'] += 1
            if mu == 1: totals['mobius_1'] += 1
            if cycle: totals['cycles'] += 1

    print(f"Cycles simples C7 : {totals['cycles']}")
    print(f"beta1=1 : {totals['beta1_1']}")
    print(f"Mobius=1 : {totals['mobius_1']}")

if __name__ == "__main__":
    main()
