import math
from collections import defaultdict
from compas.geometry import Point, Vector, Polygon, Frame

EPS = 1e-9

def build_sensor_patches(face: Polygon, grid_dx: float, grid_dy: float
                         ) -> tuple[list[Point], list[list[Polygon]], list[float]]:
    """Return (sensor_points_world, patches_per_sensor_world, areas_per_sensor).

    Coverage is exact: the union of all patches equals `face`.
    Patches are disjoint (no overlaps), so areas per sensor sum to the face area.
    """
    # 1) Work in the face's local 2D frame
    f = Frame.from_points(face.points[0], face.points[1], face.points[2])
    pts_local = [f.to_local_coordinates(p) for p in face.points]
    poly_local = Polygon(pts_local)

    # 2) Regular grid covering the local bounding box
    xs = [p.x for p in pts_local]
    ys = [p.y for p in pts_local]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)

    nx = max(2, int(math.ceil((xmax - xmin) / grid_dx)) + 1)
    ny = max(2, int(math.ceil((ymax - ymin) / grid_dy)) + 1)
    dx = (xmax - xmin) / (nx - 1) if nx > 1 else grid_dx
    dy = (ymax - ymin) / (ny - 1) if ny > 1 else grid_dy

    # Grid node coordinates and "inside" mask
    idx_in: set[tuple[int, int]] = set()
    coords: dict[tuple[int, int], tuple[float, float]] = {}

    # keep sensors keyed by grid index + their insertion order
    sensors_by_key: dict[tuple[int, int], Point] = {}
    sensor_keys_order: list[tuple[int, int]] = []

    for j in range(ny):
        py = ymin + j * dy
        for i in range(nx):
            px = xmin + i * dx
            coords[(i, j)] = (px, py)
            p_local = Point(px, py, 0.0)
            if p_local.in_polygon(poly_local):
                key = (i, j)
                idx_in.add(key)
                sensors_by_key[key] = f.to_world_coordinates(p_local)
                sensor_keys_order.append(key)

    if not idx_in:
        c = poly_local.centroid
        return [f.to_world_coordinates(c)], [[poly_local]], [poly_local.area]

    patches_local: defaultdict[tuple[int, int], list[Polygon]] = defaultdict(list)

    # Helper to choose owner for a cell patch
    def choose_owner(i: int, j: int, centroid_xy: tuple[float, float]) -> tuple[int, int]:
        # Prefer inside corners of this cell (deterministic priority)
        candidates = [(i, j), (i + 1, j), (i, j + 1), (i + 1, j + 1)]
        inside_corners = [c for c in candidates if c in idx_in]
        if inside_corners:
            return inside_corners[0]
        # If none of the 4 corners are inside (tiny wedge cases), pick nearest inside node globally
        cx, cy = centroid_xy
        best = None
        best_d2 = float("inf")
        for (ii, jj) in idx_in:
            x, y = coords[(ii, jj)]
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if d2 < best_d2:
                best_d2 = d2
                best = (ii, jj)
        assert best is not None
        return best

    # 3) Visit each grid cell, clip with polygon, assign its patch
    for j in range(ny - 1):
        y0 = ymin + j * dy
        y1 = y0 + dy
        for i in range(nx - 1):
            x0 = xmin + i * dx
            x1 = x0 + dx

            # Cell rectangle (in local XY)
            cell_rect = Polygon([
                Point(x0, y0, 0.0),
                Point(x1, y0, 0.0),
                Point(x1, y1, 0.0),
                Point(x0, y1, 0.0),
            ])

            # Intersection with the face
            try:
                patch = cell_rect.boolean_intersection(poly_local)
            except IndexError:
                patch = None

            if not patch or patch.area <= 0:
                continue

            # Choose owner and assign
            centroid = patch.centroid
            owner = choose_owner(i, j, (centroid.x, centroid.y))
            patches_local[owner].append(patch)

    sensors_world: list[Point] = []
    patches_per_sensor_world: list[list[Polygon]] = []
    areas_per_sensor: list[float] = []

    for key in sensor_keys_order:
        sensors_world.append(sensors_by_key[key])
        local_patches = patches_local.get(key, [])
        patches_world = [
            Polygon([f.to_world_coordinates(p) for p in patch.points])
            for patch in local_patches
        ]
        patches_per_sensor_world.append(patches_world)
        areas_per_sensor.append(sum(p.area for p in local_patches))

    return sensors_world, patches_per_sensor_world, areas_per_sensor


def patch_centers_from_patches(patches_per_sensor_world: list[list[Polygon]], nudge: float = 0.0):
    """Flatten patches and return (centers, flat_patches, areas, owners).

    centers: centroid point of each patch (optionally nudged along patch normal)
    flat_patches: the patches themselves in the same order
    areas: area for each patch
    owners: index of the original inside-node that owned the patch (if you need the mapping)
    """
    centers: list[Point] = []
    flat_patches: list[Polygon] = []
    areas: list[float] = []
    owners: list[int] = []

    for owner_idx, patch_list in enumerate(patches_per_sensor_world):
        for poly in patch_list:
            c = poly.centroid
            if nudge:  # tiny push off-plane if you ever hit coplanar issues
                f = Frame.from_points(poly.points[0], poly.points[1], poly.points[2])
                c = c.translated(f.zaxis.unitized().scaled(nudge))
            centers.append(c)
            flat_patches.append(poly)
            areas.append(poly.area)
            owners.append(owner_idx)

    return centers, flat_patches, areas, owners
