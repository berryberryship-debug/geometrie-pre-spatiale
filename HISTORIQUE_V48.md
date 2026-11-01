# Généalogie du Modèle : Archive V48.19 & V48.20

Ce document sert de point d'ancrage historique. Il documente l'état de la recherche, les concepts introduits et les limites méthodologiques des versions `test_v48_19.py` (Signature Relationnelle) et `test_v48_20_miroir.py` (Protocole Miroir).

## 1. V48.19 — La Signature Relationnelle

**Objectif initial :** Caractériser la structure des échanges (flux dirigés) qui persiste ou se transforme sous perturbation.

### Apports conceptuels majeurs
*   **L'Asymétrie Relationnelle Dirigée (\(\Omega\))** : Introduction d'un indice normalisé pour mesurer la direction dominante des flux entre compartiments.
*   **La distinction \(\Omega_G\) (Cumul) vs \(\Omega_T\) (Moyenne)** : Séparation entre la prédominance directionnelle pondérée par les volumes et la moyenne temporelle des asymétries.

### Limites méthodologiques
*   **Absence d'appariement strict** : La perturbation et le bruit n'étaient pas strictement contrôlés pour isoler l'effet de la topologie.
*   **Métrique dépendante de la trajectoire** : \(\Omega\) caractérise une signature directionnelle, pas encore un invariant structurel.

---

## 2. V48.20 — Le Protocole Miroir

**Objectif initial :** Séparer l'effet de la structure de couplage de l'effet de la direction de la perturbation.

### 1. Apports conceptuels majeurs

*   **Le Protocole Miroir (P1 vs P2)** : Utilisation d'une même séquence stochastique (`p_base`) appliquée alternativement au compartiment 1 et au compartiment 2. Cela permet de contrôler l'identité de la perturbation pour comparer les réponses.
*   **La Persistance** : Introduction d'une mesure de la fréquence de concordance entre la direction instantanée et la direction globale.
*   **Propriété analytique démontrée (Spectre vs Configuration)** : Les matrices SYM et ASYM_CONS partagent le même spectre (\(\lambda_1=1, \lambda_2=0.6\)) et la même trace. Cette identité spectrale est démontrée analytiquement, elle n'est pas issue d'une découverte numérique. Cependant, leurs espaces propres diffèrent :
    *   \(W_{\mathrm{SYM}}\) : \(v_1=(1,1)\), \(v_{0.6}=(1,-1)\)
    *   \(W_{\mathrm{ASYM}}\) : \(v_1=(1,3)\), \(v_{0.6}=(1,-1)\)
    *   *Conclusion mathématique* : La conservation du spectre n'implique pas la conservation des directions propres.

### 2. Limites méthodologiques identifiées

*   **Asymétrie de l'état initial** : `etat_initial = (1.0, 0.6)` n'est pas invariant sous permutation. Le protocole miroir P1/P2 compare deux systèmes avec des réserves initiales différentes.
*   **Absence de bruit interne** : La dynamique est déterministe (hors perturbation).
*   **Absence d'intervalles de confiance** : Les moyennes sont calculées sans évaluation de la robustesse statistique.

---

## 3. Transition vers les versions ultérieures

Cette version a été conservée comme archive. L'évolution générale du dépôt (sans prétendre à une exactitude chronologique stricte pour chaque sous-version) a intégré :
*   L'ajout de protocoles stochastiques (bruit interne multiplicatif) et de phases de préchauffage.
*   La paramétrisation continue de l'asymétrie \(W(\alpha)\).
*   L'équivalence stricte des doses et l'introduction des intervalles de confiance (ex: Wilson).
*   L'instrumentation des invariants spectraux (trace, déterminant) et la décomposition des flux bruts (\(J_{12}\) et \(J_{21}\)).

---

## 4. Principe de recherche issu des versions V48

Les versions V48 ont permis de formuler rigoureusement la possibilité suivante :

$$
\boxed{
\Delta X \neq 0 \;\centernot\Rightarrow\; \Delta R \neq 0
}
$$

Où :
*   \(X\) désigne l'état du système.
*   \(R\) désigne une signature relationnelle définie par des observables.
*   \(\Delta X\) représente une transformation des états.
*   \(\Delta R\) représente une transformation de la signature.

Cette formulation exprime une **possibilité** : l'état peut changer sans que la signature relationnelle change nécessairement. Elle ne suppose pas que cette conservation a déjà été démontrée, mais elle ouvre la voie à l'étude des trois niveaux de continuité :
1.  **Continuité d'état** : Les variables internes demeurent relativement stables.
2.  **Continuité fonctionnelle** : Le système conserve sa viabilité.
3.  **Continuité relationnelle** : Certaines propriétés de l'organisation demeurent reconnaissables malgré les transformations des états.
