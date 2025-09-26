from uuid import uuid4

class Universe():

    def __init__(self, kwargs):
        self.uuid = uuid4()
        self.in_energy = kwargs.get('in_energy', 100)
        self.ratio_energy = kwargs.get('ratio_energy', 0.5)

        self.food_energy = self.ratio_energy * kwargs.get('food_ratio', 0.5)
        self.venom_energy = self.ratio_energy * (1 - kwargs.get('food_ratio', 0.5))
        
    def run(self):
        print(f"Running {self.uuid} with input energy {self.in_energy} and energy from food/venom {self.ratio_energy}" )
