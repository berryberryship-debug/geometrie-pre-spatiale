# Géométrie Pré-Spatiale : Continuité d'État, de Fonction et de Structure

## Le Fil Directeur du Programme

Ce projet n'est pas une simple collection de simulations. Il explore une hypothèse fondamentale sur la nature des systèmes complexes : la manière dont une organisation maintient son identité face aux perturbations.

Pour cela, nous distinguons rigoureusement trois formes de continuité :

*   **La continuité d'état** : Ce qui demeure dans les variables internes (résistance classique).
*   **La continuité fonctionnelle** : Ce que le système peut encore accomplir (viabilité).
*   **La continuité structurelle** : Les relations qui persistent, même lorsque l'état et la fonction sont altérés.

## Architecture des Versions

L'évolution du dépôt suit cette progression conceptuelle :

| Version | Contribution au fil directeur |
| :--- | :--- |
| **V44** | **Invariants Topologiques** : Identification et discrimination d'invariants (Möbius, cycles) pour définir la continuité structurelle. |
| **V48** | **Dynamique des États** : Couplages, redistribution et transfert de dommage sous perturbations. |
| **V49** | **Conservation Relationnelle** : Polarisation directionnelle et conservation de la masse relationnelle (via des matrices colonne-stochastiques). |
| **V50** | **Frontière de Viabilité** : Cartographie probabiliste de l'effondrement fonctionnel (Intervalles de Wilson). |
| **V51** | **Plasticité et Reconstruction** : Mutations structurelles et capacité de l'organisation à se reconstruire. |

## Le Verrou Mathématique de V49

Pour que la géométrie relationnelle ait un sens physique, la conservation de la masse relationnelle doit être garantie. Si \(\mathbf{1}^\top x\) est la masse, alors la matrice de couplage \(W\) doit impérativement être **colonne-stochastique** :
\[
 \mathbf{1}^\top W = \mathbf{1}^\top 
\]
Sans cette propriété, le couplage détruit ou crée de l'information, invalidant l'analyse des invariants.

## L'Hypothèse Centrale

> **Sans cette propriété (matrice colonne-stochastique), la conservation de la masse relationnelle n'est plus garantie. L'analyse des invariants de somme doit alors être reformulée.**
> 
> Un système peut conserver certaines relations organisatrices malgré une altération profonde de ses états et de ses fonctions. Ces relations invariantes constituent les conditions de possibilité d'une reconstruction.

## Conclusion

La géométrie relationnelle (l'étude de ce qui persiste) devient ainsi l'objet théorique unificateur. Les états (V48) et la viabilité (V50) ne sont que des niveaux d'observation d'une structure plus profonde, dont V44 et V49 nous donnent les premiers invariants mathématiques.
