from __future__ import annotations

import random
import time
from uuid import uuid4
import matplotlib.pyplot as plt
import argparse

from cell import Cell
from entities import Food, Venom

from universe import Universe
from render import Renderer


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(description="Cell Simulation with Video Recording")
    
    # Simulation parameters
    parser.add_argument("--width", type=float, default=1000.0, help="Universe width")
    parser.add_argument("--height", type=float, default=1200.0, help="Universe height")
    parser.add_argument("--cells", type=int, default=7, help="Initial number of cells")
    parser.add_argument("--food", type=int, default=5, help="Initial number of food items")
    parser.add_argument("--venom", type=int, default=5, help="Initial number of venom items")
    
    # Rendering parameters
    parser.add_argument("--fps", type=int, default=30, help="Target frames per second")
    parser.add_argument("--update-every", type=int, default=2, help="Render every N frames")
    parser.add_argument("--no-scatter", action="store_false", dest="use_scatter", 
                       help="Use circle patches instead of scatter")
    
    # Recording parameters
    parser.add_argument("--record", action="store_true", help="Enable video recording")
    parser.add_argument("--record-path", type=str, default="simulation", 
                       help="Output path for recording")
    parser.add_argument("--record-fps", type=int, default=30, 
                       help="FPS for recording")
    parser.add_argument("--record-quality", type=int, default=8, choices=range(1, 11),
                       help="Recording quality (1-10, higher is better)")
    parser.add_argument("--record-format", type=str, default="mp4", 
                       choices=["mp4", "gif", "avi"], help="Output format for recording")
    
    # Performance parameters
    parser.add_argument("--batch-size", type=int, default=50, 
                       help="Batch size for rendering")
    
    return parser


def main():
    """Main function with CLI integration"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Initialize universe
    universe = Universe(
        initial_energy=7,
        ratio=0.6,
        waste_factor=0.95,
        width=1000.0,
        height=1200.0,
        venom_energy_to_toxicity=1.5,
        food_degrade_factor=0.998,
        venom_degrade_factor=0.998,
        cleanup_depleted=True,
        max_new_foods=3,
        max_new_venoms=2,
        min_unit_food=1.2,
        min_unit_venom=1.5,
    )
    
    # Add initial entities
    for _ in range(args.cells):
        universe.add_cell(
            Cell(
                id=uuid4(),
                energy=200.0,
                position=(random.uniform(0, universe.width),
                         random.uniform(0, universe.height)),
                basal_metabolism=0.08,
                reproduction_probability=0.05,
                move_cost_per_unit=0.02,
            )
        )
        
    for _ in range(args.food):
        universe.add_food(
            Food(
                id=uuid4(),
                energy=random.uniform(50.0, 100.0),
                position=(random.uniform(0, universe.width),
                         random.uniform(0, universe.height))
            )
        )

    for _ in range(args.venom):
        universe.add_venom(
            Venom(
                id=uuid4(),
                toxicity=random.uniform(50.0, 100.0),
                position=(random.uniform(0, universe.width),
                         random.uniform(0, universe.height))
            )
        )

    # Initialize renderer with CLI options
    renderer = Renderer(
        update_every_n_frames=args.update_every,
        use_scatter_plots=args.use_scatter,
        batch_size=args.batch_size,
        recording_enabled=args.record,
        recording_path=args.record_path,
        recording_fps=args.record_fps,
        recording_quality=args.record_quality,
    )

    print("Simulation Starting...")
    print(f"Universe: {args.width}x{args.height}")
    print(f"Entities: {args.cells} cells, {args.food} food, {args.venom} venom")
    print(f"Rendering: {args.fps} FPS target, update every {args.update_every} frames")
    if args.record:
        print(f"Recording: {args.record_path}.{args.record_format} at {args.record_fps} FPS")
    print("Controls: [R] Start recording, [S] Stop recording, [Q] Quit")

    renderer.start(universe)

    # Start recording immediately if requested
    if args.record:
        renderer.start_recording(args.record_format)

    # Simulation loop
    target_fps = args.fps
    frame_time = 1.0 / target_fps
    cycle_count = 0
    start_time = time.time()
    last_frame_time = start_time

    try:
        while not renderer.stopped:
            current_time = time.time()
            elapsed = current_time - last_frame_time
            
            if elapsed >= frame_time:
                cycle_count += 1
                steps_per_frame = 3
                for _ in range(steps_per_frame):
                    input_energy = random.uniform(250.0, 300.0)
                    universe.run(input_energy=input_energy, cycle_count=cycle_count)
                    cycle_count += 1
                
                renderer.update(universe, cycle_idx=cycle_count)
                last_frame_time = current_time
            else:
                time.sleep(0.0001)
                
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
    finally:
        # Stop recording if active
        if renderer.recorder.is_recording:
            renderer.stop_recording()
    
    print("\nFinal state:")
    print(f"Cells: {len(universe.cells)} | Food: {len(universe.foods)} | Venom: {len(universe.venoms)}")
    print(f"Average render time: {renderer.average_render_time*1000:.1f}ms")


if __name__ == "__main__":
    main()