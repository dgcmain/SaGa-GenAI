from uuid import uuid4, UUID

from strands import Agent, tool
from strands_tools import calculator, current_time
from strands.models import BedrockModel

class Agent:
    id: UUID
    energy: float
    position: tuple[float, float]

    def grow(self, amount: float) -> None:
        """Increase energy by a growth factor each cycle."""
        self.energy += amount
        if self.energy > 100.0:
            self.energy = 100.0

    def move(self, new_position: tuple[float, float]) -> None:
        """Update the agent's position."""
        self.position = new_position

    def shrink(self, amount: float) -> None:
        """Decrease energy by a shrinkage factor each cycle."""
        self.energy -= amount
        if self.energy < 0.0:
            self.energy = 0.0

    def consume(self, food) -> None:
        """Consume food to gain energy."""
        self.energy += food.energy
        food.energy = 0.0

    def die(self) -> None:
        """Handle the agent's death."""
        self.energy = 0.0
        self.position = (0.0, 0.0)

    def reproduce(self) -> 'Agent':
        """Create a new agent with half the energy."""
        offspring_energy = self.energy / 2
        self.energy /= 2
        return Agent(id=uuid4(), energy=offspring_energy, position=self.position)

    def degrade(self, factor: float = 0.98) -> None:
        """Reduce energy by a degradation factor each cycle."""
        self.energy *= factor
        if self.energy < 0.01:
            self.energy = 0.0


# Define a custom tool as a Python function using the @tool decorator
@tool
def letter_counter(word: str, letter: str) -> int:
    """
    Count occurrences of a specific letter in a word.

    Args:
        word (str): The input word to search in
        letter (str): The specific letter to count

    Returns:
        int: The number of occurrences of the letter in the word
    """
    if not isinstance(word, str) or not isinstance(letter, str):
        return 0

    if len(letter) != 1:
        raise ValueError("The 'letter' parameter must be a single character")

    return word.lower().count(letter.lower())


def main():
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
        tools=[calculator, current_time, letter_counter],
    )

    # Ask the agent a question that uses the available tools
    message = """
    I have 4 requests:

    1. What is the time right now?
    2. Calculate 3111696 / 74088
    3. Tell me how many letter R's are in the word "strawberry" 🍓
    """
    agent(message)


if __name__ == "__main__":
    main()