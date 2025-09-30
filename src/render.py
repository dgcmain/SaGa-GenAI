from __future__ import annotations
import math
import numpy as np

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
import matplotlib.collections as mcollections
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
    cells: List[Cell]  # Changed from 'agents' to 'cells' to match your Universe class


class Renderer:
    """
    Live renderer. Press 'q' or 'Esc' to stop.
    
    Now uses cell.diameter property directly for smooth size changes.
    """

    def __init__(
        self,
        food_size_range: tuple[float, float] = (20.0, 400.0),
        venom_size_range: tuple[float, float] = (20.0, 400.0),
        sqrt_scale_food: bool = True,
        sqrt_scale_venom: bool = True,
    ):
        self.fig = None
        self.ax = None
        self.food_scatter = None
        self.venom_scatter = None
        self.cell_scatter = None
        self.text_box = None
        self._stopped = False

        self.food_size_range = food_size_range
        self.venom_size_range = venom_size_range
        self.sqrt_scale_food = sqrt_scale_food
        self.sqrt_scale_venom = sqrt_scale_venom

    def _sizes_area_from_values(
        self, values: Sequence[float], smin: float, smax: float, sqrt_scale: bool
    ) -> List[float]:
        """Return sizes in points^2 so that area tracks values (optionally sqrt-tempered)."""
        if not values:
            return []
        vals = [max(v, 0.0) for v in values]
        if sqrt_scale:
            vals = [math.sqrt(v) for v in vals]
        vmax = max(vals) if vals else 1.0
        if vmax <= 1e-12:
            return [smin for _ in vals]
        scale = (smax - smin) / vmax
        return [smin + v * scale for v in vals]

    def _diameters_to_areas(self, diameters: Sequence[float]) -> List[float]:
        """Convert diameters to areas (matplotlib scatter uses area for point sizes)."""
        return [d**2 for d in diameters]

    def _on_key(self, event) -> None:
        if event.key in ("q", "escape"):
            self._stopped = True

    def start(self, universe: RenderableUniverse, title: str = "Universe Live View") -> None:
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlim(0, universe.width)
        self.ax.set_ylim(0, universe.height)
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.set_title(title)

        # Food: blue filled circles
        self.food_scatter = self.ax.scatter([], [], marker='o', c='tab:blue', label='Food')

        # Venom: red hollow circles
        self.venom_scatter = self.ax.scatter([], [], marker='o', facecolors='none',
                                             edgecolors='tab:red', label='Venom')

        # Cells: green filled circles - use diameter property directly
        self.cell_scatter = self.ax.scatter([], [], marker='o', label='Cell')

        self.ax.legend(loc="upper right")
        self.fig.canvas.mpl_connect('key_press_event', self._on_key)
        plt.show(block=False)

    def update(self, universe: RenderableUniverse, cycle_idx: int) -> None:
        # Foods
        fx = [f.position[0] for f in universe.foods]
        fy = [f.position[1] for f in universe.foods]
        fE = [f.energy for f in universe.foods]
        self._set_offsets_safe(self.food_scatter, fx, fy)
        self.food_scatter.set_sizes(
            self._sizes_area_from_values(fE, *self.food_size_range, sqrt_scale=self.sqrt_scale_food)
        )

        # Venoms
        vx = [v.position[0] for v in universe.venoms]
        vy = [v.position[1] for v in universe.venoms]
        vT = [v.toxicity for v in universe.venoms]
        self._set_offsets_safe(self.venom_scatter, vx, vy)
        self.venom_scatter.set_sizes(
            self._sizes_area_from_values(vT, *self.venom_size_range, sqrt_scale=self.sqrt_scale_venom)
        )

        # Cells - use diameter property directly for smooth size changes
        cx = [c.position[0] for c in universe.cells]
        cy = [c.position[1] for c in universe.cells]
        cell_diameters = [c.diameter for c in universe.cells]
        cell_colors = [cell.hex_color for cell in universe.cells]

        self._set_offsets_safe(self.cell_scatter, cx, cy)
        self.cell_scatter.set_sizes(self._diameters_to_areas(cell_diameters))
        self.cell_scatter.set_color(cell_colors)

        # Update title
        self.ax.set_title(f"Universe Live View — Cycle {cycle_idx}")
        self.fig.canvas.draw()
        plt.pause(0.01)

    def _set_offsets_safe(self, scatter, xs, ys):
        if xs and ys:
            scatter.set_offsets(np.c_[xs, ys])   # shape (N,2)
        else:
            scatter.set_offsets(np.empty((0, 2)))  # shape (0,2) to avoid IndexError

    @property
    def stopped(self) -> bool:
        return self._stopped
    

