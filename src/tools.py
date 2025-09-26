from typing import Optional
from cell import Cell


def _dist2(a: tuple[float, float], b: tuple[float, float]) -> float:
    dx, dy = a[0]-b[0], a[1]-b[1]
    return dx*dx + dy*dy


def _nearest_food_within(self, pos: tuple[float, float]) -> Optional[int]:
    best_i, best_d2 = None, self.touch_radius_food2
    for i, f in enumerate(self.foods):
        d2 = _dist2(pos, f.position)
        if d2 <= best_d2:
            best_d2 = d2
            best_i = i
    return best_i


def _nearest_venom_within(self, pos: tuple[float, float]) -> Optional[int]:
    best_i, best_d2 = None, self.touch_radius_venom2
    for i, v in enumerate(self.venoms):
        d2 = _dist2(pos, v.position)
        if d2 <= best_d2:
            best_d2 = d2
            best_i = i
    return best_i


def _interact_partial(self, cell: Cell) -> None:
    """Transfer a fraction (capped) from the nearest food & venom within touch radius."""
    if cell.energy <= 0.0:
        return

    # Food → cell (gain some)
    fi = self._nearest_food_within(cell.position)
    if fi is not None:
        food = self.foods[fi]
        if food.energy > 0.0:
            amt = min(food.energy * self.food_transfer_fraction, self.food_transfer_cap)
            if amt > 0.0:
                food.energy -= amt
                cell.energy += amt

    # Venom → cell (lose some)
    vi = self._nearest_venom_within(cell.position)
    if vi is not None:
        venom = self.venoms[vi]
        if venom.toxicity > 0.0:
            dmg = min(venom.toxicity * self.venom_transfer_fraction, self.venom_transfer_cap)
            if dmg > 0.0:
                venom.toxicity -= dmg
                cell.energy -= dmg
                if cell.energy < 0.0:
                    cell.energy = 0.0
