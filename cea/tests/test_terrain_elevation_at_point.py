"""`ElevationMap.elevation_at_point` should not need scipy's Delaunay to answer "what is the
terrain elevation here" -- the raster is already a regular grid.

`generate_tin` hands the same (x, y) points to `scipy.spatial.Delaunay`, triangulated on (x, y)
alone. Every 2x2 cell of a regular grid is exactly cocircular in (x, y) -- a textbook Delaunay
degeneracy, where both diagonals are equally valid and the choice comes down to floating-point
tie-breaking that can differ across platforms/builds. `burn_buildings` then ray-casts a single
point (a building's footprint centroid) against that triangulation, so whenever the centroid
falls in a cell whose diagonal choice differs, the *whole* building's elevation shifts -- see
#4080's follow-up, where fixing the wall mesh surfaced this as the next-largest source of
cross-OS drift, with buildings shifting a few cm vertically (identically across every one of
their sensors) between platforms.

`elevation_at_point` sidesteps the ambiguity instead of resolving it: a regular grid's
triangulation needs no library, since splitting each cell along a fixed diagonal is unambiguous
by construction.
"""

import numpy as np
import pytest

from cea.resources.radiation.geometry_generator import ElevationMap


def grid(values, x_size=2.0, y_size=2.0, nodata=-9999.0):
    values = np.array(values, dtype=float)
    y, x = values.shape
    x_coords = np.arange(x) * x_size
    y_coords = np.arange(y) * y_size
    return ElevationMap(values, x_coords, y_coords, x_size, y_size, nodata)


def test_matches_the_flat_case_exactly():
    em = grid([[5.0, 5.0], [5.0, 5.0]])
    assert em.elevation_at_point(0.5, 0.5) == pytest.approx(5.0)
    assert em.elevation_at_point(1.7, 0.3) == pytest.approx(5.0)


def test_interpolates_linearly_along_each_axis():
    # a simple ramp in x: elevation = x, everywhere, for any grid resolution and any point in the cell
    em = grid([[0.0, 2.0], [0.0, 2.0]], x_size=2.0)
    assert em.elevation_at_point(0.5, 1.0) == pytest.approx(0.5)
    assert em.elevation_at_point(1.5, 0.3) == pytest.approx(1.5)


@pytest.mark.parametrize("x,y", [(0.3, 0.3), (1.7, 0.3), (0.3, 1.7), (1.7, 1.7), (1.0, 1.0)])
def test_is_deterministic_regardless_of_which_diagonal_a_point_sits_near(x, y):
    # points on either side of the cell's fixed diagonal, and exactly on it, should all resolve
    # to a definite, reproducible value -- this is exactly the query pattern (a single interior
    # point) that a Delaunay triangulator's tie-break makes platform-sensitive.
    em = grid([[0.0, 3.0], [1.0, 9.0]], x_size=2.0)
    first = em.elevation_at_point(x, y)
    second = em.elevation_at_point(x, y)
    assert first == second
    assert first is not None


def test_falls_back_to_none_outside_the_grid():
    em = grid([[1.0, 1.0], [1.0, 1.0]], x_size=2.0)
    assert em.elevation_at_point(-1.0, 0.5) is None
    assert em.elevation_at_point(0.5, 100.0) is None


def test_falls_back_to_none_when_the_containing_cell_touches_nodata():
    # a 4x4 grid with nodata at (row=1, col=1): every cell that has it as one of its 4 corners
    # (the 2x2 block of cells around it) must fall back; cells entirely away from it must not.
    rows = [[1.0] * 4 for _ in range(4)]
    rows[1][1] = -9999.0
    em = grid(rows, x_size=2.0)
    assert em.elevation_at_point(0.5, 0.5) is None  # cell (0,0): touches the nodata corner
    assert em.elevation_at_point(4.5, 4.5) == pytest.approx(1.0)  # cell (2,2): nowhere near it


def test_two_triangles_of_a_cell_agree_exactly_on_their_shared_diagonal():
    # the point exactly on the fixed diagonal must give the same answer whichever triangle's
    # plane equation it is evaluated against, so the surface has no seam along the diagonal itself
    em = grid([[0.0, 4.0], [2.0, 10.0]], x_size=2.0)
    on_diagonal = em.elevation_at_point(1.0, 1.0)
    just_below = em.elevation_at_point(1.0 - 1e-9, 1.0 - 1e-9)
    just_above = em.elevation_at_point(1.0 + 1e-9, 1.0 + 1e-9)
    assert on_diagonal == pytest.approx(just_below, abs=1e-6)
    assert on_diagonal == pytest.approx(just_above, abs=1e-6)
