"""
Moteur de Cohérence Contextuelle (MCC)

États internes :
  - M_c  : Charge (accumulation de friction)
  - M_r  : Régulation (protection produite)
  - C    : Cohérence / contexte (qualité de la réponse)
  - sigma: Stress résiduel (M_c - M_r)

Le moteur est purement déterministe et sans effet de bord.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, Callable, List, Optional


@dataclass
class State:
    t: float
    M_c: float
    M_r: float
    C: float
    sigma: float
    step: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MCCEngine:
    """
    Simulateur simple de cohérence contextuelle.

    Paramètres
    ----------
    dt : float
        Pas de temps.
    friction_gain : float
        Gain appliqué à la friction externe.
    protection_gain : float
        Gain de production de régulation.
    stress_threshold : float
        Seuil au-delà duquel le contexte commence à se dégrader.
    context_decay : float
        Vitesse de dégradation du contexte sous stress.
    """

    def __init__(
        self,
        dt: float = 0.1,
        friction_gain: float = 1.0,
        protection_gain: float = 0.8,
        stress_threshold: float = 0.5,
        context_decay: float = 0.05,
    ):
        self.dt = dt
        self.friction_gain = friction_gain
        self.protection_gain = protection_gain
        self.stress_threshold = stress_threshold
        self.context_decay = context_decay

        # État initial
        self.M_c = 0.5
        self.M_r = 0.3
        self.C = 1.0
        self.t = 0.0
        self._step_count = 0

    def reset(self) -> None:
        """Remet le moteur dans son état initial."""
        self.M_c = 0.5
        self.M_r = 0.3
        self.C = 1.0
        self.t = 0.0
        self._step_count = 0

    def step(self, friction_externe: float, protection_demandee: float) -> State:
        """
        Effectue un pas de simulation.
        """
        # Accumulation de charge
        self.M_c += friction_externe * self.friction_gain * self.dt

        # Production de régulation
        protection_produite = protection_demandee * self.C * self.protection_gain
        self.M_r += protection_produite * self.dt

        # Stress résiduel
        sigma = max(0.0, self.M_c - self.M_r)

        # Dégradation du contexte sous stress
        if sigma > self.stress_threshold:
            self.C -= self.context_decay * self.dt

        # Bornes
        self.C = max(0.1, min(1.0, self.C))
        self.t += self.dt
        self._step_count += 1

        return State(
            t=round(self.t, 4),
            M_c=round(self.M_c, 6),
            M_r=round(self.M_r, 6),
            C=round(self.C, 6),
            sigma=round(sigma, 6),
            step=self._step_count,
        )

    def run(
        self,
        n_steps: int,
        friction_fn: Optional[Callable[[int], float]] = None,
        protection_fn: Optional[Callable[[int], float]] = None,
    ) -> List[State]:
        """
        Lance une simulation complète.
        """
        if friction_fn is None:
            friction_fn = lambda s: 0.3 + 0.1 * (s % 5 == 0)
        if protection_fn is None:
            protection_fn = lambda s: 0.7

        history = []
        for s in range(1, n_steps + 1):
            state = self.step(friction_fn(s), protection_fn(s))
            history.append(state)
        return history
