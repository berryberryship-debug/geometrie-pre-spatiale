# V51.5 — Preuve Analytique du Modèle MCC (Théorèmes A et B)

Ce document formalise la démonstration de convergence globale du Modèle de Configuration Circonstancielle (MCC) pour des paramètres positifs sous la condition \(P_0 < \lambda_r + r\).

## Statut des Résultats

| Proposition | Statut |
| :--- | :--- |
| **Théorème A** : Convergence globale du système réduit (2D) | **DÉMONTRÉ** (Calcul symbolique et topologique) |
| **Théorème B** : Convergence globale du système complet (3D) | **ESQUISSÉ** (Systèmes asymptotiquement autonomes) |
| Comportement si \(P_0 \ge \lambda_r + r\) | **NON DÉMONTRÉ** (Instabilité ou cycles possibles) |

## 1. Démonstration du Théorème A (Système 2D)

**Hypothèses :** \(M = M^* = 4.0\), paramètres strictement positifs, \(P_0 = 0.15 < \lambda_r + r = 0.30\).

1. **Invariance du domaine** : Les dérivées aux frontières (\(R=0\), \(C=0\), \(C=1\)) pointent vers l'intérieur. Le domaine physique est préservé.
2. **Bornitude et exclusion de la frontière \(C=0\)** : \(\dot{R} \le P_0 - \lambda_r R\) borne \(R\). De plus, \(\dot{C} \ge r - (r+qM^*)C\) implique que \(\liminf C(t) \ge \frac{r}{r+qM^*} = 0.0476 > 0\). La trajectoire ne s'accumule pas sur \(C=0\).
3. **Raccord \(R=M^*\)** : \(\dot{R}|_{R=M^*} \le P_0 - \lambda_r M^* = -0.65 < 0\). Le champ est rentrant, aucune trajectoire ne s'accumule sur le raccord.
4. **Absence de cycles limites** : La divergence du champ est strictement négative dans les deux régimes (stress et sans stress). Par le critère de Bendixson-Dulac, il n'y a pas d'orbites périodiques.
5. **Unicité de l'équilibre** : Le polynôme d'équilibre est \(20s^3 - 56s^2 - 92s - 13 = 0\). Par la règle de Descartes (1 changement de signe), il admet exactement une racine positive dans \((0, 4)\).
6. **Conclusion** : Par le théorème de Poincaré-Bendixson, toute trajectoire du système réduit converge vers l'unique équilibre \((R^*, C^*)\) localement stable.
**=> Théorème A démontré.**

## 2. Extension au Théorème B (Système 3D)

**Hypothèse :** \(M(t)\) n'est plus fixe, mais \(\dot{M} = f_0 - \lambda_c M\).

1. **Stabilité locale** : La matrice Jacobienne 3D est triangulaire par blocs. Ses valeurs propres sont \(\{-\lambda_c, \lambda_1, \lambda_2\}\), toutes strictement négatives. L'équilibre 3D est localement stable.
2. **Asymptoticité autonome** : \(M(t) = M^* + (M_0 - M^*)e^{-\lambda_c t}\) converge exponentiellement vers \(M^*\).
3. **Convergence globale** : Le champ de vecteurs 3D converge uniformément sur tout compact vers le champ 2D. Le théorème des systèmes asymptotiquement autonomes permet de transférer la convergence globale du système 2D (Théorème A) au système 3D.
**=> Théorème B esquissé (la preuve complète nécessiterait une publication formelle de l'argument d'asymptoticité autonome).**

## 3. Limites de la démonstration

- **Seuil de stabilité** : L'absence de cycles n'est garantie que si \(P_0 < \lambda_r + r\). Au-delà, le système peut développer des oscillations ou des comportements chaotiques.
- **Robustesse paramétrique** : La marge de stabilité face à des variations des paramètres (ex: \(\lambda_c, q\)) n'est pas quantifiée.
