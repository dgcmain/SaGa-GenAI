import random

from strands import Agent, tool
from strands.models import BedrockModel
# from strands_tools import calculator, current_time


@tool
def euclidean_distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """
    Calculates the Euclidean distance between two points in 2D space.
    Args:
        p1 (tuple[float, float]): The first point as a tuple of (x, y) coordinates.
        p2 (tuple[float, float]): The second point as a tuple of (x, y) coordinates.
    Returns:
        float: The Euclidean distance between p1 and p2.
    Example:
        >>> euclidean_distance((0, 0), (3, 4))
        5.0
    """

    return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5


def llm_based_cell_movement(universe_state: dict[str, any], cell_state: dict[str, any]) -> dict:
    
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
        tools=[euclidean_distance],
    )

    # Ask the agent a question that uses the available tools
    message = f"""
    You are a biological cell in a 2D universe. You have the following state:
    Cell State: {cell_state}
    Universe State: {universe_state}

    Based on your current state and the universe state, decide your next velocity
    as a tuple (vx, vy) where vx and vy are floats representing the velocity x and y coordinates.
    Your objective is to find food and avoid venom, and get the food before your energy runs out and others eat it
    Example: If your current position is (100, 150) and you decide to move right
    by 5 and up by 3, you should respond with (5.0, 3.0).
    You need to calculate the Euclidean distance to nearby food and venom.

    Respond only with the tuple (vx, vy) and nothing else.
    """
    response = agent(message)
    try:
        # Expecting a tuple (dx, dy)
        movement_str = response.message["content"][0]["text"].rsplit('\n', 1)[-1]
        movement = eval(movement_str)
        if isinstance(movement, tuple) and len(movement) == 2:
            return movement
        else:
            print("Invalid response format. Expected a tuple (dx, dy).")
            return (0.0, 0.0)
    except Exception as e:
        print(f"Error parsing response: {e}, got response: {response}")
        # random_angle = random.uniform(0, 2 * math.pi)
        return (random.uniform(0, 2), random.uniform(0, 2))


