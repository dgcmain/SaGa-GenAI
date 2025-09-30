from __future__ import annotations
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from typing import Protocol, runtime_checkable, List, Sequence
from entities import Food, Venom
from cell import Cell
import math


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