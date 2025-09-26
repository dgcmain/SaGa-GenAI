from __future__ import annotations
import numpy as np


import matplotlib
matplotlib.use("TkAgg")  # you said Tk works on your machine

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
    agents: List[Cell]


class Renderer:
    """
    Live renderer. Press 'q' or 'Esc' to stop.

    Sizes:
      - Foods: area ∝ energy  (sqrt scale ON)
      - Venoms: area ∝ toxicity (sqrt scale ON)
      - Agents: DIAMETER ∝ energy  -> area ∝ energy^2  (sqrt scale OFF + square)
    """

    def __init__(
        self,
        food_size_range: tuple[float, float] = (20.0, 400.0),
        venom_size_range: tuple[float, float] = (20.0, 400.0),
        agent_size_range: tuple[float, float] = (20.0, 500.0),  # diameter range (pts) converted to area
        sqrt_scale_food: bool = True,
        sqrt_scale_venom: bool = True,
    ):
        self.fig = None
        self.ax = None
        self.food_scatter = None
        self.venom_scatter = None
        self.agent_scatter = None
        self.text_box = None
        self._stopped = False

        self.food_size_range = food_size_range
        self.venom_size_range = venom_size_range
        self.agent_size_range = agent_size_range
        self.sqrt_scale_food = sqrt_scale_food
        self.sqrt_scale_venom = sqrt_scale_venom

    # ---------- helpers ----------

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

    def _sizes_area_for_diameter_proportional(
        self, values: Sequence[float], dmin: float, dmax: float
    ) -> List[float]:
        """
        Diameter ∝ value. Matplotlib 's' is area (pts^2), so we map:
          d = dmin + (value/max(value))*(dmax - dmin)
          area s = d^2
        """
        if not values:
            return []
        vals = [max(v, 0.0) for v in values]
        vmax = max(vals) if vals else 1.0
        if vmax <= 1e-12:
            return [dmin * dmin for _ in vals]
        scale = (dmax - dmin) / vmax
        return [(dmin + v * scale) ** 2 for v in vals]

    def _on_key(self, event) -> None:
        if event.key in ("q", "escape"):
            self._stopped = True

    # ---------- public ----------

    def start(self, universe: RenderableUniverse, title: str = "Universe Live View") -> None:
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlim(0, universe.width)
        self.ax.set_ylim(0, universe.height)
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.set_title(title)

        # Food: blue filled circles
        self.food_scatter  = self.ax.scatter([], [], marker='o', c='tab:blue', label='Food')

        # Venom: red hollow circles
        self.venom_scatter = self.ax.scatter([], [], marker='o', facecolors='none',
                                             edgecolors='tab:red', label='Venom')

        # Agents (cells): green filled circles (diameter ∝ energy)
        self.agent_scatter = self.ax.scatter([], [], marker='o', c='tab:green', label='Cell')

        self.ax.legend(loc="upper right")
        #self.text_box = self.ax.text(0.01, 0.99, "", transform=self.ax.transAxes, va="top")

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

        # Cells
        axx = [a.position[0] for a in universe.cells]
        ayy = [a.position[1] for a in universe.cells]
        aE  = [getattr(a, "energy", 0.0) for a in universe.cells]
        self._set_offsets_safe(self.agent_scatter, axx, ayy)
        self.agent_scatter.set_sizes(
            self._sizes_area_from_values(aE, *self.agent_size_range, sqrt_scale=True)
        )

        # HUD + redraw
        # self.text_box.set_text(
        #     f"Cycle: {cycle_idx}\n"
        #     f"Foods: {len(universe.foods)}\n"
        #     f"Venoms: {len(universe.venoms)}\n"
        #     f"Cells: {len(universe.cells)}\n"
        #     f"(press 'q' or Esc to stop)"
        # )
        self.ax.set_title(f"Universe Live View — Cycle {cycle_idx}")
        self.fig.canvas.draw()
        plt.pause(0.01)

    # inside Renderer class
    def _set_offsets_safe(self, scatter, xs, ys):
        if xs and ys:
            scatter.set_offsets(np.c_[xs, ys])   # shape (N,2)
        else:
            scatter.set_offsets(np.empty((0, 2)))  # shape (0,2) to avoid IndexError

    @property
    def stopped(self) -> bool:
        return self._stopped