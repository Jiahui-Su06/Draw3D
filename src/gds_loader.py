from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import gdstk
import numpy as np

from objects import Bounds2D


@dataclass(frozen=True)
class GdsLayerData:
    file_path: Path
    cell_name: str
    layer: int
    datatype: int
    bounds: Bounds2D
    polygons: list[gdstk.Polygon]


def load_default_gds_layer(file_path: Path) -> GdsLayerData:
    """Load the first useful GDS layer using conservative defaults."""
    path = file_path.expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() != ".gds":
        raise ValueError("selected file is not a .gds file")

    lib = gdstk.read_gds(str(path))
    top_cells = [cell for cell in lib.top_level() if isinstance(cell, gdstk.Cell)]
    if not top_cells:
        raise ValueError("no top-level cell found in GDS")

    cell = _choose_cell(top_cells)
    all_polygons = cell.get_polygons(
        apply_repetitions=True, include_paths=True, depth=None
    )
    if not all_polygons:
        raise ValueError(f"cell has no polygons: {cell.name}")

    layer, datatype = _choose_layer_pair(all_polygons)
    polygons = [
        poly
        for poly in all_polygons
        if int(poly.layer) == layer and int(poly.datatype) == datatype
    ]
    if not polygons:
        raise ValueError(f"no polygons found on layer/datatype ({layer}, {datatype})")

    return GdsLayerData(
        file_path=path,
        cell_name=cell.name,
        layer=layer,
        datatype=datatype,
        bounds=_compute_bounds(polygons),
        polygons=polygons,
    )


def _choose_cell(cells: list[gdstk.Cell]) -> gdstk.Cell:
    for cell in cells:
        if cell.name == "AWG":
            return cell
    return cells[0]


def _choose_layer_pair(polygons: list[gdstk.Polygon]) -> tuple[int, int]:
    pairs = sorted({(int(poly.layer), int(poly.datatype)) for poly in polygons})
    if (4, 1) in pairs:
        return (4, 1)
    return pairs[0]


def _compute_bounds(polygons: list[gdstk.Polygon]) -> Bounds2D:
    points = [np.asarray(poly.points, dtype=np.float64) for poly in polygons]
    if not points:
        raise ValueError("cannot compute bounds for an empty polygon list")

    xy = np.vstack(points)
    if xy.shape[1] != 2:
        raise ValueError("GDS polygon points must be 2D")

    min_x = float(np.min(xy[:, 0]))
    min_y = float(np.min(xy[:, 1]))
    max_x = float(np.max(xy[:, 0]))
    max_y = float(np.max(xy[:, 1]))
    return Bounds2D(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)
