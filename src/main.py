from __future__ import annotations

import random
import time
from uuid import uuid4
import matplotlib.pyplot as plt

from cell import Cell
from entities import Food, Venom

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
        food_degrade_factor=0.998,
        venom_degrade_factor=0.998,
        cleanup_depleted=True,
        max_new_foods=3,
        max_new_venoms=2,
        min_unit_food=1.2,
        min_unit_venom=1.5,
    )

    # Add some agents to show on the plot
    for _ in range(5):
        universe.add_cell(
            Cell(
                id=uuid4(),
                energy=20.0,
                position=(random.uniform(0, universe.width),
                        random.uniform(0, universe.height)),
                basal_metabolism=0.02,  # Much lower metabolism for 30 FPS
                reproduction_probability=0.05,  # Lower reproduction rate
            )
        )

    
    # Add 5 initial foods
    for _ in range(5):
        universe.add_food(
            Food(
                id=uuid4(),
                energy=random.uniform(5.0, 15.0),  # Random energy between 5-15
                position=(random.uniform(0, universe.width),
                         random.uniform(0, universe.height))
            )
        )

    # Add 5 initial venoms
    for _ in range(5):
        universe.add_venom(
            Venom(
                id=uuid4(),
                toxicity=random.uniform(3.0, 8.0),  # Random toxicity between 3-8
                position=(random.uniform(0, universe.width),
                         random.uniform(0, universe.height))
            )
        )


    print("Initial state (summary):")
    print(f"Total energy tracked: {universe.energy:.2f}")
    print(f"Foods alive: {len(universe.foods)} | Venoms alive: {len(universe.venoms)}")
    print(f"Cells alive: {len(universe.cells)}")

    renderer = Renderer()
    renderer.start(universe)

    # Real-time simulation parameters
    target_fps = 30
    frame_time = 1.0 / target_fps
    
    cycle_count = 0
    start_time = time.time()
    last_frame_time = start_time
    
    try:
        while not renderer.stopped:
            current_time_sim = time.time()
            elapsed = current_time_sim - last_frame_time
            
            if elapsed >= frame_time:
                cycle_count += 1
                
                # Increased input energy to sustain ecosystem
                universe.run(random.uniform(2.0, 5.0))
                
                # Update velocity less frequently
                if cycle_count % 20 == 0:  # Every 20 cycles (~0.67 seconds)
                    for cell in universe.cells:
                        new_velocity = (random.uniform(-1.5, 1.5), random.uniform(-1.5, 1.5))
                        cell.update_velocity(new_velocity)
                
                renderer.update(universe, cycle_idx=cycle_count)
                
                if cycle_count % 60 == 0:  # Print status every 2 seconds
                    print(f"Cycle {cycle_count}: Energy={universe.energy:.2f}, "
                          f"Foods={len(universe.foods)}, Venoms={len(universe.venoms)}, "
                          f"Cells={len(universe.cells)}")
                
                last_frame_time = current_time_sim
            else:
                time.sleep(0.001)
                
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
    
    print("\nFinal state (summary):")
    print(f"Total energy tracked: {universe.energy:.2f}")
    print(f"Foods alive: {len(universe.foods)} | Venoms alive: {len(universe.venoms)}")
    print(f"Cells alive: {len(universe.cells)}")

    plt.show()