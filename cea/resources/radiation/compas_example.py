from compas.geometry import Point, Line, Vector, Polygon, intersection_ray_mesh
from compas.datastructures import Mesh
from compas_occ.brep import OCCBrep
from compas_viewer import Viewer  # type: ignore
import math

UP = Vector(0, 0, 1)

def extrude_line_to_polygon(line: Line, height: float, direction: Vector = UP) -> Polygon:
    """Make a rectangular wall polygon by extruding a line along a direction."""
    v = direction.unitized().scaled(height)
    return Polygon([line.start, line.end, line.end.translated(v), line.start.translated(v)])

def open_window_in_wall(wall: Polygon, wwr: float) -> tuple[list[Polygon], Polygon]:
    """open a window in the center of the polygon, and cut the the original polygon with a hole.

    :param polygon: input polygon (typically a wall).
    :type polygon: Polygon
    :param wwr: window-to-wall ratio (0.0 - 1.0)
    :type wwr: float
    :return: original polygon with a hole (cut into four trapezoids through its corners), and the window polygon
    :rtype: tuple[list[Polygon], Polygon]
    """
    polygon_win: Polygon = wall.scaled(math.sqrt(wwr)) # scaled relative to world origin
    polygon_win.translate(Vector.from_start_end(polygon_win.centroid, wall.centroid))
    polygons_wall: list[Polygon] = []
    for i in range(len(wall.lines)):
        line_wall = wall.lines[i]
        line_win = polygon_win.lines[i]
        wall_trapezoid = Polygon([line_wall.start, line_wall.end, line_win.end, line_win.start])
        polygons_wall.append(wall_trapezoid)
    return polygons_wall, polygon_win
    
def ground_z_under(mesh: Mesh, origin_point, direction: Vector = UP) -> float:
    """Cast a ray and return the Z at the first hit via barycentric interpolation."""
    hit: list[tuple[int, float, float, float]] | None = intersection_ray_mesh((origin_point, direction), mesh.to_vertices_and_faces())
    if not hit:
        raise ValueError("No ground hit under the footprint.")
    fkey, u, v, _ = hit[0]
    a, b, c = mesh.face_points(fkey)  # triangle
    w = 1 - u - v
    return w * a.z + u * b.z + v * c.z

def make_floor_brep(footprint_at_z: Polygon, floor_height: float, wwr: float) -> OCCBrep:
    """Build one floor solid from: slab + walls + ceiling."""
    slab = footprint_at_z
    walls = [extrude_line_to_polygon(edge, floor_height, UP) for edge in slab.lines]
    if wwr > 0:
        walls_with_holes: list[Polygon] = []
        windows: list[Polygon] = []
        for i, wall in enumerate(walls):
            wall_with_hole, window = open_window_in_wall(wall, wwr)
            walls_with_holes.extend(wall_with_hole)
            windows.append(window)
        walls = walls_with_holes
    else:
        windows = []
    ceiling = slab.translated(Vector(0, 0, floor_height))
    return OCCBrep.from_polygons([slab, *walls, *windows, ceiling])

# --- scene setup --------------------------------------------------------------
viewer = Viewer()

# square footprint and a simple 'ground' mesh at z=10
footprint = Polygon([Point(0, 0, 0), Point(1, 0, 0), Point(1, 1, 0), Point(0, 1, 0)])
ground = Mesh.from_points([Point(0, 0, 10), Point(2, 0, 10), Point(2, 2, 10), Point(0, 2, 10)])
wwr = 0.4
floor_height = 3.0
floor_range = range(2, 5)

viewer.scene.add(footprint)
viewer.scene.add(ground)

# --- find elevation and place floors -----------------------------------------
elevation = ground_z_under(ground, footprint.centroid)
base_footprint = footprint.translated(Vector(0, 0, elevation))

breps: list[OCCBrep] = []
for floor in floor_range:  # floors 2, 3, 4 (building floats)
    z = floor * floor_height
    brep = make_floor_brep(base_footprint.translated(Vector(0, 0, z)), floor_height, wwr)
    breps.append(brep)

final_brep = breps[0].boolean_union(*breps[1:])
viewer.scene.add(final_brep)
viewer.show()
final_brep.faces[0].to_polygon().normal