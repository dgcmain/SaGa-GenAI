from __future__ import annotations

import matplotlib
matplotlib.use("TkAgg")  # or "Qt5Agg"

import matplotlib.pyplot as plt
from typing import Protocol, runtime_checkable, List, Sequence

from entities import Food, Venom, Agent


@runtime_checkable
class RenderableUniverse(Protocol):
    width: float
    height: float
    foods: List[Food]
    venoms: List[Venom]
    agents: List[Agent]


class Renderer:
    """Live renderer that depends only on the RenderableUniverse protocol.
       Food circle size ∝ energy; Venom circle size ∝ toxicity."""

    def __init__(self,
                 food_size_range: tuple[float, float] = (20.0, 400.0),
                 venom_size_range: tuple[float, float] = (20.0, 400.0),
                 sqrt_scale: bool = True):
        self.fig = None
        self.ax = None
        self.food_scatter = None
        self.venom_scatter = None
        self.agent_scatter = None
        self.text_box = None

        self.food_size_range = food_size_range
        self.venom_size_range = venom_size_range
        self.sqrt_scale = sqrt_scale  # reduces dominance of big values

    # ---------- helpers ----------

    def _normalize_sizes(self, values: Sequence[float], vmin: float, vmax: float,
                         smin: float, smax: float) -> List[float]:
        """Map values in [vmin, vmax] → sizes in [smin, smax] (points^2)."""
        if not values:
            return []
        if self.sqrt_scale:
            # sqrt scaling tames large values visually
            import math
            values = [math.sqrt(max(v, 0.0)) for v in values]
            vmin = 0.0
            vmax = max(values) if values else 1.0
        else:
            vmax = max(vmax, vmin + 1e-12)
        if vmax <= vmin + 1e-12:
            return [smin for _ in values]
        scale = (smax - smin) / (vmax - vmin)
        return [smin + (v - vmin) * scale for v in values]

    # ---------- public ----------

    def start(self, universe: RenderableUniverse, title: str = "Universe Live View") -> None:
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlim(0, universe.width)
        self.ax.set_ylim(0, universe.height)
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.set_title(title)

        # Initialize empty scatters (we will set sizes later in update)
        self.food_scatter  = self.ax.scatter([], [], marker='o', label='Food')
        self.venom_scatter = self.ax.scatter([], [], marker='o', facecolors='none', edgecolors='black', label='Venom')
        self.agent_scatter = self.ax.scatter([], [], marker='^', label='Agent')
        self.ax.legend(loc="upper right")

        self.text_box = self.ax.text(0.01, 0.99, "", transform=self.ax.transAxes, va="top")
        plt.show(block=False)

    def update(self, universe: RenderableUniverse, cycle_idx: int) -> None:
        # --- Foods ---
        fx = [f.position[0] for f in universe.foods]
        fy = [f.position[1] for f in universe.foods]
        fE = [max(f.energy, 0.0) for f in universe.foods]
        f_sizes = self._normalize_sizes(
            fE,
            vmin=0.0,
            vmax=max(fE) if fE else 1.0,
            smin=self.food_size_range[0],
            smax=self.food_size_range[1],
        )
        self.food_scatter.set_offsets(list(zip(fx, fy)) if fx else [])
        self.food_scatter.set_sizes(f_sizes)

        # --- Venoms ---
        vx = [v.position[0] for v in universe.venoms]
        vy = [v.position[1] for v in universe.venoms]
        vT = [max(v.toxicity, 0.0) for v in universe.venoms]
        v_sizes = self._normalize_sizes(
            vT,
            vmin=0.0,
            vmax=max(vT) if vT else 1.0,
            smin=self.venom_size_range[0],
            smax=self.venom_size_range[1],
        )
        self.venom_scatter.set_offsets(list(zip(vx, vy)) if vx else [])
        self.venom_scatter.set_sizes(v_sizes)

        # --- Agents ---
        axx = [a.position[0] for a in universe.agents]
        ayy = [a.position[1] for a in universe.agents]
        self.agent_scatter.set_offsets(list(zip(axx, ayy)) if axx else [])

        # HUD
        self.text_box.set_text(
            f"Cycle: {cycle_idx}\n"
            f"Foods: {len(universe.foods)}\n"
            f"Venoms: {len(universe.venoms)}\n"
            f"Agents: {len(universe.agents)}"
        )
        self.ax.set_title(f"Universe Live View — Cycle {cycle_idx}")

        self.fig.canvas.draw()
        plt.pause(0.01)
