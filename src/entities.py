from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
from uuid import UUID


@dataclass
class Food:
    id: UUID
    energy: float
    position: Tuple[float, float]

    def degrade(self, factor: float) -> None:
        self.energy *= factor
        if self.energy < 0.01:
            self.energy = 0.0

    @property
    def state(self) -> dict:
        return {
            "id": str(self.id),
            "energy": self.energy,
            "position": self.position,
        }


@dataclass
class Venom:
    id: UUID
    toxicity: float
    position: Tuple[float, float]

    def degrade(self, factor: float) -> None:
        self.toxicity *= factor
        if self.toxicity < 0.01:
            self.toxicity = 0.0

    @property
    def state(self) -> dict:
        return {
            "id": str(self.id),
            "energy": self.toxicity,
            "position": self.position,
        }