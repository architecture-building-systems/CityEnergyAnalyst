##Copyright 2008-2013 Jelle Feringa (jelleferinga@gmail.com)
##
##This file is part of pythonOCC.
##
##pythonOCC is free software: you can redistribute it and/or modify
##it under the terms of the GNU Lesser General Public License as published by
##the Free Software Foundation, either version 3 of the License, or
##(at your option) any later version.
##
##pythonOCC is distributed in the hope that it will be useful,
##but WITHOUT ANY WARRANTY; without even the implied warranty of
##MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##GNU Lesser General Public License for more details.
##
##You should have received a copy of the GNU Lesser General Public License
##along with pythonOCC.  If not, see <http://www.gnu.org/licenses/>

from OCC.BRep import BRep_Tool_Surface, BRep_Tool
from OCC.BRepTopAdaptor import BRepTopAdaptor_FClass2d
from OCC.Geom import Geom_Curve
from OCC.GeomAPI import GeomAPI_ProjectPointOnSurf
from OCC.GeomLib import GeomLib_IsPlanarSurface
from OCC.TopAbs import TopAbs_IN
from OCC.TopExp import topexp
from OCC.TopoDS import TopoDS_Vertex, TopoDS_Face, TopoDS_Edge
from OCC.GeomLProp import GeomLProp_SLProps
from OCC.BRepTools import breptools_UVBounds
from OCC.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_HSurface
from OCC.ShapeAnalysis import ShapeAnalysis_Surface
from OCC.GeomProjLib import geomprojlib
from OCC.Adaptor3d import Adaptor3d_IsoCurve
from OCC.gp import gp_Pnt2d, gp_Dir

from OCCUtils.base import BaseObject
from OCCUtils.edge import Edge
from OCCUtils.Construct import TOLERANCE, to_adaptor_3d
from OCCUtils.Topology import Topo, WireExplorer


class DiffGeomSurface(object):
    def __init__(self, instance):
        self.instance = instance
        self._curvature = None
        self._curvature_initiated = False

    def curvature(self, u, v):
        '''returns the curvature at the u parameter
        the curvature object can be returned too using
        curvatureType == curvatureType
        curvatureTypes are:
            gaussian
            minimum
            maximum
            mean
            curvatureType
        '''
        if not self._curvature_initiated:
            self._curvature = GeomLProp_SLProps(self.instance.surface_handle, u, v, 2, 1e-7)

        _domain = self.instance.domain()
        if u in _domain or v in _domain:
            print('<<<CORRECTING DOMAIN...>>>')
            div = 1000
            delta_u, delta_v = (_domain[0] - _domain[1])/div, (_domain[2] - _domain[3])/div

            if u in _domain:
                low, hi = u-_domain[0], u-_domain[1]
                if low < hi:
                    u = u - delta_u
                else:
                    u = u + delta_u

            if v in _domain:
                low, hi = v-_domain[2], v-_domain[3]
                if low < hi:
                    v = v - delta_v
                else:
                    v = v + delta_v

        self._curvature.SetParameters(u, v)
        self._curvature_initiated = True

        return self._curvature

    def gaussian_curvature(self, u, v):
        return self.curvature(u, v).GaussianCurvature()

    def min_curvature(self, u, v):
        return self.curvature(u, v).MinCurvature()

    def mean_curvature(self, u, v):
        return self.curvature(u, v).MeanCurvature()

    def max_curvature(self, u, v):
        return self.curvature(u, v).MaxCurvature()

    def normal(self, u, v):
        # TODO: should make this return a gp_Vec
        curv = self.curvature(u, v)
        if curv.IsNormalDefined():
            return curv.Normal()
        else:
            raise ValueError('normal is not defined at u,v: {0}, {1}'.format(u, v))

    def tangent(self, u, v):
        dU, dV = gp_Dir(), gp_Dir()
        curv = self.curvature(u, v)
        if curv.IsTangentUDefined() and curv.IsTangentVDefined():
            curv.TangentU(dU), curv.TangentV(dV)
            return dU, dV
        else:
            return None, None

    def radius(self, u, v):
        '''returns the radius at u
        '''
        # TODO: SHOULD WE RETURN A SIGNED RADIUS? ( get rid of abs() )?
        try:
            _crv_min = 1./self.min_curvature(u, v)
        except ZeroDivisionError:
            _crv_min = 0.

        try:
            _crv_max = 1./self.max_curvature(u, v)
        except ZeroDivisionError:
            _crv_max = 0.
        return abs((_crv_min+_crv_max)/2.)


