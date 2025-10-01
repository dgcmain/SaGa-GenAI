from __future__ import annotations
import random
import math
from uuid import uuid4, UUID
from dataclasses import dataclass, field

from tools import distance_to, mutate_color
from agents import llm_based_cell_movement


@dataclass
class Cell:
    id: UUID
    energy: float
    position: tuple[float, float]

    vx: float = 0.0
    vy: float = 0.0
    ax: float = 0.0
    ay: float = 0.0
    speed: float = 3.0
    accel_sigma: float = 1.5
    accel_tau: float = 0.5
    vel_damping: float = 0.02

    reproduction_probability: float = 0.1
    reproduction_energy_threshold: float = 35.0
    reproduction_age_threshold: int = 125
    
    basal_metabolism: float = 0.0001
    move_cost_per_unit: float = 0.00001
    max_energy: float = 50.0

    color: tuple[float, float, float] = field(default_factory=lambda: (0.0, random.uniform(0.7, 0.99), 0.0))
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

    @property
    def state(self) -> dict:
        """Gets cell state"""
        return {
            "id": str(self.id),
            "energy": self.energy,
            "position": self.position,
        }

    @property
    def state_full(self) -> dict:
        """Gets cell extended state"""
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

    def run(self, state) -> Cell | None:
        """
        Executes a single lifecycle step for the cell.
        This method updates the cell's age and energy, checks for death conditions,
        performs thinking and movement actions, and attempts reproduction.
        Args:
            state: The current simulation state or environment context.
        Returns:
            Cell | None: A new Cell instance if reproduction occurs, otherwise None.
            Returns None if the cell dies during this step.
        """

        self.metabolism()
        if (self.age >= self.max_age) or (self.energy <= 5.0):
            self.die()
            return None
        self.think(state)
        self.move()

        return self.reproduce()

    def metabolism(self) -> None:
        self.age += 1
        self.energy -= self.basal_metabolism
        self.energy -= self.move_cost_per_unit * (self.vx**2 + self.vy**2)**0.5

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

            angle = random.uniform(0, 2 * math.pi)
            child_vx = math.cos(angle) * 0.3
            child_vy = math.sin(angle) * 0.3
            child_color = mutate_color(self.color, self.color_mutation_rate, self.color_mutation_strength)
            child = Cell(
                id=uuid4(),
                energy=child_energy,
                position=(self.position[0] + self.energy/2 + random.uniform(-25.0, 25.0), 
                          self.position[1] + self.energy/2 + random.uniform(-25.0, 25.0)),
                vx=child_vx,
                vy=child_vy,
                ax=0.0,
                ay=0.0,
                speed=self.speed,
                accel_sigma=self.accel_sigma,
                accel_tau=self.accel_tau,
                vel_damping=self.vel_damping,
                reproduction_probability=self.reproduction_probability,
                reproduction_energy_threshold=self.reproduction_energy_threshold,
                reproduction_age_threshold=self.reproduction_age_threshold,
                basal_metabolism=self.basal_metabolism,
                move_cost_per_unit=self.move_cost_per_unit,
                max_energy=self.max_energy,
                color=child_color,
                color_mutation_rate=self.color_mutation_rate,
                color_mutation_strength=self.color_mutation_strength,
                age=0,
                max_age=self.max_age,
            )

        return child

    def move(self, dt: float = 1) -> None:
        """
        Update velocity with more aggressive exploration.
        """
        if dt <= 0:
            return

        # More significant acceleration changes for actual movement
        sigma = self.accel_sigma
        tau = max(0.08, self.accel_tau)

        # Ornstein-Uhlenbeck process for wandering
        sqrt_dt = math.sqrt(dt)
        self.ax += (-self.ax / tau) * dt + sigma * sqrt_dt * random.gauss(0, 1)
        self.ay += (-self.ay / tau) * dt + sigma * sqrt_dt * random.gauss(0, 1)

        # Integrate acceleration
        self.vx += self.ax * dt
        self.vy += self.ay * dt

        # Minimal damping - let them keep their momentum
        damp = max(0.0, min(1.0, self.vel_damping * dt))
        self.vx *= (1.0 - damp)
        self.vy *= (1.0 - damp)

        x, y = self.position
        self.position = (x + self.vx, y + self.vy)

    def think(self, universe_state: dict) -> None:
        """
        Updates the cell's state for one simulation step.
        This method performs the following actions:
        - Updates the cell's velocity.
        - Considers changing the cell's movement direction.
        - Finds the closest food item in the universe state and moves towards it if found.
        Args:
            universe_state (dict): The current state of the universe, containing information about food and other entities.
        """
        
        self.vx, self.vy = self._move_random()
        self.vx, self.vy = self._move_towards_closest_food(universe_state)
        # self.vx, self.vy = self._move_llm(universe_state)

    def _move_towards_closest_food(self, universe_state: dict) -> dict | None:
        """Find the closest food from universe state."""
        vx, vy = 0., 0.
        if "foods" not in universe_state or not universe_state.get("foods"):
            return vx, vy

        closest_food = None
        min_distance = float('inf')
        for food in universe_state["foods"]:
            if food.get("energy", 0) > 0:
                distance = distance_to(self.position, food.get("position", []))
                if distance < min_distance:
                    min_distance = distance
                    closest_food = food

        if not closest_food:
            return vx, vy

        food_pos = closest_food.get("position")
        current_speed = math.sqrt(self.vx**2 + self.vy**2)
        dx = food_pos[0] - self.position[0]
        dy = food_pos[1] - self.position[1]
        distance = math.sqrt(dx**2 + dy**2)
        vx, vy = 0., 0.
        if distance > 0:
            dx /= distance
            dy /= distance
            influence_strength = 0.3
            vx = (1 - influence_strength) * self.vx + influence_strength * dx * current_speed
            vy = (1 - influence_strength) * self.vy + influence_strength * dy * current_speed
        return vx, vy

    def _move_random(self):
        """Randomly change direction with small angle adjustments (±20 degrees)."""        
        max_angle_change = math.radians(10)
        angle_change = random.uniform(-max_angle_change, max_angle_change)
        
        current_angle = math.atan2(self.vy, self.vx)
        new_angle = current_angle + angle_change
        
        speed = math.sqrt(self.vx**2 + self.vy**2)
        new_speed = max(0.5, speed * random.uniform(0.9, 1.1))        
        vx = math.cos(new_angle) * new_speed
        vy = math.sin(new_angle) * new_speed
        return vx, vy

    def _move_llm(self, universe_state: dict) -> None:
        vx, vy = llm_based_cell_movement(universe_state, self.state)
        return vx, vy
