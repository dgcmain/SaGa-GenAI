from __future__ import annotations

import random
from uuid import uuid4, UUID
from dataclasses import dataclass

@dataclass
class Cell:
    id: UUID
    energy: float
    position: tuple[float, float]

    reproduction_probability: float = 0.8
    growth_factor: float = 1.0
    degradation_factor: float = 0.98
    max_energy: float = 100.0

    def run(self) -> Cell | None:
        """Simulate one cycle of the cell's life."""
        if self.energy <= 0:
            self.die()
            return

        offspring = None
        self.grow(amount=self.growth_factor)
        self.degrade(factor=self.degradation_factor)
        if random.random() < self.reproduction_probability and self.energy > 20:
            offspring = self.reproduce()

        self.move(new_position=self.position + (random.uniform(-5, 5), random.uniform(-5, 5)))

        if self.energy > self.max_energy:
            self.energy = self.max_energy

        return offspring

    def grow(self, amount: float) -> None:
        """Increase energy by a growth factor each cycle."""
        self.energy += amount

    def move(self, new_position: tuple[float, float]) -> None:
        """Update the cell's position."""
        self.position = new_position

    def consume(self, food) -> None:
        """Consume food to gain energy."""
        # if food cerca
        # if venom cerca
        # self.energy += food.energy
        # food.energy = 0.0

    def die(self) -> None:
        """Handle the cell's death."""
        self.energy = 0.0
        self.position = (0.0, 0.0)

    def reproduce(self) -> Cell:
        """Create a new cell with half the energy."""
        offspring_energy = self.energy / 2
        self.energy /= 2
        return Cell(id=uuid4(), energy=offspring_energy, position=self.position)

    def degrade(self, factor: float = 0.98) -> None:
        """Reduce energy by a degradation factor each cycle."""
        self.energy *= factor
        if self.energy < 0.01:
            self.energy = 0.0
