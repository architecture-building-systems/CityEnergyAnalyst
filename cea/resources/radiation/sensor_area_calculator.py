import math

from compas.geometry import Frame, Point, Polygon, Vector, normal_polygon
from shapely.geometry import MultiPolygon
from shapely.geometry import Polygon as SPolygon
from shapely.geometry import box as sbox


def partition_polygon_by_grid(
    face: Polygon, grid_dx: float, grid_dy: float
) -> list[Polygon]:
    f = Frame.from_points(face.points[0], face.points[1], face.points[2])
    face_normal = Vector(*normal_polygon(face))
    if face_normal.dot(f.normal) < 0:
        f.flip()

    poly_local = f.to_local_coordinates(face)

    xs = [p.x for p in poly_local.points]
    ys = [p.y for p in poly_local.points]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    nx = max(2, int(math.ceil((xmax - xmin) / grid_dx)) + 1)
    ny = max(2, int(math.ceil((ymax - ymin) / grid_dy)) + 1)
    dx = (xmax - xmin) / (nx - 1)
    dy = (ymax - ymin) / (ny - 1)

    poly_s = SPolygon([(p.x, p.y) for p in poly_local.points])

    patches_world: list[Polygon] = []
    for j in range(ny - 1):
        y0, y1 = ymin + j * dy, ymin + (j + 1) * dy
        for i in range(nx - 1):
            x0, x1 = xmin + i * dx, xmin + (i + 1) * dx
            inter = sbox(x0, y0, x1, y1).intersection(poly_s)
            if inter.is_empty:
                continue
            if isinstance(inter, MultiPolygon):
                geoms: list[SPolygon] = [
                    g for g in inter.geoms if isinstance(g, SPolygon)
                ]
            elif isinstance(inter, SPolygon):
                geoms: list[SPolygon] = [inter]
            else:
                continue
            for g in geoms:
                if g.area < 1e-4: # avoid tiny patches
                    continue
                coords = list(g.exterior.coords)[:-1]
                poly_local_piece = Polygon([Point(x, y, 0.0) for x, y in coords])
                patches_world.append(f.to_world_coordinates(poly_local_piece))
    return patches_world


if __name__ == "__main__":
    from random import Random

    from compas.colors import Color
    from compas.geometry import Vector
    from compas.tolerance import Tolerance
    from compas_viewer import Viewer

    tol = Tolerance()
    tol.relative = 1e-10

    # --- tiny helper just to color patches nicely ---
    def draw_patches(viewer, patches, seed: int = 7):
        rng = Random(seed)
        for poly in patches:
            col = Color(rng.random(), rng.random(), rng.random())
            viewer.scene.add(poly, facecolor=col, linecolor=Color(0.15, 0.15, 0.15))

    def coverage_error(face, patches):
        total = sum(p.area for p in patches)
        return abs(total - face.area) / max(1.0, face.area)

    viewer = Viewer()

    # 1) Big-coordinate quad (far from origin)
    face_xy = Polygon(
        [
            Point(462690.407177893, 5250683.3713515345, 521.7213518470525),
            Point(462690.4071778929, 5250683.3713515345, 524.7213518470525),
            Point(462700.07827149925, 5250702.778322218, 523.9087382012959),
            Point(462700.07827149925, 5250702.778322218, 522.5339654928091),
        ]
    )
    patches1 = partition_polygon_by_grid(face_xy, grid_dx=1.0, grid_dy=1.0)
    move_vec = Vector.from_start_end(face_xy.centroid, Point(0, 0, 0))
    patches1_moved = [p.translated(move_vec) for p in patches1]
    draw_patches(viewer, patches1_moved, seed=3)
    print("err big-coord quad:", f"{coverage_error(face_xy, patches1):.2e}")

    # 2) Tilted rectangle in full 3D
    base_3d = Polygon.from_rectangle(point=Point(0, 0, 0), width=8, height=4)
    face_3d = (
        base_3d.rotated(math.radians(25), axis=Vector.Xaxis(), point=Point(0, 0, 0))
        .rotated(math.radians(-20), axis=Vector.Yaxis(), point=Point(0, 0, 0))
        .translated(Vector(0, 0, 3))
    )
    patches2 = partition_polygon_by_grid(face_3d, grid_dx=0.472, grid_dy=1.83)
    # viewer.scene.add(face_3d)
    draw_patches(viewer, patches2, seed=11)
    print("err tilted rect 3D:", f"{coverage_error(face_3d, patches2):.2e}")

    # 3) Concave “L” polygon in 3D (to exercise MultiPolygon splits)
    #    Build an L-shape in XY, then rotate/translate into space.
    L_xy = Polygon(
        [
            Point(0, 0, 0),
            Point(6, 0, 0),
            Point(6, 5, 0),
            Point(1, 1, 0),
            Point(5, 6, 0),
            Point(0, 6, 0),
        ]
    )
    L_3d = (
        L_xy.rotated(math.radians(35), axis=Vector.Xaxis(), point=Point(0, 0, 0))
        .rotated(math.radians(20), axis=Vector.Yaxis(), point=Point(0, 0, 0))
        .translated(Vector(-6, 5, 2.5))
    )
    patches3 = partition_polygon_by_grid(L_3d, grid_dx=0.8, grid_dy=0.8)
    # viewer.scene.add(L_3d)
    draw_patches(viewer, patches3, seed=29)
    print("err concave L 3D:", f"{coverage_error(L_3d, patches3):.2e}")

    viewer.show()