# ------------------------------- demo ---------------------------------------

if __name__ == "__main__":
    from random import Random
    from compas.colors import Color
    from compas_viewer import Viewer


    def draw_sensor_groups(viewer, sensors, patches_per_sensor, seed: int = 3):
        """Color each sensor and its patches with the same random color."""
        rng = Random(seed)
        for sensor, patches in zip(sensors, patches_per_sensor):
            col = Color(rng.random(), rng.random(), rng.random())
            # draw the patches owned by this sensor
            for poly in patches:
                viewer.scene.add(poly, facecolor=col, linecolor=Color(0.15, 0.15, 0.15))
            # draw the sensor itself on top
            viewer.scene.add(sensor, pointsize=20, pointcolor=col)

    viewer = Viewer()

    # 1) Rotated rectangle in XY
    base_xy = Polygon.from_rectangle(point=Point(0, 0, 0), width=10, height=5)
    face_xy = base_xy.rotated(math.radians(30), axis=Vector.Zaxis(), point=base_xy.centroid)

    sensors1, patches1, areas1 = build_sensor_patches(face_xy, grid_dx=0.8, grid_dy=0.6)
    draw_sensor_groups(viewer, sensors1, patches1, seed=7)

    # swap to patch-centric sensors
    centers1, patches1_flat, areas1_flat, owners1 = patch_centers_from_patches(patches1)
    print(f"original sensors: {len(sensors1)}, now patches: {len(patches1_flat)}, areas number: {len(areas1_flat)}, owners: {len(owners1)}")

    # draw
    for poly in patches1_flat:
        viewer.scene.add(poly)
    for p in centers1:
        viewer.scene.add(p, pointsize=4)

    # coverage check (unchanged)
    err1 = abs(sum(areas1_flat) - face_xy.area) / max(1.0, face_xy.area)
    print(f"relative area error XY: {err1:.2e}")

    # 2) Tilted rectangle in 3D
    base_3d = Polygon.from_rectangle(point=Point(0, 0, 0), width=8, height=4)
    face_3d = (
        base_3d
        .rotated(math.radians(25), axis=Vector.Xaxis(), point=Point(0, 0, 0))
        .rotated(math.radians(-20), axis=Vector.Yaxis(), point=Point(0, 0, 0))
        .translated(Vector(0, 0, 3))
    )

    sensors2, patches2, areas2 = build_sensor_patches(face_3d, grid_dx=0.472, grid_dy=1.83)
    viewer.scene.add(face_3d)

    for sensor_patches in patches2:
        for poly in sensor_patches:
            viewer.scene.add(poly)

    for p in sensors2:
        viewer.scene.add(p, pointsize=10)

    # Coverage check (should be ~0)
    err1 = abs(sum(a for a in areas1) - face_xy.area) / max(1.0, face_xy.area)
    err2 = abs(sum(a for a in areas2) - face_3d.area) / max(1.0, face_3d.area)
    print(f"relative area error XY:  {err1:.2e}")
    print(f"relative area error 3D: {err2:.2e}")
    # 3) One face from a tetrahedron, rotated/translated in 3D
    s = 3.0  # edge length
    A = Point(0.0, 0.0, 0.0)
    B = Point(s, 0.0, 0.0)
    C = Point(0.5 * s, (math.sqrt(3) / 2.0) * s, 0.0)
    D = Point(0.5 * s, (math.sqrt(3) / 6.0) * s, (math.sqrt(2.0 / 3.0)) * s)

    # pick any triangular face of the tetrahedron
    face_t = Polygon([A, B, D])

    # rotate around world axes and move somewhere in space
    face_t = face_t.rotated(math.radians(35), axis=Vector.Xaxis(), point=Point(0, 0, 0))
    face_t = face_t.rotated(math.radians(15), axis=Vector.Yaxis(), point=Point(0, 0, 0))
    face_t = face_t.rotated(math.radians(-20), axis=Vector.Zaxis(), point=Point(0, 0, 0))
    face_t = face_t.translated(Vector(6, -6, 3))

    sensors3, patches3, areas3 = build_sensor_patches(face_t, grid_dx=0.4, grid_dy=0.4)

    viewer.scene.add(face_t)
    for sensor_patches in patches3:
        for poly in sensor_patches:
            viewer.scene.add(poly)
    for p in sensors3:
        viewer.scene.add(p, pointsize=10)

    # optional coverage check (should be ~0)
    err3 = abs(sum(areas3) - face_t.area) / max(1.0, face_t.area)
    print(f"relative area error (tetra face): {err3:.2e}")

    viewer.show()
