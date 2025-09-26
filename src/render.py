from __future__ import annotations

import matplotlib.pyplot as plt
from typing import Protocol, runtime_checkable, List

from entities import Food, Venom, Agent


@runtime_checkable
class RenderableUniverse(Protocol):
    width: float
    height: float
    foods: List[Food]
    venoms: List[Venom]
    agents: List[Agent]


class Renderer:
    """Live renderer that depends only on the RenderableUniverse protocol."""

    def __init__(self):
        self.fig = None
        self.ax = None
        self.food_scatter = None
        self.venom_scatter = None
        self.agent_scatter = None
        self.text_box = None

    def start(self, universe: RenderableUniverse, title: str = "Universe Live View") -> None:
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlim(0, universe.width)
        self.ax.set_ylim(0, universe.height)
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.set_title(title)

        self.food_scatter = self.ax.scatter([], [], marker='o', label='Food')
        self.venom_scatter = self.ax.scatter([], [], marker='x', label='Venom')
        self.agent_scatter = self.ax.scatter([], [], marker='^', label='Agent')
        self.ax.legend(loc="upper right")

        self.text_box = self.ax.text(0.01, 0.99, "", transform=self.ax.transAxes, va="top")
        plt.show(block=False)

    def update(self, universe: RenderableUniverse, cycle_idx: int) -> None:
        fx = [f.position[0] for f in universe.foods]
        fy = [f.position[1] for f in universe.foods]
        vx = [v.position[0] for v in universe.venoms]
        vy = [v.position[1] for v in universe.venoms]
        axx = [a.position[0] for a in universe.agents]
        ayy = [a.position[1] for a in universe.agents]

        self.food_scatter.set_offsets(list(zip(fx, fy)) if fx else [])
        self.venom_scatter.set_offsets(list(zip(vx, vy)) if vx else [])
        self.agent_scatter.set_offsets(list(zip(axx, ayy)) if axx else [])

        self.text_box.set_text(
            f"Cycle: {cycle_idx}\n"
            f"Foods: {len(universe.foods)}\n"
            f"Venoms: {len(universe.venoms)}\n"
            f"Agents: {len(universe.agents)}"
        )
        self.ax.set_title(f"Universe Live View — Cycle {cycle_idx}")
        self.fig.canvas.draw()
        plt.pause(0.01)
