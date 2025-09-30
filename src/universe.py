from __future__ import annotations

import json
import random
from uuid import uuid4
from typing import List, Tuple, Dict, Any, Optional, DefaultDict
from collections import defaultdict

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
        width: float = 1000.0,  # Larger default for better spatial partitioning
        height: float = 1000.0,
        venom_energy_to_toxicity: float = 1.0,
        food_degrade_factor: float = 0.78,
        venom_degrade_factor: float = 0.80,
        cleanup_depleted: bool = True,

        # spawn controls
        max_new_foods: int = 6,
        max_new_venoms: int = 6,
        min_unit_food: float = 1.0,
        min_unit_venom: float = 1.0,

        # performance limits
        max_cells: int = 500,  # Maximum number of cells before simulation slows
        cell_check_radius: float = 100.0,  # Only check nearby cells/food/venom

        # cell boundary handling
        boundary_mode: str = "bounce",
        bounce_restitution: float = 0.8,
    ):
        assert 0.0 <= ratio <= 1.0, "ratio must be in [0, 1]"
        assert width > 0 and height > 0, "Universe dimensions must be positive"

        # world config
        self.width = width
        self.height = height
        self.boundary_mode = boundary_mode
        self.bounce_restitution = bounce_restitution

        # performance settings
        self.max_cells = max_cells
        self.cell_check_radius = cell_check_radius
        self.cell_check_radius2 = cell_check_radius * cell_check_radius

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

        # state
        self.foods: List[Food] = []
        self.venoms: List[Venom] = []
        self.cells: List[Cell] = []

        # Spatial partitioning for performance
        self._spatial_grid: DefaultDict[Tuple[int, int], List[Cell]] = defaultdict(list)
        self._grid_cell_size = 100.0  # Size of each grid cell
        
    def add_cell(self, agent: Cell) -> None:
        self.cells.append(agent)

    def add_food(self, food: Food) -> None:
        self.foods.append(food)

    def add_venom(self, venom: Venom) -> None:
        self.venoms.append(venom)

    def run(self, input_energy: float, cycle_count: int) -> tuple[List[Food], List[Venom], List[Cell]]:
        """Optimized simulation step with spatial partitioning."""
        
        # Update spatial grid at start of cycle
        self._update_spatial_grid()
        
        offspring: List[Cell] = []
        foods_created: List[Food] = []
        venoms_created: List[Venom] = []
        
        # Process cells with performance optimization
        cell_count = len(self.cells)
        if cell_count > self.max_cells * 0.8:
            # Slow down when approaching limit
            process_every_n = max(1, cell_count // (self.max_cells // 2))
        else:
            process_every_n = 1

        for i, cell in enumerate(list(self.cells)):
            if i % process_every_n == 0:  # Skip some cells when population is high
                child = cell.run()
                self._apply_bounds(cell)
                self._interact_partial(cell)
                if child is not None and len(self.cells) < self.max_cells:
                    self._apply_bounds(child)
                    self._interact_partial(child)
                    offspring.append(child)

        # Add offspring if under limit
        if offspring and len(self.cells) + len(offspring) <= self.max_cells:
            self.cells.extend(offspring)

        # Add resources every 50 cycles
        if cycle_count % 50 == 0 and len(self.cells) < self.max_cells:
            usable = input_energy * self.waste_factor * random.uniform(0.8, 0.99)
            ef = usable * self.ratio
            ev = usable * (1.0 - self.ratio)
            foods_created = self._create_foods(self._random_partition(ef, self.min_unit_food, self.max_new_foods))
            venoms_created = self._create_venoms(self._random_partition(ev, self.min_unit_venom, self.max_new_venoms))
            self.energy += input_energy

        # Cleanup
        self.degrade_all()
        if self.cleanup_depleted:
            self.cells = [c for c in self.cells if c.energy > 0.0]
            self.foods = [f for f in self.foods if f.energy > 0.0]
            self.venoms = [v for v in self.venoms if v.toxicity > 0.0]

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

    def _apply_bounds(self, cell: Cell) -> None:
        """Keep a cell inside bounds by bouncing or wrapping and update velocity if bouncing."""
        x, y = cell.position
        vx = getattr(cell, "vx", 0.0)
        vy = getattr(cell, "vy", 0.0)

        if self.boundary_mode == "wrap":
            if x < 0.0:
                x += self.width
            elif x > self.width:
                x -= self.width

            if y < 0.0:
                y += self.height
            elif y > self.height:
                y -= self.height

        else:
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

    def _nearest_food_within(self, cell: Cell) -> Optional[int]:
        """Find nearest food that is touching the cell (surface-to-surface)."""
        cell_radius = cell.diameter / 2.0
        best_i, best_distance = None, float('inf')
        
        for i, food in enumerate(self.foods):
            if food.energy <= 0:
                continue
                
            # Calculate distance between centers
            distance = _dist2(cell.position, food.position) ** 0.5
            
            # Food radius based on its energy (since diameter = energy)
            food_radius = food.energy / 2.0
            
            # Check if surfaces are touching or overlapping
            if distance <= (cell_radius + food_radius):
                if distance < best_distance:
                    best_distance = distance
                    best_i = i
        
        return best_i

    def _nearest_venom_within(self, cell: Cell) -> Optional[int]:
        """Find nearest venom that is touching the cell (surface-to-surface)."""
        cell_radius = cell.diameter / 2.0
        best_i, best_distance = None, float('inf')
        
        for i, venom in enumerate(self.venoms):
            if venom.toxicity <= 0:
                continue
                
            # Calculate distance between centers
            distance = _dist2(cell.position, venom.position) ** 0.5
            
            # Venom radius based on its toxicity (since diameter = toxicity)
            venom_radius = venom.toxicity / 2.0
            
            # Check if surfaces are touching or overlapping
            if distance <= (cell_radius + venom_radius):
                if distance < best_distance:
                    best_distance = distance
                    best_i = i
        
        return best_i

    def _interact_partial(self, cell: Cell) -> None:
        """Optimized interaction checking only nearby objects."""
        if cell.energy <= 0.0:
            return

        # Get nearby objects
        nearby_foods = self._get_nearby_foods(cell.position)
        nearby_venoms = self._get_nearby_venoms(cell.position)
        
        cell_radius = cell.diameter / 2.0

        # Food interactions
        for food in nearby_foods:
            if food.energy > 0:
                distance = _dist2(cell.position, food.position) ** 0.5
                food_radius = food.energy / 2.0
                
                if distance <= (cell_radius + food_radius):
                    # Eating logic
                    cell_size_factor = min(cell.energy / (food.energy + 0.1), 2.0)
                    base_eat_rate = 0.1
                    eat_rate = base_eat_rate * cell_size_factor
                    
                    amt = min(food.energy * eat_rate, food.energy)
                    food.energy -= amt
                    cell.energy += amt
                    
                    if food.energy <= 0.01:
                        food.energy = 0.0

        # Venom interactions
        for venom in nearby_venoms:
            if venom.toxicity > 0:
                distance = _dist2(cell.position, venom.position) ** 0.5
                venom_radius = venom.toxicity / 2.0
                
                if distance <= (cell_radius + venom_radius):
                    # Poisoning logic
                    venom_potency = venom.toxicity / (cell.energy + 0.1)
                    base_poison_rate = 0.09
                    poison_rate = base_poison_rate * venom_potency
                    
                    dmg = min(venom.toxicity * poison_rate, venom.toxicity)
                    venom.toxicity -= dmg * 0.4
                    cell.energy -= dmg
                    
                    if venom.toxicity <= 0.01:
                        venom.toxicity = 0.0
                    if cell.energy <= 0.0:
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

    def _get_grid_key(self, position: Tuple[float, float]) -> Tuple[int, int]:
        """Convert position to grid coordinates."""
        x, y = position
        grid_x = int(x // self._grid_cell_size)
        grid_y = int(y // self._grid_cell_size)
        return (grid_x, grid_y)

    def _update_spatial_grid(self):
        """Update the spatial partitioning grid."""
        self._spatial_grid.clear()
        for cell in self.cells:
            if cell.energy > 0:
                key = self._get_grid_key(cell.position)
                self._spatial_grid[key].append(cell)

    def _get_nearby_cells(self, position: Tuple[float, float]) -> List[Cell]:
        """Get cells near a position using spatial partitioning."""
        center_key = self._get_grid_key(position)
        nearby_cells = []
        
        # Check 3x3 grid around the position
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                check_key = (center_key[0] + dx, center_key[1] + dy)
                if check_key in self._spatial_grid:
                    for cell in self._spatial_grid[check_key]:
                        # Check actual distance
                        if _dist2(position, cell.position) <= self.cell_check_radius2:
                            nearby_cells.append(cell)
        
        return nearby_cells

    def _get_nearby_foods(self, position: Tuple[float, float]) -> List[Food]:
        """Get foods near a position."""
        nearby_foods = []
        for food in self.foods:
            if food.energy > 0 and _dist2(position, food.position) <= self.cell_check_radius2:
                nearby_foods.append(food)
        return nearby_foods

    def _get_nearby_venoms(self, position: Tuple[float, float]) -> List[Venom]:
        """Get venoms near a position."""
        nearby_venoms = []
        for venom in self.venoms:
            if venom.toxicity > 0 and _dist2(position, venom.position) <= self.cell_check_radius2:
                nearby_venoms.append(venom)
        return nearby_venoms
