from typing import Optional
from cell import Cell

from strands import Agent, tool
from strands_tools import calculator, current_time
from strands.models import BedrockModel

@tool
def update_universe(universe_state: dict, cell_state: dict) -> tuple[float, float]:
    """Update the universe based on the cell's state and return food and venom consumed."""


@tool
def euclidean_distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5


def _get_cell_movement(universe_state: dict[str, any], cell_state: dict[str, any]) -> dict:
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





def _dist2(a: tuple[float, float], b: tuple[float, float]) -> float:
    dx, dy = a[0]-b[0], a[1]-b[1]
    return dx*dx + dy*dy


def _nearest_food_within(self, pos: tuple[float, float]) -> Optional[int]:
    best_i, best_d2 = None, self.touch_radius_food2
    for i, f in enumerate(self.foods):
        d2 = _dist2(pos, f.position)
        if d2 <= best_d2:
            best_d2 = d2
            best_i = i
    return best_i


def _nearest_venom_within(self, pos: tuple[float, float]) -> Optional[int]:
    best_i, best_d2 = None, self.touch_radius_venom2
    for i, v in enumerate(self.venoms):
        d2 = _dist2(pos, v.position)
        if d2 <= best_d2:
            best_d2 = d2
            best_i = i
    return best_i


def _interact_partial(self, cell: Cell) -> None:
    """Transfer a fraction (capped) from the nearest food & venom within touch radius."""
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
