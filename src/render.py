from __future__ import annotations
import math
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
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
    Ultra-fast, clean renderer with maximum performance.
    No axes, ticks, or labels - just the simulation.
    """

    def __init__(
        self,
        update_every_n_frames: int = 2,      # Skip frames for performance
        use_scatter_plots: bool = True,      # Use scatter for max performance
        batch_size: int = 50,                # Process objects in batches
    ):
        self.fig = None
        self.ax = None
        self._stopped = False
        
        # Performance settings
        self.update_every_n_frames = update_every_n_frames
        self.use_scatter_plots = use_scatter_plots
        self.batch_size = batch_size
        self.frame_count = 0
        
        # Scatter plot collections (for batch rendering)
        self.food_scatter = None
        self.venom_scatter = None
        self.cell_scatter = None

        # Patch collections for physical rendering
        self.food_patches = []
        self.venom_patches = [] 
        self.cell_patches = []

    def _on_key(self, event) -> None:
        if event.key in ("q", "escape"):
            self._stopped = True

    def start(self, universe: RenderableUniverse, title: str = "Universe Live View") -> None:
        # Create figure with minimal elements
        self.fig, self.ax = plt.subplots(figsize=(12, 10))
        
        # Remove all axes, ticks, labels for clean look
        self.ax.set_xlim(0, universe.width)
        self.ax.set_ylim(0, universe.height)
        self.ax.set_axis_off()  # Remove axes completely
        self.ax.set_facecolor('#000000')  # Black background for contrast
        
        # Remove padding and margins
        self.fig.tight_layout(pad=0)
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        
        # Connect keyboard events
        self.fig.canvas.mpl_connect('key_press_event', self._on_key)
        plt.show(block=False)

    def update(self, universe: RenderableUniverse, cycle_idx: int) -> None:
        self.frame_count += 1
        
        # Skip frames for performance
        if self.frame_count % self.update_every_n_frames != 0:
            return

        # Clear previous scatter plots
        if self.food_scatter:
            self.food_scatter.remove()
        if self.venom_scatter:
            self.venom_scatter.remove()
        if self.cell_scatter:
            self.cell_scatter.remove()

        # Use ultra-fast scatter plot rendering
        if self.use_scatter_plots:
            self._render_with_scatter(universe, cycle_idx)
        else:
            self._render_with_circles(universe, cycle_idx)

        # Update title less frequently for performance
        if cycle_idx % 50 == 0:
            self.ax.set_title(
                f"Cycle {cycle_idx} | Cells: {len(universe.cells)} | Food: {len(universe.foods)} | Venom: {len(universe.venoms)}",
                fontsize=10, color='white', pad=10
            )

        # Ultra-fast drawing with minimal pause
        self.fig.canvas.draw_idle()  # Use draw_idle instead of draw for better performance
        self.fig.canvas.flush_events()
        plt.pause(0.001)  # Minimal pause

    def _render_with_scatter(self, universe: RenderableUniverse, cycle_idx: int):
        """Render using Circle patches at actual physical sizes."""
        
        # Clear previous patches
        for patch in self.food_patches + self.venom_patches + self.cell_patches:
            patch.remove()
        self.food_patches.clear()
        self.venom_patches.clear()
        self.cell_patches.clear()

        # Batch process foods - use ACTUAL diameters
        for food in universe.foods:
            if food.energy > 0:
                circle = Circle(
                    food.position,
                    food.energy / 2.0,  # Use actual radius
                    facecolor="#3282bb",
                    edgecolor="#0d293b", 
                    linewidth=2.0,
                    alpha=0.8,
                )
                self.ax.add_patch(circle)
                self.food_patches.append(circle)

        # Batch process venoms - use ACTUAL diameters  
        for venom in universe.venoms:
            if venom.toxicity > 0:
                circle = Circle(
                    venom.position,
                    venom.toxicity / 2.0,  # Use actual radius
                    facecolor="#DD3131",
                    edgecolor="#421010",
                    linewidth=2,
                    alpha=0.8,
                )
                self.ax.add_patch(circle)
                self.venom_patches.append(circle)

        # Batch process cells - use ACTUAL diameters
        for cell in universe.cells:
            if cell.energy > 0:
                circle = Circle(
                    cell.position,
                    cell.diameter / 2.0,  # Use actual radius
                    facecolor=cell.hex_color,
                    edgecolor="#242b31",
                    linewidth=3.0,
                    alpha=0.85,
                )
                self.ax.add_patch(circle)
                self.cell_patches.append(circle)

    def _render_with_circles(self, universe: RenderableUniverse, cycle_idx: int):
        """Slower but higher quality rendering with Circle patches."""
        # Process in smaller batches to prevent lag
        batch_count = 0
        
        # Food circles
        for food in universe.foods:
            if food.energy > 0 and batch_count < self.batch_size:
                circle = Circle(
                    food.position,
                    food.energy / 2.0,
                    facecolor="#3282bb",
                    edgecolor="#0d293b",
                    linewidth=1.0,
                    alpha=0.8,
                )
                self.ax.add_patch(circle)
                batch_count += 1

        batch_count = 0
        # Venom circles
        for venom in universe.venoms:
            if venom.toxicity > 0 and batch_count < self.batch_size:
                circle = Circle(
                    venom.position,
                    venom.toxicity / 2.0,
                    facecolor="#7c1d1d",  # Match background for hollow effect
                    edgecolor="#2b0c09",  # Bright red
                    linewidth=2.0,  # Thicker for visibility
                    alpha=0.9,
                )
                self.ax.add_patch(circle)
                batch_count += 1

        batch_count = 0
        # Cell circles
        for cell in universe.cells:
            if cell.energy > 0 and batch_count < self.batch_size:
                circle = Circle(
                    cell.position,
                    cell.diameter / 2.0,
                    facecolor=cell.hex_color,
                    edgecolor='#2c3e50',
                    linewidth=1.0,
                    alpha=0.85,
                )
                self.ax.add_patch(circle)
                batch_count += 1

    @property
    def stopped(self) -> bool:
        return self._stopped


# Ultra-fast renderer usage:
Renderer = Renderer