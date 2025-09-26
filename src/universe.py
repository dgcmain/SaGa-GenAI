from __future__ import annotations

import json
import random
from uuid import uuid4
from typing import List, Tuple, Dict, Any

from entities import Food, Venom, Agent


class Universe:
    """
    Converts incoming energy into Food and Venom instances.
    Each chunk is >= 1.0. Food stores 'energy'; Venom stores 'toxicity'.
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

        max_new_foods: int = 6,
        max_new_venoms: int = 6,
        min_unit_food: float = 1.0,
        min_unit_venom: float = 1.0,
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

        self.max_new_foods = max_new_foods
        self.max_new_venoms = max_new_venoms
        self.min_unit_food = min_unit_food
        self.min_unit_venom = min_unit_venom

        self.foods: List[Food] = []
        self.venoms: List[Venom] = []
        self.agents: List[Agent] = []

    # ---- Public API ----
    def add_agent(self, agent: Agent) -> None:
        self.agents.append(agent)

    def add_food(self, food: Food) -> None:
        self.foods.append(food)

    def add_venom(self, venom: Venom) -> None:
        self.venoms.append(venom)

    def run(self, input_energy: float) -> tuple[list[Food], list[Venom]]:
        """One step: waste+jitter → split → instantiate → degrade."""
        usable = input_energy * self.waste_factor * random.uniform(0.8, 0.99)
        ef = usable * self.ratio
        ev = usable * (1.0 - self.ratio)

        foods = self._create_foods(self._random_partition(ef, self.min_unit_food, self.max_new_foods))
        venoms = self._create_venoms(self._random_partition(ev, self.min_unit_venom, self.max_new_venoms))

        self.energy += input_energy
        self.degrade_all()
        return foods, venoms

    def degrade_all(self) -> None:
        for f in self.foods:
            f.degrade(self.food_degrade_factor)
        for v in self.venoms:
            v.degrade(self.venom_degrade_factor)
        if self.cleanup_depleted:
            self.foods = [f for f in self.foods if f.energy > 0.0]
            self.venoms = [v for v in self.venoms if v.toxicity > 0.0]

    def get_state(self) -> Dict[str, Any]:
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
                {"id": str(a.id), "position": a.position} for a in self.agents
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
        return json.dumps(self.get_state(), indent=2)

    # ---- Internals ----
    def _random_partition(self, total: float, min_unit: float, max_parts_cap: int) -> List[float]:
        if total < min_unit:
            return []
        max_parts_by_energy = int(total // min_unit)
        if max_parts_by_energy <= 0:
            return []
        max_parts = max(1, min(max_parts_by_energy, max_parts_cap))
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
        foods = [Food(id=uuid4(), energy=e, position=self._rand_position())
                 for e in energy_chunks]
        self.foods.extend(foods)
        return foods

    def _create_venoms(self, energy_chunks: List[float]) -> List[Venom]:
        venoms = [Venom(id=uuid4(),
                        toxicity=e * self.venom_energy_to_toxicity,
                        position=self._rand_position())
                  for e in energy_chunks]
        self.venoms.extend(venoms)
        return venoms
