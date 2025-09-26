from __future__ import annotations
import random
from uuid import uuid4, UUID
from dataclasses import dataclass
from typing import Tuple


@dataclass
class Cell:
    id: UUID
    energy: float
    position: Tuple[float, float]

    # dynamics
    reproduction_probability: float = 0.2
    growth_factor: float = 0.5
    degradation_factor: float = 0.99
    max_energy: float = 100.0

    # movement
    vx: float = 0.0
    vy: float = 0.0
    speed: float = 3.0          # maximum speed magnitude
    jitter: float = 1.0         # random perturbation each cycle

    def run(self) -> Cell | None:
        """Simulate one cycle of the cell's life."""
        if self.energy <= 0.0:
            self.die()
            return None

        # growth/decay
        self.grow(self.growth_factor)
        self.degrade(self.degradation_factor)

        # movement
        self.update_velocity()
        self.move()

        # reproduction
        offspring = None
        if self.energy > 20 and random.random() < self.reproduction_probability:
            offspring = self.reproduce()

        # cap energy
        if self.energy > self.max_energy:
            self.energy = self.max_energy

        return offspring


    def grow(self, amount: float) -> None:
        self.energy += amount

    def degrade(self, factor: float = 0.98) -> None:
        self.energy *= factor
        if self.energy < 0.01:
            self.energy = 0.0

    def die(self) -> None:
        self.energy = 0.0


    def update_velocity(self) -> None:
        """Random walk with inertia, limited by max speed."""
        # small random perturbation to velocity
        self.vx += random.uniform(-self.jitter, self.jitter)
        self.vy += random.uniform(-self.jitter, self.jitter)

        # clamp to max speed
        speed2 = self.vx**2 + self.vy**2
        if speed2 > self.speed**2:
            factor = self.speed / (speed2**0.5)
            self.vx *= factor
            self.vy *= factor

    def move(self) -> None:
        """Update position according to velocity."""
        x, y = self.position
        self.position = (x + self.vx, y + self.vy)


    def consume(self, food) -> None:
        """Consume food to gain energy (placeholder)."""
        self.energy += getattr(food, "energy", 0.0)
        if hasattr(food, "energy"):
            food.energy = 0.0


    def reproduce(self) -> Cell:
        """Create a new cell with half the energy."""
        offspring_energy = self.energy / 2
        self.energy /= 2
        return Cell(
            id=uuid4(),
            energy=offspring_energy,
            position=self.position,
            vx=-self.vx * 0.5,   # offspring drifts away
            vy=-self.vy * 0.5,
            speed=self.speed,
            jitter=self.jitter,
        )
