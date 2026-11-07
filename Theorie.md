# Formalisation Théorique : Invariants et Viabilité

Ce document synthétise les propriétés mathématiques et les concepts établis par les instruments de mesure développés dans les versions V48 et V49. Il ne décrit pas le code, mais les résultats qu'il permet d'établir.

## 1. Le Principe de Conservation Relationnelle

L'étude de la matrice de couplage \(W(\alpha)\) a permis d'isoler deux propriétés mathématiques fondamentales :

### A. L'invariant de masse relationnelle
Pour toute matrice stochastique par colonnes, le couplage redistribue les influences sans modifier leur somme totale. Mathématiquement, pour un vecteur d'état \(x^-\), la variation induite par le couplage \(\Delta x_{\mathrm{couplage}} = Wx^- - x^-\) satisfait toujours :
\[
 \Delta x_1 + \Delta x_2 = 0 
\]
Cette propriété d'antisymétrie garantit que le système ne crée ni ne détruit de "ressource" lors de l'échange relationnel (avant compensation et écrêtage).

### B. L'identité spectrale
La paramétrisation \(W(\alpha)\) démontre qu'une transformation d'orientation (changement de la polarisation directionnelle \(W_{21} - W_{12}\)) peut s'opérer **à spectre strictement constant**.
Pour \(W(\alpha) = \begin{pmatrix} 0.8-\alpha & 0.2-\alpha \\ 0.2+\alpha & 0.8+\alpha \end{pmatrix}\) :
*   La trace reste constante : \(\mathrm{tr}(W) = 1.6\)
*   Le déterminant reste constant : \(\det(W) = 0.6\)
*   Les valeurs propres restent constantes : \(\lambda_1 = 1, \lambda_2 = 0.6\)

**Propriété algébrique démontrée : La famille de matrices W(\alpha) conserve un spectre constant. En revanche, la divergence des trajectoires fonctionnelles sous l'effet de la dynamique est une propriété du modèle qui doit être vérifiée par les simulations.**

**Précision sur la distribution et la reconstruction (Revue par les pairs) :**
Bien que le spectre (trace, déterminant, valeurs propres) soit strictement invariant, les vecteurs propres de \(W(\alpha)\) varient. Par conséquent, la distribution stationnaire \(\pi(\alpha)\) varie linéairement avec l'orientation : \(\pi = (0.5 - 2.5\alpha ; 0.5 + 2.5\alpha)\) sur le domaine \(\alpha \in [-0.2 ; 0.2]\). 
*Conséquence :* L'invariant spectral garantit la *vitesse de relaxation* (la loi physique), mais **ne détermine pas la direction de l'état** (vers où le système évolue). La capacité de reconstruction post-choc dépend donc de l'orientation \(\alpha\) (l'information de l'état), et non uniquement du spectre.

## 2. La Distinction Dose / Perte Réalisée

Dans un système soumis à un stress non linéaire (avec plafonnement), il est mathématiquement erroné de supposer qu'une "dose imposée" équivaut à une "dose subie".
*   **Dose nominale** : Somme des perturbations injectées.
*   **Dose d'entrée** : Perturbation après plafonnement (ex: \(\min(\delta P_t, 1)\)).
*   **Dose réalisée** : Perte effective calculée comme \(x_t - x_t^-\), dépendante de l'état de remplissage du compartiment.

L'équivalence stricte des expériences (ex: stress chronique vs stress aigu) n'est possible que si la dose d'entrée est strictement normalisée (ex: via des solutions analytiques ou la méthode de Brent).

## 3. Les Trois Niveaux de Continuité

La viabilité (le fait de rester au-dessus d'un seuil \(F_{\min} \geq 0.25\)) n'est pas la résilience structurelle. Le programme distingue trois formes de continuité :

1.  **Continuité d'État** (Résistance) : Les variables internes (\(x_1, x_2\)) demeurent relativement stables.
2.  **Continuité Fonctionnelle** (Viabilité) : Le système maintient son intégrité globale. La fonction de viabilité est définie comme le produit des états : \(F(x) = x_1 x_2\) (ou une somme pondérée pour N états).
3.  **Continuité Relationnelle** (Invariant) : L'organisation (ex: le spectre de \(W\), la conservation de la masse) demeure reconnaissable malgré la déformation des états.

## 4. Hypothèse Fondamentale du Programme

À partir des outils de la V49 (mesure des flux bruts \(J_{12}\), \(J_{21}\), et suivi de la récupération), le programme pose l'hypothèse falsifiable suivante :

> **Un système peut subir une transformation profonde de ses états et de ses flux (perte de viabilité fonctionnelle) tout en conservant les invariants spectraux et structurels qui rendent possible sa reconstruction ou sa reconnaissance organisationnelle.**

Le passage de la V49 à la V50 devra tester si cette conservation des invariants permet effectivement une reconstruction post-choc (V51), ou si la dégradation fonctionnelle détruit irrémédiablement la capacité de retour à l'équilibre.
