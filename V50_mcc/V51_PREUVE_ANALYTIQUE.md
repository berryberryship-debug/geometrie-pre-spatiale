# V51.5 — Preuve Analytique du Modèle MCC (Édition de Référence)

Ce document formalise la démonstration de convergence globale du Modèle de Configuration Circonstancielle (MCC) pour un jeu de paramètres spécifique, et définit les conditions de validité de cette démonstration.

## 1. Statut Scientifique et Conditions de Validité

**Jeu de paramètres de la démonstration :**
- \(M^* = 4.0\) (équilibre de charge)
- \(P_0 = 0.15\) (protection demandée)
- \(\lambda_r = 0.2\) (dissipation de la réserve)
- \(r = 0.1\) (récupération du contexte)
- \(q = 0.5\) (sensibilité du contexte)
- \(\lambda_c = 0.05\) (dissipation de la charge)

**Condition générale de dissipation :** \(P_0 < \lambda_r + r\) (ici, \(0.15 < 0.30\)).

### Tableau des Statuts

| Proposition | Statut |
| :--- | :--- |
| Invariance du système réduit | **DÉMONTRÉE** |
| Bornitude du système réduit | **DÉMONTRÉE** |
| Absence de cycles | **DÉMONTRÉE pour les paramètres étudiés** |
| Unicité de l'équilibre | **DÉMONTRÉE pour les paramètres étudiés** |
| Convergence globale 2D | **DÉMONTRÉE pour les paramètres étudiés** |
| Stabilité locale 3D | **DÉMONTRÉE** |
| Convergence globale 3D | **ESQUISSÉE** |
| Généralisation à tous les paramètres positifs | **NON DÉMONTRÉE** |
| Comportement au-delà du seuil | **NON DÉTERMINÉ** |

## 2. Théorème A — Système Réduit (2D)

**Statut : DÉMONTRÉ pour le jeu de paramètres spécifié.**

1. **Invariance du domaine** : Les dérivées aux frontières (\(R=0\), \(C=0\), \(C=1\)) pointent vers l'intérieur.
2. **Bornitude et exclusion de \(C=0\)** : \(\dot{R} \le P_0 - \lambda_r R\) borne \(R\). De plus, \(\dot{C} \ge r - (r+qM^*)C\), ce qui implique \(\liminf_{t\to\infty} C(t) \ge \frac{r}{r+qM^*} = \frac{1}{21} > 0\).
3. **Raccord \(R=M^*\)** : \(\dot{R}|_{R=M^*} \le P_0 - \lambda_r M^* = -0.65 < 0\). Le champ est rentrant pour tout \(C\).
4. **Absence de cycles** : Dans le régime de stress (\(R < M^*\)), la divergence est majorée par \(-0.15\), donc strictement négative. Dans le régime sans stress (\(R > M^*\)), elle vaut exactement \(-0.30\). Le raccord est traversé dans un seul sens. Le critère de Bendixson exclut ainsi les orbites périodiques.
5. **Unicité de l'équilibre** : Le polynôme d'équilibre est \(20s^3 - 56s^2 - 92s - 13 = 0\). Par la règle de Descartes (1 changement de signe) et l'évaluation \(P(0)=-13\), \(P(4)=3\), il admet exactement une racine positive dans \((0,4)\). L'équilibre sans stress (\(R=0.75, C=1\)) est inadmissible.
6. **Conclusion** : Par le théorème de Poincaré-Bendixson, toute trajectoire du système réduit converge vers l'unique équilibre localement stable \((R^*, C^*)\).

## 3. Théorème B — Extension au Système Complet (3D)

**Statut : ESQUISSÉ (Preuve complète requise).**

1. **Stabilité locale** : La matrice jacobienne 3D est triangulaire par blocs. Ses valeurs propres sont \(\{-\lambda_c, \lambda_1, \lambda_2\}\), toutes strictement négatives.
2. **Asymptoticité autonome** : \(M(t) = M^* + (M_0 - M^*)e^{-\lambda_c t}\) converge exponentiellement vers \(M^*\).
3. **Argument manquant** : Pour conclure à la convergence globale, il faut démontrer la précompacité des trajectoires complètes et que le champ non autonome converge uniformément sur tout compact vers le champ 2D, puis appliquer le théorème des systèmes asymptotiquement autonomes. Cet argument reste à écrire formellement.

## 4. Limites de la démonstration

- **Généralisation paramétrique** : L'unicité de la racine admissible a été démontrée grâce aux coefficients numériques spécifiques du polynôme. Elle n'est pas garantie pour toute la famille paramétrique \(P_0 < \lambda_r + r\).
- **Comportement au-delà du seuil** : Lorsque \(P_0 \ge \lambda_r + r\), le critère de divergence négative utilisé dans cette démonstration ne permet plus de conclure. L'existence d'oscillations, d'autres attracteurs ou d'une instabilité reste à étudier. Aucun comportement chaotique n'est établi.

## 5. Architecture Documentaire et Statut de Référence

**Organisation du dépôt :**
```text
V50_mcc/
│
├── Readme.md
├── V51_PREUVE_ANALYTIQUE.md
│
├── v50_2_1_adaptateur.py
├── v50_2_mcc.py
├── v50_couplage.py
├── v50_memoire.py
├── v50_noyau.py
├── v50_orchestrateur.py
└── v50_validation.py
