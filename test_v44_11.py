#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import itertools
import networkx as nx

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

C7_edges = [(0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,0)]
Classe1_edges = [(0, 1), (0, 4), (0, 5), (0, 6), (1, 4), (1, 6), (5, 6)]
Classe2_edges = [(0, 1), (0, 4), (0, 5), (0, 6), (1, 6), (4, 6), (5, 6)]

def tester_perturbation(nom, edges_init):
    print(f"\n>>> Test : {nom} <<<")
    print(f"Initial : beta1={beta1(nx.Graph(edges_init))}, Möbius={mobius_beta1(edges_init)}")
    for e in edges_init:
        edges_restants = [edge for edge in edges_init if edge != e]
        print(f" - Arête {e} retirée -> Möbius={mobius_beta1(edges_restants)}")

if __name__ == "__main__":
    tester_perturbation("Témoin C7", C7_edges)
    tester_perturbation("Classe 1", Classe1_edges)
    tester_perturbation("Classe 2", Classe2_edges)