class RoughRenderer:
    """
    Renderer that creates rough, hand-drawn looking cells with strokes.
    """

    def __init__(
        self,
        food_size_range: tuple[float, float] = (20.0, 400.0),
        venom_size_range: tuple[float, float] = (20.0, 400.0),
        cell_roughness: float = 0.1,  # How rough the cells look (0=smooth, 1=very rough)
        cell_stroke_width: float = 1,  # Width of the cell border stroke
        sqrt_scale_food: bool = True,
        sqrt_scale_venom: bool = True,
    ):
        self.fig = None
        self.ax = None
        self.food_scatter = None
        self.venom_scatter = None
        self.cell_patches: List[PathPatch] = []
        self.text_box = None
        self._stopped = False

        self.food_size_range = food_size_range
        self.venom_size_range = venom_size_range
        self.cell_roughness = cell_roughness
        self.cell_stroke_width = cell_stroke_width
        self.sqrt_scale_food = sqrt_scale_food
        self.sqrt_scale_venom = sqrt_scale_venom

    def _sizes_area_from_values(
        self, values: Sequence[float], smin: float, smax: float, sqrt_scale: bool
    ) -> List[float]:
        """Return sizes in points^2 so that area tracks values (optionally sqrt-tempered)."""
        if not values:
            return []
        vals = [max(v, 0.0) for v in values]
        if sqrt_scale:
            vals = [math.sqrt(v) for v in vals]
        vmax = max(vals) if vals else 1.0
        if vmax <= 1e-12:
            return [smin for _ in vals]
        scale = (smax - smin) / vmax
        return [smin + v * scale for v in vals]

    def _create_simple_rough_circle(self, center: tuple[float, float], radius: float) -> Path:
        """Simpler version for better performance."""
        x, y = center
        num_points = 20  # Fixed number of points for consistency
        
        angles = np.linspace(0, 2 * np.pi, num_points)
        base_x = x + radius * np.cos(angles)
        base_y = y + radius * np.sin(angles)
        
        # Add roughness
        roughness = self.cell_roughness * radius * 0.6
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
        self.ax.set_facecolor('#f8f8f8')  # Light background

        # Food: blue filled circles with rough appearance
        self.food_scatter = self.ax.scatter([], [], marker='o', c='tab:blue', 
                                           alpha=0.7, label='Food')

        # Venom: red hollow circles with rough appearance
        self.venom_scatter = self.ax.scatter([], [], marker='o', facecolors='none',
                                             edgecolors='tab:red', linewidths=1.5,
                                             alpha=0.7, label='Venom')

        # Cells will be drawn as rough patches
        self.cell_patches = []

        self.ax.legend(loc="upper right")
        self.fig.canvas.mpl_connect('key_press_event', self._on_key)
        plt.tight_layout()
        plt.show(block=False)

    def update(self, universe: RenderableUniverse, cycle_idx: int) -> None:
        # Clear previous cell patches
        for patch in self.cell_patches:
            patch.remove()
        self.cell_patches.clear()

        # Foods
        fx = [f.position[0] for f in universe.foods]
        fy = [f.position[1] for f in universe.foods]
        fE = [f.energy for f in universe.foods]
        self._set_offsets_safe(self.food_scatter, fx, fy)
        self.food_scatter.set_sizes(
            self._sizes_area_from_values(fE, *self.food_size_range, sqrt_scale=self.sqrt_scale_food)
        )

        # Venoms
        vx = [v.position[0] for v in universe.venoms]
        vy = [v.position[1] for v in universe.venoms]
        vT = [v.toxicity for v in universe.venoms]
        self._set_offsets_safe(self.venom_scatter, vx, vy)
        self.venom_scatter.set_sizes(
            self._sizes_area_from_values(vT, *self.venom_size_range, sqrt_scale=self.sqrt_scale_venom)
        )

        # Cells - create rough circular patches with strokes
        for cell in universe.cells:
            if cell.energy <= 0:
                continue
                
            # Calculate radius from diameter
            radius = cell.diameter / 2.0
            
            # Create rough circle path
            path = self._create_simple_rough_circle(cell.position, radius)
            
            # Create patch with fill and stroke
            patch = PathPatch(
                path,
                facecolor=cell.hex_color,
                edgecolor='black',
                linewidth=self.cell_stroke_width,
                alpha=0.8,
                capstyle='round',
                joinstyle='round'
            )
            
            self.ax.add_patch(patch)
            self.cell_patches.append(patch)

        # Update title with stats
        self.ax.set_title(
            f"Universe Live View — Cycle {cycle_idx}\n"
            f"Cells: {len(universe.cells)} | Food: {len(universe.foods)} | Venom: {len(universe.venoms)}"
        )
        
        self.fig.canvas.draw()
        plt.pause(0.01)

    def _set_offsets_safe(self, scatter, xs, ys):
        if xs and ys:
            scatter.set_offsets(np.c_[xs, ys])
        else:
            scatter.set_offsets(np.empty((0, 2)))

    @property
    def stopped(self) -> bool:
        return self._stopped


Renderer = RoughRenderer
