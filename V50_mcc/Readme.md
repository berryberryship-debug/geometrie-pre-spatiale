V50 — Architecture MCC (6 fichiers)
v50_1_noyau.py — noyau dynamique, héritage V49.6.1-H.
v50_2_mcc.py — collecteur circonstanciel et journal SHA-256.
v50_2_1_adaptateur.py — calibration puis journalisation d'un run nominal.
v50_3_memoire.py — persistance et activation temporelle des traces.
v50_4_couplage.py — propositions de couplage hypothétiques, inactives par défaut.
v50_5_validation.py — tests de non-interférence, journal, mémoire et couplage.
Dépendance : NumPy. Place les six fichiers dans le même dossier.
python -m pip install numpy
python v50_5_validation.py
python v50_2_1_adaptateur.py --mode chronique --alpha 0 --gain 0.8 --seed 42
Limites méthodologiques
Le balayage de calibration ne garantit pas la détection de racines tangentes ni de croisements multiples dans une même cellule.
Le raffinement vérifie maintenant le signe aux deux bornes ; il ne rend pas exhaustive la recherche sur une grille finie.
La convention choisit la plus petite amplitude parmi les solutions détectées.
L'activation de V50.3 est une fonction mathématique de persistance, pas une mesure psychologique.
V50.4 encode des hypothèses causales paramétrées ; aucun effet causal n'est établi par le code.
Le chaînage SHA-256 détecte les altérations de la chaîne présente, mais ne protège pas contre la réécriture complète du fichier et de ses empreintes. Conserver une empreinte de référence hors du journal.
Les tests doivent être exécutés localement ; aucun PASS n'est présumé.
