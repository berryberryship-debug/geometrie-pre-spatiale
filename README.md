# Géométrie Pré-Spatiale et Résilience Stochastique
### Étude computationnelle des interactions entre couplage asymétrique, compensation locale et fluctuations stochastiques dans un système dynamique à deux compartiments

## Objet de recherche

Ce projet étudie les conditions dans lesquelles un système dynamique composé de deux compartiments interdépendants conserve, redistribue ou restaure son intégrité sous perturbations.

L'architecture expérimentale repose sur trois mécanismes :

- **Perturbation stochastique** : introduction de fluctuations contrôlées afin d'étudier leur influence sur les trajectoires et les transitions entre régimes dynamiques.
- **Couplage asymétrique** : circulation non équivalente des influences entre compartiments, permettant d'examiner les transferts directionnels et leurs conséquences sur l'intégrité du système.
- **Compensation locale** : mécanisme correctif agissant sur les déficits internes, dont l'efficacité est étudiée en présence et en absence de couplage.

## Fondement géométrique : organisation pré-spatiale des relations

La géométrie pré-spatiale constitue le cadre théorique dans lequel sont étudiées les configurations relationnelles précédant leur représentation dans un espace géométrique explicite.

L'objet premier n'est pas la position des compartiments, mais la structure des relations qui les constituent : orientation, intensité, asymétrie, dépendance, réciprocité et transformation.

Cette approche distingue :
1. **L'état** : configuration instantanée des variables internes.
2. **La relation** : dépendance dynamique entre les composantes du système.
3. **La configuration** : organisation globale produite par l'ensemble des relations.
4. **L'invariant relationnel** : propriété conservée malgré les transformations des états ou des relations.
5. **La reconfiguration** : transformation de l'organisation relationnelle sous perturbation.

La question géométrique centrale devient alors :
> Dans quelles conditions un système peut-il transformer ses états et ses relations tout en conservant une continuité structurelle identifiable ?

## Problématique centrale

Dans quelles conditions l'interaction entre fluctuations stochastiques, asymétrie relationnelle et compensation locale favorise-t-elle la conservation de l'intégrité du système, et dans quelles conditions produit-elle au contraire une redistribution du dommage ou une dégradation de ses capacités de récupération ?

## Axes d'analyse

1. **Stabilité dynamique** — caractérisation des régimes stationnaires, transitoires et instables.
2. **Transfert intercompartimental** — quantification du flux directionnel, du transfert net et de la redistribution des déficits.
3. **Compensation et régulation** — mesure de l'efficacité corrective locale et de ses effets sur l'état global.
4. **Sensibilité stochastique** — détermination de l'influence de l'intensité et de la structure du bruit sur les transitions dynamiques.
5. **Résilience** — évaluation de la capacité de récupération, de la durée des perturbations et de la conservation de l'intégrité après sollicitation.
6. **Structure relationnelle** — étude des propriétés géométriques et des transformations induites par l'asymétrie du couplage.

## Distinctions conceptuelles et méthodologiques

- **Résistance** : capacité à limiter la dégradation pendant la perturbation.
- **Récupération** : capacité à retrouver un état fonctionnel après la perturbation.
- **Résilience structurelle** : capacité à préserver ou reconstruire les relations constitutives du système malgré les transformations de ses états internes.
- **Dose imposée vs Dose réalisée** : distinction stricte entre l'intensité de la perturbation injectée dans le modèle (soumise à des effets de plafonnement) et la perte effectivement subie par les compartiments selon leur état disponible.
- **Viabilité sous stress vs Viabilité après récupération** : séparation des métriques évaluant la survie pendant le choc et celles évaluant la capacité de retour à l'équilibre post-choc.

## Statut des résultats et fil directeur

Les simulations (versions V48.16 à V48.37) fournissent des observations préliminaires concernant les interactions entre compensation, couplage et transfert de dommage.

Les protocoles tardifs (V48.33 à V48.37) ont permis de corriger les biais d'appariement, d'assurer une équivalence de dose d'entrée stricte, et de mesurer la viabilité avec des intervalles de confiance (IC de Wilson). 

La qualification de résonance stochastique, de transition topologique ou de résilience émergente demeure conditionnée à des critères opérationnels, des contrôles comparatifs et des tests de robustesse indépendants.

**Hypothèse structurante :**
> La continuité d'un système ne réside peut-être pas dans la conservation de ses états, mais dans la conservation, la transformation ou la reconstruction de certaines relations qui rendent son organisation identifiable.

La prochaine étape du programme théorique consiste à formaliser les invariants relationnels avant d'ajouter de nouveaux mécanismes à la simulation.

## Fichiers

- `audit_v2.py` : Protocole d'évaluation multidimensionnelle des métriques topologiques et informationnelles.
- `test_v48_22.py` : Moteur de mesure de la continuité relationnelle (préchauffage, bruit apparié).
- `test_v48_25.py` : Test de plasticité relationnelle (mutation de la matrice W sous le stress).
- `test_v48_28.py` : Audit contrôlé avec appariement strict par transformée inverse.
- `test_v48_33.py` : Équivalence de dose et effet du calendrier temporel (chocs réguliers, groupés, aléatoires).
- `test_v48_37_conclusion.py` : Protocole final traçant la surface de viabilité (matrice paramétrique de l'asymétrie, calcul strict de la dose réalisée, et double analyse stress/récupération avec IC de Wilson).
