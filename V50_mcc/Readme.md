V50 — Architecture MCC (6 fichiers)
v50_noyau.py — noyau dynamique, héritage V49.6.1-H.
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
# V51.4 — Audit Cryptographique

**Note importante :** Ce dossier documente la chaîne de preuve **cryptographique** (intégrité, authenticité, antériorité). La chaîne de preuve **mathématique** (Théorèmes A et B) est documentée séparément dans le fichier `../../V51_PREUVE_ANALYTIQUE.md`.

## 1. Architecture de confiance

1. **Intégrité interne** : les journaux MCC (`journal_sans_memoire.jsonl` et `journal_avec_memoire.jsonl`) contiennent chacun 20 lignes, chaînées par hachage SHA-256.
2. **Authenticité** : le manifeste global (`manifest_global.json`) est signé numériquement avec Ed25519. Sa vérification nécessite la clé publique de référence.
3. **Anti-substitution** : l'empreinte SHA-256 de la clé publique est consignée ci-dessous. **Sa publication par un canal indépendant (ex: profil, réseau social, autre dépôt) reste nécessaire pour établir une confiance absolue.**
4. **Antériorité** : le fichier `ANCHOR.sha256` (qui contient le hash du manifeste) a été soumis à OpenTimestamps. La confirmation dans la blockchain Bitcoin est en attente.

## 2. Références cryptographiques (Chaîne de vérification)

- **Empreinte SHA-256 de la clé publique** : `38e5b10ca0eb5eb20c25c2151010558fecaf50cb01da6f3f8e4c258ad0a74816`
- **Empreinte SHA-256 de l'archive finale complète** : `04b78d6cdfeb8e65210eadf8b39366a2487d6b79558dcc1a327c22a8aee9cb1f`
- **Empreinte du sceau `ANCHOR.sha256`** (hash du manifeste) : `ee44fe1c762a01ea04564cfff2d35e5e9114aaab15c13b02b9deb0758883fb9e`

## 3. Artefacts inclus dans l'archive

L'archive `V51_4_FINAL_ARCHIVE.tar.gz` contient :
- Les deux journaux MCC originaux (20 lignes chacun).
- Le manifeste (`manifest_global.json`) et sa signature (`manifest_global.sig`).
- La clé publique (`public_key.pem`).
- Le sceau d'ancrage (`ANCHOR.sha256`).
- La preuve OpenTimestamps (`ANCHOR.sha256.ots` - en attente de confirmation).

*(Note : La clé privée `private_key.pem` n'est jamais incluse pour des raisons évidentes de sécurité).*

## 4. Limites documentées

- La sécurité cryptographique protège l'intégrité et l'authenticité des artefacts ; elle ne démontre pas les propriétés mathématiques du modèle.
- Le Théorème A est déclaré démontré ; le Théorème B demeure esquissé.
- L'ancrage OpenTimestamps a été soumis, mais sa confirmation Bitcoin reste à obtenir.
- La date inscrite dans le manifeste ne constitue pas, à elle seule, un horodatage indépendant (d'où l'importance de l'ancrage).

## 5. Procédure de vérification indépendante

Un auditeur souhaitant vérifier ces artefacts sans faire confiance aux logs de création doit :
1. Vérifier que l'empreinte de sa clé publique `public_key.pem` correspond à celle publiée hors-bande (indiquée ci-dessus).
2. Vérifier la signature du manifeste avec OpenSSL (`openssl pkeyutl -verify ...`).
3. Recalculer les hashes des journaux et les comparer aux valeurs du manifeste.
4. Vérifier la preuve OpenTimestamps une fois le bloc Bitcoin miné (`ots verify ...`).
