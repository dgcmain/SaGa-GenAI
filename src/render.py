from __future__ import annotations
import math
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch, Circle
from matplotlib.path import Path
matplotlib.use("TkAgg")

from typing import Protocol, runtime_checkable, List, Sequence

from entities import Food, Venom
from cell import Cell


@runtime_checkable
class RenderableUniverse(Protocol):
    width: float
    height: float
    foods: List[Food]
    venoms: List[Venom]
    cells: List[Cell]


class Renderer:
    """
    Clean renderer where only cells have roughness.
    Food and venom are simple proportional circles.
    """

    def __init__(
        self,
        food_diameter_range: tuple[float, float] = (6.0, 20.0),   # Diameter range for food
        venom_diameter_range: tuple[float, float] = (8.0, 22.0),  # Diameter range for venom
        cell_roughness: float = 0.4,      # How rough cells look (0=smooth, 1=very rough)
        cell_stroke_width: float = 1.8,   # Width of cell borders
    ):
        self.fig = None
        self.ax = None
        self.food_patches: List[Circle] = []
        self.venom_patches: List[Circle] = []
        self.cell_patches: List[PathPatch] = []
        self._stopped = False

        self.food_diameter_range = food_diameter_range
        self.venom_diameter_range = venom_diameter_range
        self.cell_roughness = cell_roughness
        self.cell_stroke_width = cell_stroke_width

    def _diameter_from_value(self, value: float) -> float:
        return max(0.0, value)

    def _create_rough_circle(self, center: tuple[float, float], radius: float) -> Path:
        """Create a rough circle path for cells only."""
        x, y = center
        num_points = 10
        
        angles = np.linspace(0, 2 * np.pi, num_points)
        base_x = x + radius * np.cos(angles)
        base_y = y + radius * np.sin(angles)
        
        # Add roughness
        roughness = self.cell_roughness * radius * 0.1
        rough_x = base_x + np.random.uniform(-roughness, roughness, num_points)
        rough_y = base_y + np.random.uniform(-roughness, roughness, num_points)
        
        # Create polygon path
        vertices = np.column_stack([rough_x, rough_y])
        vertices = np.vstack([vertices, vertices[0]])  # Close the polygon
        codes = [Path.MOVETO] + [Path.LINETO] * (num_points - 1) + [Path.CLOSEPOLY]
        
        return Path(vertices, codes)

    def _on_key(self, event) -> None:
        if event.key in ("q", "escape"):
            self._stopped = True

    def start(self, universe: RenderableUniverse, title: str = "Universe Live View") -> None:
        self.fig, self.ax = plt.subplots(figsize=(12, 10))
        self.ax.set_xlim(0, universe.width)
        self.ax.set_ylim(0, universe.height)
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.set_title(title)
        self.ax.set_facecolor('#f8f8f8')

        # Initialize empty patch lists
        self.food_patches = []
        self.venom_patches = []
        self.cell_patches = []

        # # Create legend
        # from matplotlib.patches import Patch
        # legend_elements = [
        #     Patch(facecolor='#3498db', edgecolor='#2980b9', label='Food'),
        #     Patch(facecolor='none', edgecolor='#e74c3c', linewidth=2, label='Venom'),
        #     Patch(facecolor='tab:green', edgecolor='#2c3e50', label='Cell')
        # ]
        # self.ax.legend(handles=legend_elements, loc="upper right")
        
        # self.fig.canvas.mpl_connect('key_press_event', self._on_key)
        plt.tight_layout()
        plt.show(block=False)

    def update(self, universe: RenderableUniverse, cycle_idx: int) -> None:
        # Clear previous patches
        for patch in self.food_patches + self.venom_patches + self.cell_patches:
            patch.remove()
        self.food_patches.clear()
        self.venom_patches.clear()
        self.cell_patches.clear()

        # Foods - simple smooth circles proportional to energy
        for food in universe.foods:
            if food.energy <= 0:
                continue
                
            diameter = self._diameter_from_value(food.energy)
            radius = diameter / 2.0
            
            circle = Circle(
                food.position,
                radius,
                facecolor="#3282bb",  # Bright blue
                edgecolor="#0d293b",  # Darker blue border
                linewidth=2.0,
                alpha=0.9,
            )
            self.ax.add_patch(circle)
            self.food_patches.append(circle)

        # Venoms - simple smooth hollow circles proportional to toxicity
        for venom in universe.venoms:
            if venom.toxicity <= 0:
                continue
                
            diameter = self._diameter_from_value(venom.toxicity)
            radius = diameter / 2.0
            
            circle = Circle(
                venom.position,
                radius,
                facecolor="#7c1d1d",  # Match background for hollow effect
                edgecolor="#2b0c09",  # Bright red
                linewidth=2.0,  # Thicker for visibility
                alpha=0.9,
            )
            self.ax.add_patch(circle)
            self.venom_patches.append(circle)

        # Cells - rough circles with inheritance colors
        for cell in universe.cells:
            if cell.energy <= 0:
                continue
                
            radius = cell.diameter / 2.0
            circle = Circle(
                cell.position,
                radius,
                facecolor=cell.hex_color,
                edgecolor='#2c3e50',
                linewidth=2.0,
                alpha=0.9,
            )

            self.ax.add_patch(circle)
            self.cell_patches.append(circle)

        # Update title
        self.ax.set_title(
            f"Universe Live View — Cycle {cycle_idx}\n"
            f"Cells: {len(universe.cells)} | Food: {len(universe.foods)} | Venom: {len(universe.venoms)}",
            fontsize=12
        )
        
        self.fig.canvas.draw()
        plt.pause(0.01)

    @property
    def stopped(self) -> bool:
        return self._stopped


# Simple usage:
Renderer = Renderer