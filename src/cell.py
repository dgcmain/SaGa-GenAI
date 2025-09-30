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
    reproduction_probability: float = 0.1   # less frequent
    growth_factor: float = 0.0              # no passive growth (let FOOD drive growth)
    degradation_factor: float = 0.998       # mild multiplicative decay
    basal_metabolism: float = 0.05          # fixed cost per tick
    move_cost_per_unit: float = 0.01        # cost per unit of speed (per tick)
    max_energy: float = 50.0                # lower cap to avoid huge bubbles

    # movement
    vx: float = 0.0
    vy: float = 0.0
    speed: float = 3.0           # max speed magnitude
    jitter: float = 1.0          # random perturbation each cycle

    # visual properties
    min_diameter: float = 5.0    # diameter when energy = 0
    max_diameter: float = 30.0   # diameter when energy = max_energy

    @property
    def diameter(self) -> float:
        """Diameter linearly proportional to energy, clamped between min and max."""
        if self.energy <= 0:
            return self.min_diameter
        
        # Linear interpolation between min and max diameter based on energy
        energy_ratio = min(self.energy / self.max_energy, 1.0)  # clamp to 1.0
        return self.min_diameter + energy_ratio * (self.max_diameter - self.min_diameter)

    def run(self) -> Cell | None:
        if self.energy <= 0.0:
            self.die()
            return None

        # 1) Apply basal metabolism FIRST - this makes cells shrink over time
        self.energy -= self.basal_metabolism
        
        # 2) Apply movement cost
        speed_mag = (self.vx**2 + self.vy**2)**0.5
        self.energy -= self.move_cost_per_unit * speed_mag
        
        # 3) Apply degradation (multiplicative decay)
        self.degrade(self.degradation_factor)
        
        # 4) Check if cell died from energy loss
        if self.energy <= 0.0:
            self.die()
            return None

        # 5) update movement
        self.move()

        # 6) clamp energy to max
        if self.energy > self.max_energy:
            self.energy = self.max_energy

        # 7) reproduction (costly) - only if enough energy
        offspring = None
        if self.energy > 20.0 and random.random() < self.reproduction_probability:
            # Give child a fraction of energy; parent pays extra penalty
            fraction = 0.3
            child_energy = self.energy * fraction
            self.energy -= child_energy + 1.0  # reproduction overhead
            
            # Check if parent died from reproduction cost
            if self.energy <= 0.0:
                self.die()
                return None
                
            offspring = Cell(
                id=uuid4(),
                energy=child_energy,
                position=self.position,
                vx=-self.vx * 0.4,
                vy=-self.vy * 0.4,
                speed=self.speed,
                jitter=self.jitter,
                reproduction_probability=self.reproduction_probability,
                growth_factor=self.growth_factor,
                degradation_factor=self.degradation_factor,
                basal_metabolism=self.basal_metabolism,
                move_cost_per_unit=self.move_cost_per_unit,
                max_energy=self.max_energy,
                min_diameter=self.min_diameter,
                max_diameter=self.max_diameter,
            )

        return offspring

    def grow(self, amount: float) -> None:
        self.energy += amount

    def degrade(self, factor: float) -> None:
        self.energy *= factor
        if self.energy < 0.01:
            self.energy = 0.0

    def die(self) -> None:
        self.energy = 0.0

    def update_velocity(self, velocity: Tuple[float, float], dt: float = 1.0) -> None:
        """
        Update the cell's velocity based on an external (vx, vy) tuple.
        Velocity is clamped to the max speed.
        """
        vx, vy = velocity
        s2 = vx * vx + vy * vy
        if s2 > self.speed * self.speed:
            k = self.speed / (s2 ** 0.5)
            vx *= k
            vy *= k
        self.vx = vx
        self.vy = vy

    def move(self) -> None:
        x, y = self.position
        self.position = (x + self.vx, y + self.vy)

    def consume(self, food) -> None:
        gained = getattr(food, "energy", 0.0)
        self.energy += gained
        if hasattr(food, "energy"):
            food.energy = 0.0
        if self.energy > self.max_energy:
            self.energy = self.max_energy

    def _state(self) -> dict:
        return {
            "id": str(self.id),
            "energy": self.energy,
            "position": self.position,
            "diameter": self.diameter,
        }
