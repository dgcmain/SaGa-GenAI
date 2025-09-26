from __future__ import annotations

import random
from typing import Any
from uuid import uuid4, UUID
from dataclasses import dataclass
import matplotlib.pyplot as plt

from strands import Agent, tool
from strands_tools import calculator, current_time
from strands.models import BedrockModel

from cell import Cell
from universe import Universe
from render import Renderer


@tool
def update_universe(universe_state: dict, cell_state: dict) -> tuple[float, float]:
    """Update the universe based on the cell's state and return food and venom consumed."""



@tool
def euclidean_distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5


def _get_cell_movement(universe_state: dict[str, Any], cell_state: dict[str, Any]) -> dict:
    # Create a BedrockModel
    bedrock_model = BedrockModel(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        region_name="us-west-2",
        temperature=0.3,
    )

    # Create an agent with tools from the community-driven strands-tools package
    # as well as our custom letter_counter tool
    agent = Agent(
        model=bedrock_model,
        tools=[euclidean_distance, update_universe],
    )

    # Ask the agent a question that uses the available tools
    message = f"""
    You are a biological cell in a 2D universe. You have the following state:
    Cell State: {cell_state}
    Universe State: {universe_state}

    Based on your current state and the universe state, decide your next movement velocity
    as a tuple (vx, vy) where vx and vy are floats representing the velocity in change in x and y coordinates.
    Ensure that your new position remains within the universe bounds defined by width and height.

    Example: If your current position is (100, 150) and you decide to move right
    by 5 and up by 3, you should respond with (5.0, 3.0).
    You need to calculate the Euclidean distance to nearby food and venom.

    You like food, but you avoid venom. If you are close to food, move towards it.
    If you are close to venom, move away from it.
    Consider your energy level: if it's low, prioritize moving towards food.
    If it's high, you can afford to explore more.

    Respond only with the tuple (vx, vy) and nothing else.
    """
    response = agent(message)
    try:
        movement_str = response.message["content"][0]["text"].rsplit('\n', 1)[-1] # Expecting a tuple (dx, dy)
        movement = eval(movement_str)
        if isinstance(movement, tuple) and len(movement) == 2:
            return movement
        else:
            print("Invalid response format. Expected a tuple (dx, dy).")
            return (0.0, 0.0)
    except Exception as e:
        print(f"Error parsing response: {e}, got response: {response}")
        return (0.0, 0.0)


def get_cell_state(cell: Cell) -> dict:
    return {
        "id": str(cell.id),
        "energy": cell.energy,
        "position": cell.position,
    }


if __name__ == "__main__":
    random.seed(42)
    universe = Universe(
        initial_energy=0.0,
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
    for _ in range(2):
        universe.add_cell(
            Cell(
                id=uuid4(),
                energy=random.uniform(1.0, 10.0),
                position=(random.uniform(0, universe.width),
                        random.uniform(0, universe.height)))
        )

    print("Initial state (summary):")
    print(f"Total energy tracked: {universe.energy:.2f}")
    print(f"Foods alive: {len(universe.foods)} | Venoms alive: {len(universe.venoms)}")

    renderer = Renderer()
    renderer.start(universe)

    for i in range(1, 101):
        universe.run(random.uniform(5.0, 12.0))
        renderer.update(universe, cycle_idx=i)

        universe_state = universe.get_state()
        for cell in universe.cells:
            cell_state = get_cell_state(cell=cell)
            new_velocity = _get_cell_movement(universe_state=universe_state, cell_state=cell_state)
            print(f"Cell {cell.id} moving from {cell.position} with {new_velocity}.")
            # cell.update_velocity(new_velocity)
            cell.run()

    print("\nFinal state (summary):")
    print(f"Total energy tracked: {universe.energy:.2f}")
    print(f"Foods alive: {len(universe.foods)} | Venoms alive: {len(universe.venoms)}")

    plt.show()