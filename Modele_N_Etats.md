# Exploration du Modèle à N-états (N=3, N=4)

## Contexte
Le modèle à 2 états (\(W(\alpha)\)) a démontré une identité spectrale : le spectre reste constant tandis que l'orientation \(\alpha\) modifie la distribution stationnaire \(\pi\). La viabilité est dictée par \(\pi\), pas par le spectre.

## Objectif
Construire une famille isospectrale de matrices stochastiques pour N=3 et N=4, afin de tester si un **ralentissement critique** (spectral gap tendant vers 0, temps de relaxation \(\tau \to \infty\)) peut apparaître à spectre strictement constant.

## Proposition Mathématique (Revue par les pairs)
Construire \(W(\alpha)\) sous la forme :
\[ W(\alpha) = \pi(\alpha)1^T + R \]
Où :
*   \(\pi(\alpha)\) est la distribution stationnaire variant avec l'orientation \(\alpha\).
*   \(1^T\) est le vecteur ligne de uns.
*   \(R\) est une matrice qui conserve la partie non triviale du spectre (les valeurs propres \(\lambda_2, \lambda_3...\)).

## Fonction de Viabilité
Pour ce test à N états, la fonction de viabilité \(F\) est définie comme le produit des états (l'intégrité fonctionnelle) : \(F(x) = x_1 \cdot x_2 \cdot ... \cdot x_N\). Le seuil critique reste \(F_{\min} \geq 0.25\).

## Question pour l'Agent de Recherche (ou l'IA)
"Dans cette famille isospectrale à N états, si l'on fait varier \(\alpha\) (l'orientation) tout en gardant le spectre strictement constant, observe-t-on l'apparition d'un ralentissement critique (spectral gap \(\to 0\)) ? Comment cela se traduit-il physiquement en termes de brisure de symétrie (comme le champ \(h\) dans le modèle de Curie-Weiss) ?"