class Face(TopoDS_Face, BaseObject):
    """high level surface API
    object is a Face if part of a Solid
    otherwise the same methods do apply, apart from the topology obviously
    """
    def __init__(self, face):
        '''
        '''
        assert isinstance(face, TopoDS_Face), 'need a TopoDS_Face, got a %s' % face.__class__
        assert not face.IsNull()
        super(Face, self).__init__()
        BaseObject.__init__(self, 'face')
        # we need to copy the base shape using the following three
        # lines
        assert self.IsNull()
        self.TShape(face.TShape())
        self.Location(face.Location())
        self.Orientation(face.Orientation())
        assert not self.IsNull()

        # cooperative classes
        self.DiffGeom = DiffGeomSurface(self)

        # STATE; whether cooperative classes are yet initialized
        self._curvature_initiated = False
        self._geometry_lookup_init = False

        #===================================================================
        # properties
        #===================================================================
        self._h_srf = None
        self._srf = None
        self._adaptor = None
        self._adaptor_handle = None
        self._classify_uv = None  # cache the u,v classifier, no need to rebuild for every sample
        self._topo = None

        # aliasing of useful methods
        def is_u_periodic(self):
            return self.adaptor.IsUPeriodic()

        def is_v_periodic(self):
            return self.adaptor.IsVPeriodic()

        def is_u_closed(self):
            return self.adaptor.IsUClosed()

        def is_v_closed(self):
            return self.adaptor.IsVClosed()

        def is_u_rational(self):
            return self.adaptor.IsURational()

        def is_v_rational(self):
            return self.adaptor.IsVRational()

        def u_degree(self):
            return self.adaptor.UDegree()

        def v_degree(self):
            return self.adaptor.VDegree()

        def u_continuity(self):
            return self.adaptor.UContinuity()

        def v_continuity(self):
            return self.adaptor.VContinuity()

    def domain(self):
        '''the u,v domain of the curve
        :return: UMin, UMax, VMin, VMax
        '''
        return breptools_UVBounds(self)

    def mid_point(self):
        """
        :return: the parameter at the mid point of the face,
        and its corresponding gp_Pnt
        """
        u_min, u_max, v_min, v_max = self.domain()
        u_mid = (u_min + u_max) / 2.
        v_mid = (v_min + v_max) / 2.
        return ((u_mid, v_mid), self.adaptor.Value(u_mid, v_mid))

    @property
    def topo(self):
        if self._topo is not None:
            return self._topo
        else:
            self._topo = Topo(self)
            return self._topo

    @property
    def surface(self):
        if self._srf is None or self.is_dirty:
            self._h_srf = BRep_Tool_Surface(self)
            self._srf = self._h_srf.GetObject()
        return self._srf

    @property
    def surface_handle(self):
        if self._h_srf is None or self.is_dirty:
            self.surface  # force building handle
        return self._h_srf

    @property
    def adaptor(self):
        if self._adaptor is not None and not self.is_dirty:
            pass
        else:
            self._adaptor = BRepAdaptor_Surface(self)
            self._adaptor_handle = BRepAdaptor_HSurface()
            self._adaptor_handle.Set(self._adaptor)
        return self._adaptor

    @property
    def adaptor_handle(self):
        if self._adaptor_handle is not None and not self.is_dirty:
            pass
        else:
            self.adaptor
        return self._adaptor_handle

    def is_closed(self):
        sa = ShapeAnalysis_Surface(self.surface_handle)
        # sa.GetBoxUF()
        return sa.IsUClosed(), sa.IsVClosed()

    def is_planar(self, tol=TOLERANCE):
        '''checks if the surface is planar within a tolerance
        :return: bool, gp_Pln
        '''
        print(self.surface_handle)
        is_planar_surface = GeomLib_IsPlanarSurface(self.surface_handle, tol)
        return is_planar_surface.IsPlanar()

    def is_trimmed(self):
        """
        :return: True if the Wire delimiting the Face lies on the bounds
        of the surface
        if this is not the case, the wire represents a contour that delimits
        the face [ think cookie cutter ]
        and implies that the surface is trimmed
        """
        _round = lambda x: round(x, 3)
        a = map(_round, breptools_UVBounds(self))
        b = map(_round, self.adaptor.Surface().Surface().GetObject().Bounds())
        if a != b:
            print('a,b', a, b)
            return True
        return False

    def on_trimmed(self, u, v):
        '''tests whether the surface at the u,v parameter has been trimmed
        '''
        if self._classify_uv is None:
            self._classify_uv = BRepTopAdaptor_FClass2d(self, 1e-9)
        uv = gp_Pnt2d(u, v)
        if self._classify_uv.Perform(uv) == TopAbs_IN:
            return True
        else:
            return False

    def parameter_to_point(self, u, v):
        '''returns the coordinate at u,v
        '''
        return self.surface.Value(u, v)

    def point_to_parameter(self, pt):
        '''
        returns the uv value of a point on a surface
        @param pt:
        '''
        sas = ShapeAnalysis_Surface(self.surface_handle)
        uv = sas.ValueOfUV(pt, self.tolerance)
        return uv.Coord()

    def continuity_edge_face(self, edge, face):
        """
        compute the continuity between two faces at :edge:

        :param edge: an Edge or TopoDS_Edge from :face:
        :param face: a Face or TopoDS_Face
        :return: bool, GeomAbs_Shape if it has continuity, otherwise
         False, None
        """
        bt = BRep_Tool()
        if bt.HasContinuity(edge, self, face):
            continuity = bt.Continuity(edge, self, face)
            return True, continuity
        else:
            return False, None

