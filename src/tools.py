import math
import random


def distance_to(self_position: tuple[float, float], target_position: tuple[float, float]) -> float:
    """Calculate distance to target position."""
    x1, y1 = self_position
    x2, y2 = target_position
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def mutate_color(color, mutation_rate: float = 0.95, mutation_strength: float = 0.8) -> tuple[float, float, float]:
    """Mutate only the green channel with some probability,
       otherwise inherit parent's color."""
    if random.random() > mutation_rate:
        return color
    
    r, g, b = color
    g = max(0.0, min(1.0, g + random.uniform(-mutation_strength, mutation_strength)))
    return (r, g, b)
