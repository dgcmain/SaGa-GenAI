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
    reproduction_probability: float = 0.75  # 75% chance when conditions are met
    reproduction_energy_threshold: float = 35.0  # Energy level required for reproduction
    reproduction_age_threshold: int = 10  # Minimum age (cycles) required for reproduction
    growth_factor: float = 0.0
    degradation_factor: float = 0.998
    basal_metabolism: float = 0.05
    move_cost_per_unit: float = 0.01
    max_energy: float = 50.0

    # movement
    vx: float = 0.0
    vy: float = 0.0
    speed: float = 3.0           # max speed magnitude
    jitter: float = 1.0          # random perturbation each cycle

    # visual properties
    min_diameter: float = 5.0    # diameter when energy = 0
    max_diameter: float = 30.0   # diameter when energy = max_energy

    # lifetime tracking
    age: int = 0
    max_age: int = 500

    @property
    def diameter(self) -> float:
        """Diameter linearly proportional to energy, clamped between min and max."""
        if self.energy <= 0:
            return self.min_diameter
        
        # Linear interpolation between min and max diameter based on energy
        energy_ratio = min(self.energy / self.max_energy, 1.0)  # clamp to 1.0
        return self.min_diameter + energy_ratio * (self.max_diameter - self.min_diameter)

    @property
    def lifetime_stats(self) -> dict:
        """Get statistics about the cell's lifetime."""
        return {
            "age": self.age,
            "max_age": self.max_age,
            "energy_ratio": self.energy / self.max_energy,
            "can_reproduce": (
                self.energy >= self.reproduction_energy_threshold and 
                self.age >= self.reproduction_age_threshold
            ),
            "reproduction_ready": (
                f"Energy: {self.energy >= self.reproduction_energy_threshold}, "
                f"Age: {self.age >= self.reproduction_age_threshold}"
            )
        }

    def run(self) -> Cell | None:
        self.age += 1
        if self.age >= self.max_age:
            self.die()
            return None
            
        if self.energy <= 0.0:
            self.die()
            return None

        self.energy -= self.basal_metabolism

        speed_mag = (self.vx**2 + self.vy**2)**0.5
        self.energy -= self.move_cost_per_unit * speed_mag
        
        self.degrade(self.degradation_factor)
        
        if self.energy <= 0.0:
            self.die()
            return None

        self.think()
        self.move()

        if self.energy > self.max_energy:
            self.energy = self.max_energy

        return self.reproduce()

    def grow(self, amount: float) -> None:
        self.energy += amount

    def degrade(self, factor: float) -> None:
        self.energy *= factor
        if self.energy < 0.01:
            self.energy = 0.0

    def die(self) -> None:
        self.energy = 0.0

    def reproduce(self) -> Cell | None:
        can_reproduce = (
            self.energy >= self.reproduction_energy_threshold and 
            self.age >= self.reproduction_age_threshold and
            random.random() < self.reproduction_probability
        )
        child = None
        if can_reproduce:
            fraction = 0.4
            child_energy = self.energy * fraction
            self.energy -= child_energy + 2.0

            if self.energy <= 0.0:
                self.die()
                return None

            child = Cell(
                id=uuid4(),
                energy=child_energy,
                position=(self.position[0] + random.uniform(-25.0, 25.0), self.position[1] + random.uniform(-25.0, 25.0)),
                vx=-self.vx * 0.4,
                vy=-self.vy * 0.4,
                speed=self.speed,
                jitter=self.jitter,
                reproduction_probability=self.reproduction_probability,
                reproduction_energy_threshold=self.reproduction_energy_threshold,
                reproduction_age_threshold=self.reproduction_age_threshold,
                growth_factor=self.growth_factor,
                degradation_factor=self.degradation_factor,
                basal_metabolism=self.basal_metabolism,
                move_cost_per_unit=self.move_cost_per_unit,
                max_energy=self.max_energy,
                min_diameter=self.min_diameter,
                max_diameter=self.max_diameter,
                age=0,
                max_age=self.max_age,
            )

        return child

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

    def think(self) -> None:
        self._update_velocity()

    def _update_velocity(self) -> None:
    
        """
        Update the cell's velocity based on an external (vx, vy) tuple.
        Velocity is clamped to the max speed.
        """
        self.vx = self.vx + random.uniform(-self.jitter, self.jitter)
        self.vy = self.vy + random.uniform(-self.jitter, self.jitter)

    def _state(self) -> dict:
        return {
            "id": str(self.id),
            "energy": self.energy,
            "position": self.position,
            "diameter": self.diameter,
            "age": self.age,
            "max_age": self.max_age,
            "lifetime_stats": self.lifetime_stats,
        }