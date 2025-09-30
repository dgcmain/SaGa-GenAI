from __future__ import annotations
import random, math
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

    # movement - EXPLORATORY SETTINGS
    vx: float = 5.0  # Start with some initial movement
    vy: float = 5.0
    ax: float = 0.0
    ay: float = 0.0
    speed: float = 4.0  # Good exploration speed
    accel_sigma: float = 1.2  # More acceleration for direction changes
    accel_tau: float = 0.8    # Slower acceleration changes for sustained movement
    vel_damping: float = 0.05  # Much less damping for continuous movement
    
    # Direction change system
    direction_change_prob: float = 0.02  # 2% chance per cycle to change direction
    min_movement_time: int = 30  # Minimum cycles before considering direction change
    movement_timer: int = 0

    color: Tuple[float, float, float] = field(default_factory=lambda: (0.0, random.uniform(0.7, 0.99), 0.0))
    color_mutation_rate: float = 0.99    
    color_mutation_strength: float = 0.8 

    # lifetime tracking
    age: int = 0
    max_age: int = 500

    @property
    def diameter(self) -> float:
        """Diameter linearly proportional to energy."""
        if self.energy <= 0:
            return 0.0
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
        self.movement_timer += 1
        
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
            fraction = 0.5
            child_energy = self.energy * fraction
            self.energy -= child_energy + 2.0

            if self.energy <= 0.0:
                self.die()
                return None

            # Give child some random initial direction
            angle = random.uniform(0, 2 * math.pi)
            child_vx = math.cos(angle) * 2.0
            child_vy = math.sin(angle) * 2.0

            child = Cell(
                id=uuid4(),
                energy=child_energy,
                position=(self.position[0] + random.uniform(-25.0, 25.0), 
                          self.position[1] + random.uniform(-25.0, 25.0)),
                vx=child_vx,
                vy=child_vy,
                ax=0.0,
                ay=0.0,
                speed=self.speed,
                accel_sigma=self.accel_sigma,
                accel_tau=self.accel_tau,
                vel_damping=self.vel_damping,
                direction_change_prob=self.direction_change_prob,
                min_movement_time=self.min_movement_time,
                movement_timer=0,
                reproduction_probability=self.reproduction_probability,
                reproduction_energy_threshold=self.reproduction_energy_threshold,
                reproduction_age_threshold=self.reproduction_age_threshold,
                growth_factor=self.growth_factor,
                basal_metabolism=self.basal_metabolism,
                move_cost_per_unit=self.move_cost_per_unit,
                max_energy=self.max_energy,
                color=self._mutate_color(),
                color_mutation_rate=self.color_mutation_rate,
                color_mutation_strength=self.color_mutation_strength,
                age=0,
                max_age=self.max_age,
            )

        return child

    def _mutate_color(self) -> Tuple[float, float, float]:
        """Mutate only the green channel with some probability, otherwise inherit parent's color."""
        if random.random() > self.color_mutation_rate:
            return self.color
        
        r, g, b = self.color
        g = max(0.0, min(1.0, g + random.uniform(-self.color_mutation_strength, self.color_mutation_strength)))
        return (r, g, b)

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
        self._update_velocity(dt=1.0)
        self._consider_direction_change()

    def _consider_direction_change(self):
        """Randomly change direction to explore more."""
        if (self.movement_timer > self.min_movement_time and 
            random.random() < self.direction_change_prob):
            
            # Significant direction change
            angle_change = random.uniform(-math.pi/2, math.pi/2)  # ±90 degrees
            current_angle = math.atan2(self.vy, self.vx)
            new_angle = current_angle + angle_change
            
            # Set new velocity with some randomness
            speed = math.sqrt(self.vx**2 + self.vy**2)
            new_speed = max(1.0, speed * random.uniform(0.8, 1.2))
            
            self.vx = math.cos(new_angle) * new_speed
            self.vy = math.sin(new_angle) * new_speed
            
            # Reset acceleration for fresh start
            self.ax = 0.0
            self.ay = 0.0
            self.movement_timer = 0

    def _update_velocity(self, dt: float) -> None:
        """
        Update velocity with smooth exploration.
        """
        if dt <= 0:
            return

        # Gentle acceleration changes for organic movement
        sigma = self.accel_sigma
        tau = max(0.08, self.accel_tau)

        # Ornstein-Uhlenbeck process for smooth wandering
        sqrt_dt = math.sqrt(dt)
        self.ax += (-self.ax / tau) * dt + sigma * sqrt_dt * random.gauss(0, 1)
        self.ay += (-self.ay / tau) * dt + sigma * sqrt_dt * random.gauss(0, 1)

        # Integrate acceleration
        self.vx += self.ax * dt
        self.vy += self.ay * dt

        # Very gentle damping - just enough to prevent explosion
        damp = max(0.0, min(1.0, self.vel_damping * dt))
        self.vx *= (1.0 - damp)
        self.vy *= (1.0 - damp)

        # Maintain reasonable speed with soft cap
        v2 = self.vx**2 + self.vy**2
        vmax = max(1e-6, self.speed)
        vmax2 = vmax * vmax
        
        if v2 > vmax2 * 1.5:  # Only cap if significantly over
            scale = vmax / math.sqrt(v2)
            alpha = 0.3
            self.vx = (1 - alpha) * self.vx + alpha * (self.vx * scale)
            self.vy = (1 - alpha) * self.vy + alpha * (self.vy * scale)
        elif v2 < 0.5:  # Give a little push if moving too slow
            boost = 0.5
            self.vx += random.uniform(-boost, boost)
            self.vy += random.uniform(-boost, boost)

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