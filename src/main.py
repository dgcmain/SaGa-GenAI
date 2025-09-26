from __future__ import annotations

import random
from uuid import uuid4

from entities import Agent
from universe import Universe
from render import Renderer

import matplotlib.pyplot as plt

if __name__ == "__main__":
    random.seed(42)

    universe = Universe(
        initial_energy=0.0,
        ratio=0.6,
        waste_factor=0.95,
        width=200.0,
        height=120.0,
        venom_energy_to_toxicity=1.5,
        food_degrade_factor=0.96,
        venom_degrade_factor=0.92,
        cleanup_depleted=True,
    )

    # Add some agents to show on the plot
    for _ in range(5):
        universe.add_agent(
            Agent(id=uuid4(),
                  position=(random.uniform(0, universe.width),
                            random.uniform(0, universe.height)))
        )

    renderer = Renderer()
    renderer.start(universe)

    for i in range(1, 101):
        universe.run(random.uniform(25.0, 50.0))
        renderer.update(universe, i)

    print("\nFinal state (summary):")
    print(f"Total energy tracked: {universe.energy:.2f}")
    print(f"Foods alive: {len(universe.foods)} | Venoms alive: {len(universe.venoms)}")

    plt.show()
