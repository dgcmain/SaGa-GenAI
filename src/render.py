from __future__ import annotations
import math
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.animation import FFMpegWriter, PillowWriter

from pathlib import Path
from typing import Protocol, runtime_checkable, List, Sequence, Optional, Tuple
import time

matplotlib.use("TkAgg")

from entities import Food, Venom
from cell import Cell


@runtime_checkable
class RenderableUniverse(Protocol):
    width: float
    height: float
    foods: List[Food]
    venoms: List[Venom]
    cells: List[Cell]


class VideoRecorder:
    """Handles video recording functionality"""
    
    def __init__(
        self,
        output_path: str = "simulation_recording",
        fps: int = 30,
        quality: int = 5,  # 1-10, higher is better quality
        codec: str = "libx264",
        dpi: int = 100,
    ):
        self.output_path = Path(output_path)
        self.fps = fps
        self.quality = quality
        self.codec = codec
        self.dpi = dpi
        self.writer = None
        self.is_recording = False
        self.frame_count = 0
        
        # Create output directory if it doesn't exist
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
    def start_recording(self, fig: plt.Figure, output_format: str = "mp4") -> None:
        """Start recording video"""
        if self.is_recording:
            return
            
        # Determine writer based on format
        if output_format.lower() in ["mp4", "avi", "mov"]:
            self.writer = FFMpegWriter(
                fps=self.fps,
                codec=self.codec,
                bitrate=-1,  # Auto bitrate
                extra_args=["-crf", str(31 - self.quality * 3)]  # CRF: 1-51, lower is better
            )
            output_file = self.output_path.with_suffix(f".{output_format}")
        elif output_format.lower() in ["gif"]:
            self.writer = PillowWriter(fps=self.fps)
            output_file = self.output_path.with_suffix(".gif")
        else:
            raise ValueError(f"Unsupported format: {output_format}")
            
        self.writer.setup(fig, str(output_file), dpi=self.dpi)
        self.is_recording = True
        self.frame_count = 0
        print(f"Started recording: {output_file}")
        
    def capture_frame(self) -> None:
        """Capture current frame"""
        if self.is_recording and self.writer:
            self.writer.grab_frame()
            self.frame_count += 1
            
    def stop_recording(self) -> None:
        """Stop recording and finalize video"""
        if self.is_recording and self.writer:
            self.writer.finish()
            self.is_recording = False
            print(f"Recording stopped. Saved {self.frame_count} frames.")
            
    @property
    def recording_status(self) -> str:
        """Get recording status string"""
        if self.is_recording:
            return f"REC [{self.frame_count}]"
        return ""


class Renderer:
    """
    Ultra-fast, clean renderer with video recording capabilities.
    """

    def __init__(
        self,
        update_every_n_frames: int = 2,
        use_scatter_plots: bool = True,
        batch_size: int = 50,
        recording_enabled: bool = False,
        recording_path: str = "simulation",
        recording_fps: int = 30,
        recording_quality: int = 8,
    ):
        self.fig = None
        self.ax = None
        self._stopped = False
        
        # Performance settings
        self.update_every_n_frames = update_every_n_frames
        self.use_scatter_plots = use_scatter_plots
        self.batch_size = batch_size
        self.frame_count = 0
        
        # Scatter plot collections
        self.food_scatter = None
        self.venom_scatter = None
        self.cell_scatter = None

        # Patch collections for physical rendering
        self.food_patches = []
        self.venom_patches = [] 
        self.cell_patches = []
        
        # Video recording
        self.recorder = VideoRecorder(
            output_path=recording_path,
            fps=recording_fps,
            quality=recording_quality,
        )
        self.recording_enabled = recording_enabled
        
        # Performance tracking
        self.render_times = []

    def _on_key(self, event) -> None:
        """Handle keyboard events"""
        if event.key in ("q", "escape"):
            self._stopped = True
        elif event.key == "r" and not self.recorder.is_recording:
            # Start recording on 'r' key
            self.start_recording()
        elif event.key == "s" and self.recorder.is_recording:
            # Stop recording on 's' key
            self.stop_recording()
        elif event.key == "p":
            # Toggle pause (implement if needed)
            pass

    def start_recording(self, output_format: str = "mp4") -> None:
        """Start video recording"""
        if self.fig and not self.recorder.is_recording:
            self.recorder.start_recording(self.fig, output_format)
            
    def stop_recording(self) -> None:
        """Stop video recording"""
        if self.recorder.is_recording:
            self.recorder.stop_recording()

    def start(self, universe: RenderableUniverse, title: str = "Universe Live View") -> None:
        # Create figure with minimal elements
        self.fig, self.ax = plt.subplots(figsize=(12, 10))
        self.fig.canvas.toolbar.pack_forget()

        # Remove all axes, ticks, labels for clean look
        self.ax.set_xlim(0, universe.width)
        self.ax.set_ylim(0, universe.height)
        self.ax.set_axis_off()
        self.ax.set_facecolor('#000000')
        
        # Remove padding and margins
        self.fig.tight_layout(pad=0)
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        
        # Connect keyboard events
        self.fig.canvas.mpl_connect('key_press_event', self._on_key)
        
        # Add recording status text
        self.status_text = self.ax.text(
            0.02, 0.98, '', 
            transform=self.ax.transAxes, 
            color='white', 
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.7)
        )
        
        plt.show(block=False)

    def update(self, universe: RenderableUniverse, cycle_idx: int) -> None:
        start_time = time.time()
        
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

        # Update title and status
        status_lines = [
            f"Cycle: {cycle_idx}",
            f"Cells: {len(universe.cells)} | Food: {len(universe.foods)} | Venom: {len(universe.venoms)}",
            f"Recording: {self.recorder.recording_status}",
            "Controls: [R]ecord [S]top [Q]uit"
        ]
        
        if cycle_idx % 50 == 0:
            self.ax.set_title(
                f"Cycle {cycle_idx} | Cells: {len(universe.cells)} | Food: {len(universe.foods)} | Venom: {len(universe.venoms)}",
                fontsize=10, color='white', pad=10
            )
            
        # Update status text
        self.status_text.set_text('\n'.join(status_lines))

        # Capture frame for recording
        if self.recording_enabled and self.recorder.is_recording:
            self.recorder.capture_frame()

        # Ultra-fast drawing with minimal pause
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()
        plt.pause(0.001)
        
        # Track performance
        render_time = time.time() - start_time
        self.render_times.append(render_time)
        if len(self.render_times) > 100:
            self.render_times.pop(0)

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
                    food.energy / 2.0,
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
                    venom.toxicity / 2.0,
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
                    cell.diameter / 2.0,
                    facecolor=cell.hex_color,
                    edgecolor="#242b31",
                    linewidth=3.0,
                    alpha=0.85,
                )
                self.ax.add_patch(circle)
                self.cell_patches.append(circle)

    def _render_with_circles(self, universe: RenderableUniverse, cycle_idx: int):
        """Slower but higher quality rendering with Circle patches."""
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
                    facecolor="#7c1d1d",
                    edgecolor="#2b0c09",
                    linewidth=2.0,
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

    @property
    def average_render_time(self) -> float:
        """Get average render time for performance monitoring"""
        if not self.render_times:
            return 0.0
        return sum(self.render_times) / len(self.render_times)