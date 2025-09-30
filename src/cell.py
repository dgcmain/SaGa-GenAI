from __future__ import annotations
import random
from uuid import uuid4, UUID
from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class Cell:
    id: UUID
    energy: float
    position: Tuple[float, float]

    # dynamics
    reproduction_probability: float = 0.1       
    reproduction_energy_threshold: float = 35.0  
    reproduction_age_threshold: int = 25         
    growth_factor: float = 0.0
    basal_metabolism: float = 0.001
    move_cost_per_unit: float = 0.00001
    max_energy: float = 50.0

    # movement
    vx: float = 0.0
    vy: float = 0.0
    speed: float = 3.0           # max speed magnitude
    jitter: float = 1.0          # random perturbation each cycle

    # visual properties
    min_diameter: float = 5.0    # diameter when energy = 0
    max_diameter: float = 30.0   # diameter when energy = max_energy
    
    color: Tuple[float, float, float] = field(default_factory=lambda: (0.0, random.uniform(0.7, 0.99), 0.0))
    color_mutation_rate: float = 0.99     # Probability of color mutation during reproduction
    color_mutation_strength: float = 0.8  # How much colors can change during mutation

    # lifetime tracking
    age: int = 0
    max_age: int = 500

    @property
    def diameter(self) -> float:
        """Diameter linearly proportional to energy."""
        if self.energy <= 0:
            return 0.0
        
        # Simple linear scaling - no artificial max restriction
        return self.energy

    @property
    def hex_color(self) -> str:
        """Convert RGB color to hex format for matplotlib."""
        r, g, b = self.color
        return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'

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
            "color": self.color,
            "hex_color": self.hex_color,
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
                
        if self.energy <= 0.0:
            self.die()
            return None

        self.think()
        self.move()

        # if self.energy > self.max_energy:
        #     self.energy = self.max_energy

        return self.reproduce()

    def grow(self, amount: float) -> None:
        self.energy += amount

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

            # Inherit color with possible mutation
            child = Cell(
                id=uuid4(),
                energy=child_energy,
                position=(self.position[0] + random.uniform(-25.0, 25.0), 
                          self.position[1] + random.uniform(-25.0, 25.0)),
                vx=-self.vx * 0.4,
                vy=-self.vy * 0.4,
                speed=self.speed,
                jitter=self.jitter,
                reproduction_probability=self.reproduction_probability,
                reproduction_energy_threshold=self.reproduction_energy_threshold,
                reproduction_age_threshold=self.reproduction_age_threshold,
                growth_factor=self.growth_factor,
                basal_metabolism=self.basal_metabolism,
                move_cost_per_unit=self.move_cost_per_unit,
                max_energy=self.max_energy,
                min_diameter=self.min_diameter,
                max_diameter=self.max_diameter,
                color=self._mutate_color(),
                color_mutation_rate=self.color_mutation_rate,
                color_mutation_strength=self.color_mutation_strength,
                age=0,
                max_age=self.max_age,
            )

        return child

    def _mutate_color(self) -> Tuple[float, float, float]:
        """Mutate the color with some probability, otherwise inherit parent's color."""
        if random.random() > self.color_mutation_rate:
            return self.color
        r, g, b = self.color
        r = max(0.0, min(1.0, r + random.uniform(-self.color_mutation_strength, self.color_mutation_strength)))
        g = max(0.0, min(1.0, g + random.uniform(-self.color_mutation_strength, self.color_mutation_strength)))
        b = max(0.0, min(1.0, b + random.uniform(-self.color_mutation_strength, self.color_mutation_strength)))        
        new_color = (r, g, b)
        return new_color

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
        """Update the cell's velocity with random jitter."""
        self.vx = self.vx + random.uniform(-self.jitter, self.jitter)
        self.vy = self.vy + random.uniform(-self.jitter, self.jitter)

        # Clamp to max speed
        speed_squared = self.vx**2 + self.vy**2
        if speed_squared > self.speed**2:
            scale = self.speed / (speed_squared ** 0.5)
            self.vx *= scale
            self.vy *= scale

    def _state(self) -> dict:
        return {
            "id": str(self.id),
            "energy": self.energy,
            "position": self.position,
            "diameter": self.diameter,
            "age": self.age,
            "max_age": self.max_age,
            "color": self.color,
            "hex_color": self.hex_color,
            "lifetime_stats": self.lifetime_stats,
        }