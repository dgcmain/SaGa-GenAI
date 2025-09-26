from __future__ import annotations

import json
import random
from uuid import uuid4
from typing import List, Tuple, Dict, Any, Optional

from entities import Food, Venom
from cell import Cell
from tools import _dist2

class Universe:
    """
    Simulation universe:
      A) Cells run (move/grow/decay/reproduce) and interact via touch with Food/Venom
      B) Input energy -> Food/Venom spawning (random partitions, min unit, max parts)
      C) Food/Venom degrade and cleanup (and dead cells removed)
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

        # spawn controls
        max_new_foods: int = 6,
        max_new_venoms: int = 6,
        min_unit_food: float = 1.0,
        min_unit_venom: float = 1.0,

        # cell boundary handling
        boundary_mode: str = "bounce",   # "bounce" or "wrap"
        bounce_restitution: float = 0.8, # speed kept after bounce

        # touch interactions (partial transfer per cycle)
        touch_radius_food: float = 10.0,
        touch_radius_venom: float = 10.0,
        food_transfer_fraction: float = 0.25,   # fraction of food energy transferred
        venom_transfer_fraction: float = 0.25,  # fraction of venom toxicity applied
        food_transfer_cap: float = 2.0,         # max energy transferred per touch/cycle
        venom_transfer_cap: float = 2.0,        # max damage per touch/cycle
    ):
        assert 0.0 <= ratio <= 1.0, "ratio must be in [0, 1]"
        assert width > 0 and height > 0, "Universe dimensions must be positive"
        assert boundary_mode in ("bounce", "wrap"), "boundary_mode must be 'bounce' or 'wrap'"

        # world config
        self.width = width
        self.height = height
        self.boundary_mode = boundary_mode
        self.bounce_restitution = bounce_restitution

        # energy pipeline
        self.energy = initial_energy
        self.ratio = ratio
        self.waste_factor = waste_factor
        self.venom_energy_to_toxicity = venom_energy_to_toxicity

        # resource degradation
        self.food_degrade_factor = food_degrade_factor
        self.venom_degrade_factor = venom_degrade_factor
        self.cleanup_depleted = cleanup_depleted

        # spawn knobs
        self.max_new_foods = max_new_foods
        self.max_new_venoms = max_new_venoms
        self.min_unit_food = min_unit_food
        self.min_unit_venom = min_unit_venom

        # interactions
        self.touch_radius_food2 = touch_radius_food * touch_radius_food
        self.touch_radius_venom2 = touch_radius_venom * touch_radius_venom
        self.food_transfer_fraction = food_transfer_fraction
        self.venom_transfer_fraction = venom_transfer_fraction
        self.food_transfer_cap = food_transfer_cap
        self.venom_transfer_cap = venom_transfer_cap

        # state
        self.foods: List[Food] = []
        self.venoms: List[Venom] = []
        self.cells: List[Cell] = []

    # ---- Public API ----
    def add_cell(self, agent: Cell) -> None:
        self.cells.append(agent)

    def add_food(self, food: Food) -> None:
        self.foods.append(food)

    def add_venom(self, venom: Venom) -> None:
        self.venoms.append(venom)

    def run(self, input_energy: float) -> tuple[List[Food], List[Venom], List[Cell]]:
        """
        One simulation step:
          A) Update cells (move/grow/decay/reproduce), apply bounds, partial touch interactions
          B) Spawn Food/Venom from input energy
          C) Degrade resources & cleanup
        Returns (foods_created, venoms_created, offspring_created)
        """
        # ---- A) cells update & interactions ----
        offspring: List[Cell] = []
        for cell in list(self.cells):  # iterate over a copy in case we append children
            child = cell.run()
            self._apply_bounds(cell)
            self._interact_partial(cell)
            if child is not None:
                self._apply_bounds(child)
                self._interact_partial(child)
                offspring.append(child)

        if offspring:
            self.cells.extend(offspring)
            self.cells.extend(offspring)

        # Drop dead cells and depleted resources before spawning
        if self.cleanup_depleted:
            self.cells = [c for c in self.cells if c.energy > 0.0]
            self.foods  = [f for f in self.foods if f.energy > 0.0]
            self.venoms = [v for v in self.venoms if v.toxicity > 0.0]

        # ---- B) input energy -> spawn ----
        usable = input_energy * self.waste_factor * random.uniform(0.8, 0.99)
        ef = usable * self.ratio
        ev = usable * (1.0 - self.ratio)

        foods_created  = self._create_foods(self._random_partition(ef, self.min_unit_food,  self.max_new_foods))
        venoms_created = self._create_venoms(self._random_partition(ev, self.min_unit_venom, self.max_new_venoms))

        self.energy += input_energy

        # ---- C) degrade resources & cleanup ----
        self.degrade_all()

        return foods_created, venoms_created, offspring

    def degrade_all(self) -> None:
        for f in self.foods:
            f.degrade(self.food_degrade_factor)
        for v in self.venoms:
            v.degrade(self.venom_degrade_factor)
        if self.cleanup_depleted:
            self.foods  = [f for f in self.foods  if f.energy   > 0.0]
            self.venoms = [v for v in self.venoms if v.toxicity > 0.0]

    def get_state(self) -> dict[str, Any]:
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
            "cells": [
                {
                    "id": str(a.id),
                    "energy": a.energy,
                    "position": a.position,
                    "velocity": (getattr(a, "vx", 0.0), getattr(a, "vy", 0.0)),
                }
                for a in self.cells
            ],
            "config": {
                "bounds": (self.width, self.height),
                "boundary_mode": self.boundary_mode,
                "bounce_restitution": self.bounce_restitution,
                "ratio": self.ratio,
                "waste_factor": self.waste_factor,
                "venom_energy_to_toxicity": self.venom_energy_to_toxicity,
                "food_degrade_factor": self.food_degrade_factor,
                "venom_degrade_factor": self.venom_degrade_factor,
                "cleanup_depleted": self.cleanup_depleted,
                "max_new_foods": self.max_new_foods,
                "max_new_venoms": self.max_new_venoms,
                "min_unit_food": self.min_unit_food,
                "min_unit_venom": self.min_unit_venom,
                "touch_radius_food": (self.touch_radius_food2 ** 0.5),
                "touch_radius_venom": (self.touch_radius_venom2 ** 0.5),
                "food_transfer_fraction": self.food_transfer_fraction,
                "venom_transfer_fraction": self.venom_transfer_fraction,
                "food_transfer_cap": self.food_transfer_cap,
                "venom_transfer_cap": self.venom_transfer_cap,
            },
        }

    def to_json(self) -> str:
        return json.dumps(self.get_state(), indent=2)

    # ---- Internals ----

    def _apply_bounds(self, cell: Cell) -> None:
        """Keep a cell inside bounds by bouncing or wrapping and update velocity if bouncing."""
        x, y = cell.position
        vx = getattr(cell, "vx", 0.0)
        vy = getattr(cell, "vy", 0.0)

        if self.boundary_mode == "wrap":
            if x < 0.0:         x += self.width
            elif x > self.width: x -= self.width
            if y < 0.0:          y += self.height
            elif y > self.height: y -= self.height
        else:  # bounce
            if x < 0.0:
                x = 0.0
                vx = abs(vx) * self.bounce_restitution
            elif x > self.width:
                x = self.width
                vx = -abs(vx) * self.bounce_restitution

            if y < 0.0:
                y = 0.0
                vy = abs(vy) * self.bounce_restitution
            elif y > self.height:
                y = self.height
                vy = -abs(vy) * self.bounce_restitution

        cell.position = (x, y)
        if hasattr(cell, "vx"): cell.vx = vx
        if hasattr(cell, "vy"): cell.vy = vy

    def _nearest_food_within(self, pos: Tuple[float, float]) -> Optional[int]:
        best_i, best_d2 = None, self.touch_radius_food2
        for i, f in enumerate(self.foods):
            d2 = _dist2(pos, f.position)
            if d2 <= best_d2:
                best_d2 = d2
                best_i = i
        return best_i

    def _nearest_venom_within(self, pos: Tuple[float, float]) -> Optional[int]:
        best_i, best_d2 = None, self.touch_radius_venom2
        for i, v in enumerate(self.venoms):
            d2 = _dist2(pos, v.position)
            if d2 <= best_d2:
                best_d2 = d2
                best_i = i
        return best_i

    def _interact_partial(self, cell: Cell) -> None:
        """Transfer a capped fraction from the nearest food and venom within touch radius."""
        if cell.energy <= 0.0:
            return

        # Food → cell (gain some)
        fi = self._nearest_food_within(cell.position)
        if fi is not None:
            food = self.foods[fi]
            if food.energy > 0.0:
                amt = min(food.energy * self.food_transfer_fraction, self.food_transfer_cap)
                if amt > 0.0:
                    food.energy -= amt
                    cell.energy += amt

        # Venom → cell (lose some)
        vi = self._nearest_venom_within(cell.position)
        if vi is not None:
            venom = self.venoms[vi]
            if venom.toxicity > 0.0:
                dmg = min(venom.toxicity * self.venom_transfer_fraction, self.venom_transfer_cap)
                if dmg > 0.0:
                    venom.toxicity -= dmg
                    cell.energy -= dmg
                    if cell.energy < 0.0:
                        cell.energy = 0.0

    def _random_partition(self, total: float, min_unit: float, max_parts_cap: int) -> List[float]:
        """Randomly split 'total' into N parts >= min_unit, with N <= max_parts_cap."""
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

        # Dirichlet-like weights (no numpy)
        cuts = sorted(random.random() for _ in range(n - 1))
        weights: List[float] = []
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
