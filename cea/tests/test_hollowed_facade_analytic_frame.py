"""`create_hollowed_facade` should not need an OCC boolean cut and mesh for the common case.

A wall face is always a planar quadrilateral (two footprint points x two z-levels, from
`calc_solid`'s loft), and `create_windows` makes the window a uniformly scaled copy of it about
its own centre. That makes "wall minus window" an exact affine picture frame: 4 trapezoids, one
per edge, running from each outer corner to the corresponding inner corner -- computable by
interpolation alone, with no boolean operation or mesh triangulation involved.

That matters for more than speed: `BRepMesh_IncrementalMesh` triangulating a symmetric hole in a
rectangle is exactly the kind of shape where a triangulator's floating-point tie-breaking differs
between OCCT builds, which is what made wall sensor grids differ across OSes (see #4080, and the
`compare-radiation` CI job from #4075 that measures it). The analytic frame sidesteps that
entirely for any facade that is a simple planar quad; anything else still falls back to the
original OCC path.
"""

import pytest
from py4design.py3dmodel import calculate, construct, modify

from cea.resources.radiation.geometry_generator import (
    create_hollowed_facade,
    create_windows,
)


def make_rectangle(width, height, y=0.0):
    corners = [(0, y, 0), (width, y, 0), (width, y, height), (0, y, height)]
    return construct.make_polygon(corners), (width / 2, y, height / 2)


@pytest.mark.parametrize("width,height,wwr", [(4.0, 3.0, 0.4), (10.0, 2.7, 0.15), (3.0, 3.0, 0.8), (6.0, 4.0, 0.01)])
def test_analytic_frame_matches_expected_area_and_uses_4_trapezoids(width, height, wwr):
    wall, ref_pt = make_rectangle(width, height)
    window = create_windows(wall, wwr, ref_pt)

    faces, _ = create_hollowed_facade(wall, window)

    assert len(faces) == 4, "a planar quad facade should give the exact 4-trapezoid frame, not an OCC mesh"
    total_area = sum(calculate.face_area(f) for f in faces)
    assert total_area == pytest.approx(width * height * (1 - wwr), rel=1e-9)


def test_analytic_frame_is_exact_for_a_non_rectangular_quad():
    # A trapezoidal wall (as a sloped facade could produce): not a rectangle, still a planar quad.
    corners = [(0, 0, 0), (4, 0, 0), (3, 0, 3), (1, 0, 3)]
    wall = construct.make_polygon(corners)
    ref_pt = calculate.face_midpt(wall)
    wwr = 0.3
    window = create_windows(wall, wwr, ref_pt)

    faces, _ = create_hollowed_facade(wall, window)

    assert len(faces) == 4
    total_area = sum(calculate.face_area(f) for f in faces)
    expected = calculate.face_area(wall) - calculate.face_area(window)
    assert total_area == pytest.approx(expected, rel=1e-9)


def test_falls_back_to_the_occ_path_for_a_non_quad_facade():
    # A triangular facade: not a quad, so the analytic shortcut does not apply.
    wall = construct.make_polygon([(0, 0, 0), (4, 0, 0), (2, 0, 3)])
    ref_pt = calculate.face_midpt(wall)
    wwr = 0.3
    window = create_windows(wall, wwr, ref_pt)

    faces, _ = create_hollowed_facade(wall, window)

    # the OCC mesh path triangulates instead of returning a 4-piece frame
    assert len(faces) != 4
    total_area = sum(calculate.face_area(f) for f in faces)
    expected = calculate.face_area(wall) - calculate.face_area(window)
    # the OCC path discards slivers below 1e-3 m2, so allow a small, one-sided tolerance
    assert total_area <= expected + 1e-9
    assert total_area == pytest.approx(expected, abs=1e-2)


def test_analytic_frame_matches_regardless_of_facade_orientation_in_space():
    # the same shape, rotated in 3D (not axis-aligned), should still give an exact 4-trapezoid frame
    width, height, wwr = 5.0, 3.5, 0.35
    wall, _ = make_rectangle(width, height, y=10.0)
    rotated_wall = modify.rotate(wall, (0, 10.0, 1.75), (0, 0, 1), 37)  # degrees, about the wall's own axis
    rotated_ref_pt = calculate.face_midpt(rotated_wall)

    window = create_windows(rotated_wall, wwr, rotated_ref_pt)
    faces, _ = create_hollowed_facade(rotated_wall, window)

    assert len(faces) == 4
    total_area = sum(calculate.face_area(f) for f in faces)
    assert total_area == pytest.approx(width * height * (1 - wwr), rel=1e-9)
