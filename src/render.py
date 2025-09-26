from __future__ import annotations

import matplotlib
matplotlib.use("TkAgg")  # you said Tk works on your machine

import matplotlib.pyplot as plt
from typing import Protocol, runtime_checkable, List, Sequence
from entities import Food, Venom, Agent
import math


@runtime_checkable
class RenderableUniverse(Protocol):
    width: float
    height: float
    foods: List[Food]
    venoms: List[Venom]
    agents: List[Agent]


class Renderer:
    """Live renderer. Press 'q' or 'Esc' to stop."""

    def __init__(
        self,
        food_size_range: tuple[float, float] = (20.0, 400.0),
        venom_size_range: tuple[float, float] = (20.0, 400.0),
        sqrt_scale: bool = True,
    ):
        self.fig = None
        self.ax = None
        self.food_scatter = None
        self.venom_scatter = None
        self.agent_scatter = None
        self.text_box = None
        self._stopped = False
        self._cid_key = None

        self.food_size_range = food_size_range
        self.venom_size_range = venom_size_range
        self.sqrt_scale = sqrt_scale

    # ---------- helpers ----------

    def _normalize_sizes(self, values: Sequence[float], smin: float, smax: float) -> List[float]:
        if not values:
            return []
        vals = [max(v, 0.0) for v in values]
        if self.sqrt_scale:
            vals = [math.sqrt(v) for v in vals]
        vmax = max(vals) if vals else 1.0
        if vmax <= 1e-12:
            return [smin for _ in vals]
        scale = (smax - smin) / vmax
        return [smin + v * scale for v in vals]

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

        # Colors: Food = blue (filled), Venom = red (hollow), Agents = black triangles
        self.food_scatter  = self.ax.scatter([], [], marker='o', c='tab:blue', edgecolors='k', label='Food')
        self.venom_scatter = self.ax.scatter([], [], marker='o', c='tab:red', edgecolors='k', label='Venom')
        self.agent_scatter = self.ax.scatter([], [], marker='^', c='k', label='Agent')

        # self.ax.legend(loc="upper right")
        # self.text_box = self.ax.text(0.01, 0.99, "", transform=self.ax.transAxes, va="top")

        # key handler for stop
        self._cid_key = self.fig.canvas.mpl_connect('key_press_event', self._on_key)

        plt.show(block=False)

    def update(self, universe: RenderableUniverse, cycle_idx: int) -> None:
        # Foods
        fx = [f.position[0] for f in universe.foods]
        fy = [f.position[1] for f in universe.foods]
        fE = [f.energy for f in universe.foods]
        self.food_scatter.set_offsets(list(zip(fx, fy)) if fx else [])
        self.food_scatter.set_sizes(self._normalize_sizes(fE, *self.food_size_range))

        # Venoms
        vx = [v.position[0] for v in universe.venoms]
        vy = [v.position[1] for v in universe.venoms]
        vT = [v.toxicity for v in universe.venoms]
        self.venom_scatter.set_offsets(list(zip(vx, vy)) if vx else [])
        self.venom_scatter.set_sizes(self._normalize_sizes(vT, *self.venom_size_range))

        # Agents
        axx = [a.position[0] for a in universe.agents]
        ayy = [a.position[1] for a in universe.agents]
        self.agent_scatter.set_offsets(list(zip(axx, ayy)) if axx else [])

        # HUD
        # self.text_box.set_text(
        #     f"Cycle: {cycle_idx}\n"
        #     f"Foods: {len(universe.foods)}\n"
        #     f"Venoms: {len(universe.venoms)}\n"
        #     f"Agents: {len(universe.agents)}\n"
        #     f"(press 'q' or Esc to stop)"
        # )
        self.ax.set_title(f"Universe Live View — Cycle {cycle_idx}")

        self.fig.canvas.draw()
        plt.pause(0.01)

    @property
    def stopped(self) -> bool:
        return self._stopped
