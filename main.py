from uuid import UUID, uuid4

from strands import Agent

from dataclasses import dataclass


@dataclass
class Food:
    id: UUID
    energy: float
    position: tuple[float, float]


@dataclass
class Venom:
    id: UUID
    toxicity: float
    position: tuple[float, float]


class Universe:

    def __init__(self, initial_energy: float):
        self.energy = initial_energy
        self.foods: list[Food] = []
        self.venoms: list[Venom] = []
        self.agents = []

    def add_food(self, food: Food):
        self.foods.append(food)

    def add_venom(self, venom: Venom):
        self.venoms.append(venom)

    def add_agent(self, agent):
        self.agents.append(agent)



class UniverseCycle:

    def __init__(self, input_energy: float, split_ratio: float):
        self.energy = input_energy
        self.split_ratio = split_ratio

    @property
    def food_energy(self) -> float:
        return self.energy * self.split_ratio

    @property
    def venom_energy(self) -> float:
        return self.energy * (1 - self.split_ratio)

    def run(self, universe: Universe):
        universe.energy += self.input_energy





def main():
    # Create an agent with default settings
    agent = Agent()

    # Ask the agent a question
    agent("Tell me about agentic AI")


if __name__ == "__main__":
    main()
