from __future__ import annotations

import random
import json
from uuid import uuid4, UUID
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any


@dataclass
class Food:
    id: UUID
    energy: float
    position: Tuple[float, float]

    def degrade(self, factor: float = 0.95) -> None:
        """Reduce energy by a degradation factor each cycle."""
        self.energy *= factor
        if self.energy < 0.01:
            self.energy = 0.0


@dataclass
class Venom:
    id: UUID
    toxicity: float
    position: Tuple[float, float]

    def degrade(self, factor: float = 0.90) -> None:
        """Reduce toxicity by a degradation factor each cycle."""
        self.toxicity *= factor
        if self.toxicity < 0.01:
            self.toxicity = 0.0


class Universe:
    """
    Converts incoming energy into Food and Venom instances.
    Each Food/Venom chunk is >= 1.0 of its measure.
    Food stores 'energy'; Venom stores 'toxicity' (energy * factor).
    """

    def __init__(
        self,
        initial_energy: float,
        ratio: float,
        waste_factor: float = 0.95,
        width: float = 100.0,
        height: float = 100.0,
        venom_energy_to_toxicity: float = 1.0,
        food_degrade_factor: float = 0.95,
        venom_degrade_factor: float = 0.90,
        cleanup_depleted: bool = True,
    ):
        assert 0.0 <= ratio <= 1.0, "ratio must be in [0, 1]"
        assert width > 0 and height > 0, "Universe dimensions must be positive"

        self.energy = initial_energy
        self.ratio = ratio
        self.waste_factor = waste_factor
        self.width = width
        self.height = height
        self.venom_energy_to_toxicity = venom_energy_to_toxicity
        self.food_degrade_factor = food_degrade_factor
        self.venom_degrade_factor = venom_degrade_factor
        self.cleanup_depleted = cleanup_depleted

        self.foods: List[Food] = []
        self.venoms: List[Venom] = []
        self.agents: List[object] = []

    def add_food(self, food: Food) -> None:
        self.foods.append(food)

    def add_venom(self, venom: Venom) -> None:
        self.venoms.append(venom)

    def add_agent(self, agent: object) -> None:
        self.agents.append(agent)

    def run(self, input_energy: float) -> Tuple[List[Food], List[Venom]]:
        """
        One simulation step:
          1) apply waste + jitter to input_energy
          2) split into food / venom pools
          3) partition into >=1.0 chunks and instantiate objects
          4) degrade all existing foods & venoms
        Returns (foods_created, venoms_created).
        """
        # 1) apply waste + jitter
        usable_energy = input_energy * self.waste_factor * random.uniform(0.8, 0.99)
        energy_for_food = usable_energy * self.ratio
        energy_for_venom = usable_energy * (1.0 - self.ratio)

        # 2) partition
        food_chunks = self._random_partition(energy_for_food, min_unit=1.0)
        venom_chunks = self._random_partition(energy_for_venom, min_unit=1.0)

        # 3) instantiate
        foods_created = self._create_foods(food_chunks)
        venoms_created = self._create_venoms(venom_chunks)

        # accumulate raw input into universe energy (if you track it)
        self.energy += input_energy

        # 4) degrade existing items (including newly created this step)
        self.degrade_all()

        return foods_created, venoms_created

    def degrade_all(self) -> None:
        """Apply degradation to all foods and venoms."""
        for food in self.foods:
            food.degrade(self.food_degrade_factor)
        for venom in self.venoms:
            venom.degrade(self.venom_degrade_factor)

        if self.cleanup_depleted:
            self.foods = [f for f in self.foods if f.energy > 0.0]
            self.venoms = [v for v in self.venoms if v.toxicity > 0.0]

    def get_state(self) -> Dict[str, Any]:
        """Return current state as a Python dict (IDs stringified)."""
        return {
            "energy": self.energy,
            "foods": [
                {"id": str(f.id), "energy": f.energy, "position": f.position}
                for f in self.foods
            ],
            "venoms": [
                {"id": str(v.id), "toxicity": v.toxicity, "position": v.position}
                for v in self.venoms
            ],
            "agents": [
                {"id": getattr(a, "id", None), "position": getattr(a, "position", None)}
                for a in self.agents
            ],
            "config": {
                "ratio": self.ratio,
                "waste_factor": self.waste_factor,
                "venom_energy_to_toxicity": self.venom_energy_to_toxicity,
                "food_degrade_factor": self.food_degrade_factor,
                "venom_degrade_factor": self.venom_degrade_factor,
                "cleanup_depleted": self.cleanup_depleted,
                "bounds": (self.width, self.height),
            },
        }

    def to_json(self) -> str:
        """Return state as pretty JSON."""
        return json.dumps(self.get_state(), indent=2)

    def _random_partition(self, total: float, min_unit: float = 1.0) -> List[float]:
        """
        Randomly split 'total' into N parts, each >= min_unit.
        If total < min_unit: returns [].

        Strategy:
          1) Choose N uniformly in [1, floor(total / min_unit)].
          2) Allocate base = N * min_unit (guarantees minimum).
          3) Distribute remainder across N parts with random weights.
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

        cuts = sorted(random.random() for _ in range(n - 1))
        weights = []
        last = 0.0
        for c in cuts:
            weights.append(c - last)
            last = c
        weights.append(1.0 - last)

        chunks = [b + rem * w for b, w in zip(base, weights)]
        random.shuffle(chunks)
        return chunks

    def _rand_position(self) -> Tuple[float, float]:
        return (random.uniform(0.0, self.width), random.uniform(0.0, self.height))

    def _create_foods(self, energy_chunks: List[float]) -> List[Food]:
        foods = [
            Food(id=uuid4(), energy=e, position=self._rand_position())
            for e in energy_chunks
        ]
        self.foods.extend(foods)
        return foods

    def _create_venoms(self, energy_chunks: List[float]) -> List[Venom]:
        venoms = [
            Venom(
                id=uuid4(),
                toxicity=e * self.venom_energy_to_toxicity,
                position=self._rand_position(),
            )
            for e in energy_chunks
        ]
        self.venoms.extend(venoms)
        return venoms


if __name__ == "__main__":
    random.seed(42)

    universe = Universe(
        initial_energy=0.0,
        ratio=0.6,
        waste_factor=0.95,
        width=200.0,
        height=120.0,
        venom_energy_to_toxicity=1.5,
        food_degrade_factor=0.96,   # tweak as you like
        venom_degrade_factor=0.92,  # tweak as you like
        cleanup_depleted=True,
    )

    for i in range(1, 101):
        input_energy = random.uniform(25.0, 50.0)
        foods_new, venoms_new = universe.run(input_energy)
        print(
            f"Cycle {i:03d}: +{input_energy:.2f} → "
            f"{len(foods_new)} new foods, {len(venoms_new)} new venoms | "
            f"totals: foods={len(universe.foods)}, venoms={len(universe.venoms)}"
        )

    print("\nFinal state (summary):")
    print(f"Total energy tracked: {universe.energy:.2f}")
    print(f"Foods alive: {len(universe.foods)} | Venoms alive: {len(universe.venoms)}")
    # Uncomment for full JSON:
    # print(universe.to_json())