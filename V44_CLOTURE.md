# V44 — Clôture Scientifique : Invariants Combinatoires et Limites

Ce document marque la clôture de la phase V44. Il sépare rigoureusement les résultats mathématiques démontrés des hypothèses phénoménologiques qui en découlent.

## 1. Les Acquis Mathématiques (Démontrés)

La phase V44 a permis d'établir les résultats suivants sur les graphes simples non orientés :

1.  **Définition du rang cyclomatique** sur le support actif : \(\beta_1(A) = |E_A| - |V_A| + C(H_A)\).
2.  **Transformée de Möbius** de \(\beta_1\) : \(I_{\beta_1}(A) = \sum_{T \subseteq A} (-1)^{|A|-|T|} \beta_1(T)\).
3.  **Théorème de détection des cycles** : Pour tout cycle simple \(C_k\), la transformée de Möbius \(I_{\beta_1}(C_k) = 1\). La réciproque est fausse.
4.  **Classes de faux positifs** : Deux classes isomorphes de sous-graphes denses (extraits de \(K_5\)) produisent également \(I_{\beta_1} = 1\) (Classe 1 : \(K_5 \setminus P_4\) ; Classe 2 : \(K_5 \setminus K_3\)).
5.  **Sensibilité différentielle** : Sous le retrait d'une arête, un cycle pur s'effondre (\(\Delta \beta_1 = -1\), \(I_{\beta_1} \to 0\)), tandis que les faux positifs conservent parfois leur coefficient (\(I_{\beta_1} \
