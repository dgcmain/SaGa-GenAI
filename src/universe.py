from __future__ import annotations

import math
import random
from uuid import uuid4, UUID
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Food:
    id: UUID
    energy: float
    position: Tuple[float, float]


@dataclass
class Venom:
    id: UUID
    toxicity: float
    position: Tuple[float, float]


class Universe:
    """
    A simple world that converts incoming energy into Food and Venom instances.

    - Each Food/Venom chunk must be >= 1.0 of its respective measure.
    - Food stores 'energy'; Venom stores 'toxicity' (derived from its energy chunk via a factor).
    """

    def __init__(
        self,
        initial_energy: float,
        ratio: float,
        waste_factor: float = 0.95,
        width: float = 100.0,
        height: float = 100.0,
        venom_energy_to_toxicity: float = 1.0,
    ):
        assert 0.0 <= ratio <= 1.0, "ratio must be in [0, 1]"
        assert width > 0 and height > 0, "Universe dimensions must be positive"

        self.energy = initial_energy
        self.ratio = ratio
        self.waste_factor = waste_factor
        self.width = width
        self.height = height
        self.venom_energy_to_toxicity = venom_energy_to_toxicity

        self.foods: List[Food] = []
        self.venoms: List[Venom] = []
        self.agents: List[object] = []

    def add_food(self, food: Food) -> None:
        self.foods.append(food)

    def add_venom(self, venom: Venom) -> None:
        self.venoms.append(venom)

    def add_agent(self, agent: object) -> None:
        self.agents.append(agent)

    def energy_update(self, incoming_energy: float) -> Tuple[List[Food], List[Venom]]:
        """
        Convert incoming energy into lists of Food and Venom objects.
        Returns (foods_created, venoms_created).
        """
        # Apply waste and efficiency jitter
        usable_energy = incoming_energy * self.waste_factor * random.uniform(0.8, 0.99)
        energy_for_food = usable_energy * self.ratio
        energy_for_venom = usable_energy * (1.0 - self.ratio)

        # Partition both energy pools into >= 1.0 chunks
        food_chunks = self._random_partition(energy_for_food, min_unit=1.0)
        venom_chunks = self._random_partition(energy_for_venom, min_unit=1.0)

        # Create objects
        foods_created = self._create_foods(food_chunks)
        venoms_created = self._create_venoms(venom_chunks)

        # Track total energy in the universe if desired
        self.energy += incoming_energy

        return foods_created, venoms_created

    def _random_partition(self, total: float, min_unit: float = 1.0) -> List[float]:
        """
        Randomly split 'total' into N parts, each >= min_unit.
        If total < min_unit: returns [].

        Strategy:
          1) Choose N uniformly in [1, floor(total / min_unit)].
          2) Allocate 'base' = N * min_unit (guarantees minimum).
          3) Distribute 'rem' = total - base across N parts with random weights.
        """
        if total < min_unit:
            return []

        max_parts = int(total // min_unit)
        n = random.randint(1, max_parts)

        base = [min_unit] * n
        rem = total - (n * min_unit)

        if rem <= 1e-12:
            random.shuffle(base)
            return base
        
        cuts = sorted([random.random() for _ in range(n - 1)])
        weights = []
        last = 0.0
        for c in cuts:
            weights.append(c - last)
            last = c
        weights.append(1.0 - last)

        # Distribute remainder proportional to weights
        chunks = [b + rem * w for b, w in zip(base, weights)]
        random.shuffle(chunks)
        return chunks

    def _rand_position(self) -> Tuple[float, float]:
        return (random.uniform(0.0, self.width), random.uniform(0.0, self.height))

    def _create_foods(self, energy_chunks: List[float]) -> List[Food]:
        foods = []
        for e in energy_chunks:
            foods.append(
                Food(
                    id=uuid4(),
                    energy=e,
                    position=self._rand_position(),
                )
            )
        # Persist
        self.foods.extend(foods)
        return foods

    def _create_venoms(self, energy_chunks: List[float]) -> List[Venom]:
        venoms = []
        for e in energy_chunks:
            venoms.append(
                Venom(
                    id=uuid4(),
                    toxicity=e * self.venom_energy_to_toxicity,
                    position=self._rand_position(),
                )
            )
        # Persist
        self.venoms.extend(venoms)
        return venoms


class UniverseCycle:
    """
    Represents one cycle where some energy enters the universe and is transformed.
    """

    def __init__(self, input_energy: float, universe: Universe):
        assert input_energy >= 0.0, "input_energy must be non-negative"
        self.energy = input_energy
        self.universe = universe

    def run(self) -> Tuple[List[Food], List[Venom]]:
        """Perform one cycle; returns (foods_created, venoms_created)."""
        return self.universe.energy_update(self.energy)


def main():
    random.seed(42)

    universe = Universe(
        initial_energy=0.0,
        ratio=0.6,
        waste_factor=0.95,
        width=200.0,
        height=120.0,
        venom_energy_to_toxicity=1.5,
    )

    for i in range(1, 101):
        input_energy = random.uniform(25.0, 50.0)
        cycle = UniverseCycle(input_energy=input_energy, universe=universe)
        foods, venoms = cycle.run()

        print(f"Cycle {i:03d}: +{input_energy:.2f} energy "
              f"=> {len(foods)} foods, {len(venoms)} venoms")

    print("\n--- Final Universe State ---")
    print(f"Total energy accumulated: {universe.energy:.2f}")
    print(f"Total foods created: {len(universe.foods)}")
    print(f"Total venoms created: {len(universe.venoms)}")


if __name__ == "__main__":
    main()
