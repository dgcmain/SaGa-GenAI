from __future__ import annotations

import random
# from typing import Any
# from uuid import uuid4, UUID
# from dataclasses import dataclass
import matplotlib.pyplot as plt

from cell import Cell
from universe import Universe
from render import Renderer


if __name__ == "__main__":
    random.seed(42)
    universe = Universe(
        initial_energy=7,
        ratio=0.6,
        waste_factor=0.95,
        width=1000.0,
        height=1200.0,
        venom_energy_to_toxicity=1.5,
        food_degrade_factor=0.5,
        venom_degrade_factor=0.70,
        cleanup_depleted=True,
        max_new_foods=4,
        max_new_venoms=3,
        min_unit_food=1.2,
        min_unit_venom=1.5,
    )

    # Add some agents to show on the plot
    for _ in range(5):
        universe.add_cell(
            Cell(
                id=uuid4(),
                # energy=random.uniform(1.0, 10.0),
                energy=20.0,
                position=(random.uniform(0, universe.width),
                        random.uniform(0, universe.height)))
        )

    print("Initial state (summary):")
    print(f"Total energy tracked: {universe.energy:.2f}")
    print(f"Foods alive: {len(universe.foods)} | Venoms alive: {len(universe.venoms)}")

    renderer = Renderer()
    renderer.start(universe)

    for i in range(1, 101):
        universe.run(random.uniform(1.0, 7.0))
        renderer.update(universe, cycle_idx=i)

        calculate_new_velocity = (i % 5 == 0)
        universe_state = universe.get_state()
        for cell in universe.cells:
            cell_state = cell._state()
            if calculate_new_velocity:
                new_velocity = (random.uniform(-1.0, 1.0), random.uniform(-1.0, 1.0))
                print(f"Cell {cell.id} moving from {cell.position} with {new_velocity}.")
                cell.update_velocity(new_velocity)
            offspring = cell.run()
            if offspring:
                universe.add_cell(offspring)
        print("=======================================================================")

    print("\nFinal state (summary):")
    print(f"Total energy tracked: {universe.energy:.2f}")
    print(f"Foods alive: {len(universe.foods)} | Venoms alive: {len(universe.venoms)}")

    plt.show()