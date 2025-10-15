from __future__ import annotations

import os
import pickle
from dataclasses import MISSING, dataclass, field, fields
from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
    from compas.geometry import Polygon, Vector


SURFACE_TYPES = ["walls", "windows", "roofs", "undersides"]
SURFACE_DIRECTION_LABELS = {
    "windows_east",
    "windows_west",
    "windows_south",
    "windows_north",
    "walls_east",
    "walls_west",
    "walls_south",
    "walls_north",
    "roofs_top",
    "undersides_bottom",
}


class SurfaceGroup(NamedTuple):
    faces: list[Polygon]
    orientations: list[str]
    normals: list[Vector]
    intersects: list[bool]


@dataclass(slots=True)
class BuildingGeometryForRadiation(object):
    name: str
    footprint: list[Polygon]  # footprint means the building's projection on the ground,
    walls: list[Polygon]
    roofs: list[Polygon]

    # optional slots
    terrain_elevation: float = field(
        default=0.0
    )  # elevation of the building footprint's middle point.
    windows: list[Polygon] = field(default_factory=list)
    orientation_windows: list[str] = field(default_factory=list)
    normals_windows: list[Vector] = field(default_factory=list)
    intersect_windows: list[bool] = field(default_factory=list)

    orientation_walls: list[str] = field(default_factory=list)
    normals_walls: list[Vector] = field(default_factory=list)
    intersect_walls: list[bool] = field(default_factory=list)

    orientation_roofs: list[str] = field(default_factory=list)
    normals_roofs: list[Vector] = field(default_factory=list)
    intersect_roofs: list[bool] = field(default_factory=list)

    undersides: list[Polygon] = field(
        default_factory=list
    )  # undersides means the bottom surface of the building in case it is elevated above the ground.
    orientation_undersides: list[str] = field(default_factory=list)
    normals_undersides: list[Vector] = field(default_factory=list)
    intersect_undersides: list[bool] = field(default_factory=list)

    def group(self, srf_type: str) -> SurfaceGroup:
        mapping_dict = {
            "walls": (
                self.walls,
                self.orientation_walls,
                self.normals_walls,
                self.intersect_walls,
            ),
            "windows": (
                self.windows,
                self.orientation_windows,
                self.normals_windows,
                self.intersect_windows,
            ),
            "roofs": (
                self.roofs,
                self.orientation_roofs,
                self.normals_roofs,
                self.intersect_roofs,
            ),
            "undersides": (
                self.undersides,
                self.orientation_undersides,
                self.normals_undersides,
                self.intersect_undersides,
            ),
        }
        return SurfaceGroup(*mapping_dict[srf_type])

    def __getstate__(self) -> list[Any]:
        # Use fields(type(self)) so static type checkers recognize a dataclass type
        return [getattr(self, f.name) for f in fields(type(self))]

    def __setstate__(self, data: list[Any]) -> None:
        for f, v in zip(fields(type(self)), data):
            setattr(self, f.name, v)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BuildingGeometryForRadiation":
        fs = fields(cls)
        valid = {f.name for f in fs}
        # Only pass known, non-None keys so defaults kick in for optionals
        kwargs = {k: v for k, v in d.items() if k in valid and v is not None}

        # Required = fields with no default and no default_factory
        required = [
            f.name for f in fs if f.default is MISSING and f.default_factory is MISSING
        ]
        missing = [name for name in required if name not in kwargs]
        if missing:
            raise ValueError(f"Missing required field(s): {', '.join(missing)}")

        return cls(**kwargs)

    @classmethod
    def load(cls, pickle_location: str) -> "BuildingGeometryForRadiation":
        with open(pickle_location, "rb") as fp:
            state = pickle.load(fp)

        if not isinstance(state, list):
            raise TypeError(f"Expected a list state, got {type(state).__name__}")

        obj = cls.__new__(cls)  # bypass __init__
        obj.__setstate__(state)  # restore using your dataclass fields order
        return obj

    def save(self, pickle_location: str) -> str:
        directory = os.path.dirname(pickle_location)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(pickle_location, "wb") as f:
            pickle.dump(self.__getstate__(), f)
        return pickle_location
