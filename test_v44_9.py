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

def main():
    print("V44.9 — ANATOMIE DES FAUX POSITIFS")
    N_NODES, N_GRAINES, P, K = 8, 5, 0.5, 7
    faux_positifs = []
    
    for seed in range(N_GRAINES):
        G = nx.gnp_random_graph(N_NODES, P, seed=seed)
        for subset in itertools.combinations(list(G.edges()), K):
            H = nx.Graph()
            H.add_edges_from(subset)
            if beta1(H) == 0: continue
            if mobius_beta1(subset) == 1 and max(dict(H.degree()).values()) > 2:
                deg = tuple(sorted([d for n, d in H.degree()], reverse=True))
                faux_positifs.append((H.number_of_nodes(), H.number_of_edges(), deg))

    compteur = Counter(faux_positifs)
    for sig, count in compteur.most_common():
        print(f"[{count} fois] V={sig[0]}, E={sig[1]}, Degrés={sig[2]}")

if __name__ == "__main__":
    main()