#===========================================================================
#    Surface.project
#    project curve, point on face
#===========================================================================

    def project_vertex(self, pnt, tol=TOLERANCE):
        '''projects self with a point, curve, edge, face, solid
        method wraps dealing with the various topologies

        if other is a point:
            returns uv, point

        '''
        if isinstance(pnt, TopoDS_Vertex):
            pnt = BRep_Tool.Pnt(pnt)

        proj = GeomAPI_ProjectPointOnSurf(pnt, self.surface_handle, tol)
        uv = proj.LowerDistanceParameters()
        proj_pnt = proj.NearestPoint()

        return uv, proj_pnt

    def project_curve(self, other):
        # this way Geom_Circle and alike are valid too
        if (isinstance(other, TopoDS_Edge) or
            isinstance(other, Geom_Curve) or
           issubclass(other, Geom_Curve)):
                # convert edge to curve
                first, last = topexp.FirstVertex(other), topexp.LastVertex(other)
                lbound, ubound = BRep_Tool().Parameter(first, other), BRep_Tool().Parameter(last, other)
                other = BRep_Tool.Curve(other, lbound, ubound).GetObject()
                return geomprojlib.Project(other, self.surface_handle)

    def project_edge(self, edg):
        if hasattr(edg, 'adaptor'):
            return self.project_curve(self, self.adaptor)
        return self.project_curve(self, to_adaptor_3d(edg))

    def iso_curve(self, u_or_v, param):
        """
        get the iso curve from a u,v + parameter
        :param u_or_v:
        :param param:
        :return:
        """
        uv = 0 if u_or_v == 'u' else 1
        iso = Adaptor3d_IsoCurve(self.adaptor_handle.GetHandle(), uv, param)
        return iso

    def edges(self):
        return [Edge(i) for i in WireExplorer(next(self.topo.wires())).ordered_edges()]

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.__repr__()

if __name__ == "__main__":
    from OCC.BRepPrimAPI import BRepPrimAPI_MakeSphere
    sph = BRepPrimAPI_MakeSphere(1, 1).Face()
    fc = Face(sph)
    print(fc.is_trimmed())
    print(fc.is_planar())