from compas.geometry import Point, Vector, Polygon, Brep, intersection_ray_mesh, Polyline
from compas.datastructures import Mesh


building_footprint = Polygon([Point(0, 0, 0), Point(1, 0, 0), Point(1, 1, 0), Point(0, 1, 0)])  # a square footprint
wwr = 0.4  # window-to-wall ratio
floor_range = range(2, 5)  # building is floating (doesn't have ground floor  and first floor) with floors 2, 3, 4
floor_height = 3  # each floor is 3m high
ground_mesh = Mesh.from_points([Point(0, 0, 10), Point(2, 0, 10), Point(2, 2, 10), Point(0, 2, 10)]) # a ground mesh at z=10

# calculate building's elevation
base_pt = building_footprint.centroid
proj_vector = Vector(0, 0, 1)  # project upwards
hits: list[tuple[int, float, float, float]] = intersection_ray_mesh((base_pt, proj_vector), ground_mesh.to_vertices_and_faces())
if hits:
    idx_face, u, v, t = hits[0]
    face_points = ground_mesh.face_points(idx_face)
    w = 1 - u - v
    p0 = face_points[0]
    p1 = face_points[1]
    p2 = face_points[2]
    elevation = w * p0.z + u * p1.z + v * p2.z
    print(f"Building base elevation: {elevation} m")

# create building footprint at the correct elevation
elevated_footprint: Polygon = building_footprint.transformed(Vector(0, 0, elevation))
for floor in floor_range:
    offset = floor * floor_height
    floor_polygon = elevated_footprint.transformed(Vector(0, 0, offset))
    wall