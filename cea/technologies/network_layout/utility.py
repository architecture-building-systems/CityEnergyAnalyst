"""
*********
Shapefile
*********

Generates a networkx.DiGraph from point and line shapefiles.

"The Esri Shapefile or simply a shapefile is a popular geospatial vector
data format for geographic information systems software. It is developed
and regulated by Esri as a (mostly) open specification for data
interoperability among Esri and other software products."
See https://en.wikipedia.org/wiki/Shapefile for additional information.
"""



#    Copyright (C) 2004-2019 by
#    Ben Reilly <benwreilly@gmail.com>
#    Aric Hagberg <hagberg@lanl.gov>
#    Dan Schult <dschult@colgate.edu>
#    Pieter Swart <swart@lanl.gov>
#    All rights reserved.
#    BSD license.
import networkx as nx
__author__ = """Ben Reilly (benwreilly@gmail.com)"""
__all__ = ['read_shp', 'write_shp', 'from_numpy_matrix']


def read_shp(path, simplify=True, geom_attrs=True, strict=True):
    """Generates a networkx.DiGraph from shapefiles. Point geometries are
    translated into nodes, lines into edges. Coordinate tuples are used as
    keys. Attributes are preserved, line geometries are simplified into start
    and end coordinates. Accepts a single shapefile or directory of many
    shapefiles.

    "The Esri Shapefile or simply a shapefile is a popular geospatial vector
    data format for geographic information systems software [1]_."

    :param str path: File, directory, or filename to read.
    :param bool simplify: If True, simplify line geometries to start and end coordinates.
                          If False, and line feature geometry has multiple segments, the
                          non-geometric attributes for that feature will be repeated for each
                          edge comprising that feature.
    :param bool geom_attrs: If True, include the Wkb, Wkt and Json geometry attributes with
                            each edge.
                            NOTE:  if these attributes are available, write_shp will use them
                            to write the geometry.  If nodes store the underlying coordinates for
                            the edge geometry as well (as they do when they are read via
                            this method) and they change, your geometry will be out of sync.

    :param bool strict: If True, raise NetworkXError when feature geometry is missing or
                        GeometryType is not supported.
                        If False, silently ignore missing or unsupported geometry in features.

    :return: the NetworkX graph

    :raises ImportError: If ogr module is not available.
    :raises RuntimeError: If file cannot be open or read.
    :raises NetworkXError:  If strict=True and feature is missing geometry or GeometryType is not supported.

    .. [1] https://en.wikipedia.org/wiki/Shapefile
    """
    try:
        from osgeo import ogr
    except ImportError:
        raise ImportError("read_shp requires OGR: http://www.gdal.org/")

    if not isinstance(path, str):
        return

    net = nx.DiGraph()
    shp = ogr.Open(path)
    if shp is None:
        raise RuntimeError("Unable to open {}".format(path))
    for lyr in shp:
        fields = [x.GetName() for x in lyr.schema]
        for f in lyr:
            g = f.geometry()
            if g is None:
                if strict:
                    raise nx.NetworkXError("Bad data: feature missing geometry")
                else:
                    continue
            flddata = [f.GetField(f.GetFieldIndex(x)) for x in fields]
            attributes = dict(zip(fields, flddata))
            attributes["ShpName"] = lyr.GetName()
            # Note:  Using layer level geometry type
            if g.GetGeometryType() == ogr.wkbPoint:
                net.add_node((g.GetPoint_2D(0)), **attributes)
            elif g.GetGeometryType() in (ogr.wkbLineString,
                                         ogr.wkbMultiLineString):
                for edge in edges_from_line(g, attributes, simplify,
                                            geom_attrs):
                    e1, e2, attr = edge
                    net.add_edge(e1, e2)
                    net[e1][e2].update(attr)
            else:
                if strict:
                    raise nx.NetworkXError("GeometryType {} not supported".
                                           format(g.GetGeometryType()))

    return net



def edges_from_line(geom, attrs, simplify=True, geom_attrs=True):
    """
    Generate edges for each line in geom
    Written as a helper for read_shp

    Parameters
    ----------

    geom:  ogr line geometry
        To be converted into an edge or edges

    attrs:  dict
        Attributes to be associated with all geoms

    simplify:  bool
        If True, simplify the line as in read_shp

    geom_attrs:  bool
        If True, add geom attributes to edge as in read_shp


    Returns
    -------
     edges:  generator of edges
        each edge is a tuple of form
        (node1_coord, node2_coord, attribute_dict)
        suitable for expanding into a networkx Graph add_edge call
    """
    try:
        from osgeo import ogr
    except ImportError:
        raise ImportError("edges_from_line requires OGR: http://www.gdal.org/")

    if geom.GetGeometryType() == ogr.wkbLineString:
        if simplify:
            edge_attrs = attrs.copy()
            last = geom.GetPointCount() - 1
            if geom_attrs:
                edge_attrs["Wkb"] = geom.ExportToWkb()
                edge_attrs["Wkt"] = geom.ExportToWkt()
                edge_attrs["Json"] = geom.ExportToJson()
            yield (geom.GetPoint_2D(0), geom.GetPoint_2D(last), edge_attrs)
        else:
            for i in range(0, geom.GetPointCount() - 1):
                pt1 = geom.GetPoint_2D(i)
                pt2 = geom.GetPoint_2D(i + 1)
                edge_attrs = attrs.copy()
                if geom_attrs:
                    segment = ogr.Geometry(ogr.wkbLineString)
                    segment.AddPoint_2D(pt1[0], pt1[1])
                    segment.AddPoint_2D(pt2[0], pt2[1])
                    edge_attrs["Wkb"] = segment.ExportToWkb()
                    edge_attrs["Wkt"] = segment.ExportToWkt()
                    edge_attrs["Json"] = segment.ExportToJson()
                    del segment
                yield (pt1, pt2, edge_attrs)

    elif geom.GetGeometryType() == ogr.wkbMultiLineString:
        for i in range(geom.GetGeometryCount()):
            geom_i = geom.GetGeometryRef(i)
            for edge in edges_from_line(geom_i, attrs, simplify, geom_attrs):
                yield edge


def write_shp(G, outdir):
    """Writes a networkx.DiGraph to two shapefiles, edges and nodes.
    Nodes and edges are expected to have a Well Known Binary (Wkb) or
    Well Known Text (Wkt) key in order to generate geometries. Also
    acceptable are nodes with a numeric tuple key (x,y).

    "The Esri Shapefile or simply a shapefile is a popular geospatial vector
    data format for geographic information systems software [2]_."

    :param str outdir : directory path, Output directory for the two shapefiles.
    :rtype: None

    Examples::

        nx.write_shp(digraph, '/shapefiles') # doctest +SKIP

    .. [2] https://en.wikipedia.org/wiki/Shapefile
    """
    try:
        from osgeo import ogr
    except ImportError:
        raise ImportError("write_shp requires OGR: http://www.gdal.org/")
    # easier to debug in python if ogr throws exceptions
    ogr.UseExceptions()

    def netgeometry(key, data):
        if 'Wkb' in data:
            geom = ogr.CreateGeometryFromWkb(data['Wkb'])
        elif 'Wkt' in data:
            geom = ogr.CreateGeometryFromWkt(data['Wkt'])
        elif type(key[0]).__name__ == 'tuple':  # edge keys are packed tuples
            geom = ogr.Geometry(ogr.wkbLineString)
            _from, _to = key[0], key[1]
            try:
                geom.SetPoint(0, *_from)
                geom.SetPoint(1, *_to)
            except TypeError:
                # assume user used tuple of int and choked ogr
                _ffrom = [float(x) for x in _from]
                _fto = [float(x) for x in _to]
                geom.SetPoint(0, *_ffrom)
                geom.SetPoint(1, *_fto)
        else:
            geom = ogr.Geometry(ogr.wkbPoint)
            try:
                geom.SetPoint(0, *key)
            except TypeError:
                # assume user used tuple of int and choked ogr
                fkey = [float(x) for x in key]
                geom.SetPoint(0, *fkey)

        return geom

    # Create_feature with new optional attributes arg (should be dict type)
    def create_feature(geometry, lyr, attributes=None):
        feature = ogr.Feature(lyr.GetLayerDefn())
        feature.SetGeometry(g)
        if attributes is not None:
            # Loop through attributes, assigning data to each field
            for field, data in attributes.items():
                feature.SetField(field, data)
        lyr.CreateFeature(feature)
        feature.Destroy()

    # Conversion dict between python and ogr types
    OGRTypes = {int: ogr.OFTInteger, str: ogr.OFTString, float: ogr.OFTReal}

    # Check/add fields from attribute data to Shapefile layers
    def add_fields_to_layer(key, value, fields, layer):
        # Field not in previous edges so add to dict
        if type(value) in OGRTypes:
            fields[key] = OGRTypes[type(value)]
        else:
            # Data type not supported, default to string (char 80)
            fields[key] = ogr.OFTString
        # Create the new field
        newfield = ogr.FieldDefn(key, fields[key])
        layer.CreateField(newfield)


    drv = ogr.GetDriverByName("ESRI Shapefile")
    shpdir = drv.CreateDataSource(outdir)
    # delete pre-existing output first otherwise ogr chokes
    try:
        shpdir.DeleteLayer("nodes")
    except Exception:
        pass
    nodes = shpdir.CreateLayer("nodes", None, ogr.wkbPoint)

    # Storage for node field names and their data types
    node_fields = {}

    def create_attributes(data, fields, layer):
        attributes = {}  # storage for attribute data (indexed by field names)
        for key, value in data.items():
            # Reject spatial data not required for attribute table
            if (key != 'Json' and key != 'Wkt' and key != 'Wkb'
                    and key != 'ShpName'):
                # Check/add field and data type to fields dict
                if key not in fields:
                    add_fields_to_layer(key, value, fields, layer)
                # Store the data from new field to dict for CreateLayer()
                attributes[key] = value
        return attributes, layer

    for n in G:
        data = G.nodes[n]
        g = netgeometry(n, data)
        attributes, nodes = create_attributes(data, node_fields, nodes)
        create_feature(g, nodes, attributes)

    try:
        shpdir.DeleteLayer("edges")
    except Exception:
        pass
    edges = shpdir.CreateLayer("edges", None, ogr.wkbLineString)

    # New edge attribute write support merged into edge loop
    edge_fields = {}      # storage for field names and their data types

    for e in G.edges(data=True):
        data = G.get_edge_data(*e)
        g = netgeometry(e, data)
        attributes, edges = create_attributes(e[2], edge_fields, edges)
        create_feature(g, edges, attributes)

    nodes, edges = None, None


def from_numpy_matrix(A, parallel_edges=False, create_using=None):
    """Returns a graph from a numpy matrix.

    The numpy matrix is interpreted as an adjacency matrix for the graph.

    Parameters
    ----------
    A : numpy matrix
      An adjacency matrix representation of a graph

    parallel_edges : Boolean
      If True, `create_using` is a multigraph, and `A` is an
      integer matrix, then entry *(i,j)* in the matrix is interpreted as the
      number of parallel edges joining vertices *i* and *j* in the graph.
      If False, then the entries in the adjacency matrix are interpreted as
      the weight of a single edge joining the vertices.

    create_using : NetworkX graph constructor, optional (default=nx.Graph)
       Graph type to create. If graph instance, then cleared before populated.

    Notes
    -----
    For directed graphs, explicitly mention create_using=nx.Digraph,
    and entry i,j of A corresponds to an edge from i to j.

    If `create_using` is :class:`networkx.MultiGraph` or
    :class:`networkx.MultiDiGraph`, `parallel_edges` is True, and the
    entries of `A` are of type :class:`int`, then this function returns a
    multigraph (constructed from `create_using`) with parallel edges.

    If `create_using` indicates an undirected multigraph, then only the edges
    indicated by the upper triangle of the matrix `A` will be added to the
    graph.

    Examples
    --------
    Simple integer weights on edges:

    >>> A = np.array([[1, 1], [2, 1]])
    >>> G = from_numpy_matrix(A)

    If `create_using` indicates a multigraph and the matrix has only integer
    entries and `parallel_edges` is False, then the entries will be treated
    as weights for edges with multiplicity 1:

    >>> A = np.array([[1, 1], [1, 2]])
    >>> G = from_numpy_matrix(A, create_using=nx.MultiGraph)
    >>> G[1][0]
    AtlasView({0: {'weight': 2}})

    If `create_using` indicates a multigraph and the matrix has only integer
    entries and `parallel_edges` is True, then the entries will be treated
    as the number of parallel edges between nodes:

    >>> A = np.array([[1, 1], [1, 2]])
    >>> temp = from_numpy_matrix(A, parallel_edges=True, create_using=nx.MultiGraph)
    >>> G = nx.MultiGraph(temp)
    >>> G[1][0]
    AtlasView({0: {'weight': 1}, 1: {'weight': 1}})

    References
    ----------
    .. [1] https://en.wikipedia.org/wiki/Adjacency_matrix
    """
    # This function is deprecated in NetworkX 3.0+, so we use from_numpy_array instead
    try:
        # Try to use the modern function first
        return nx.from_numpy_array(A, parallel_edges=parallel_edges, create_using=create_using)
    except AttributeError:
        # Fall back to older NetworkX versions that might still have from_numpy_matrix
        G = nx.empty_graph(0, create_using)
        n, m = A.shape

        if n != m:
            raise nx.NetworkXError("Adjacency matrix not square: nx,ny=%s" % (A.shape,))

        # Make sure we get even the isolated nodes of the graph.
        G.add_nodes_from(range(n))

        # Get a list of all the entries in the matrix with nonzero entries.
        # These coordinates become edges in the graph.
        edges = list(zip(*(A.nonzero())))
        
        # Handle directed vs undirected graphs
        if not G.is_directed():
            edges = [(u, v) for (u, v) in edges if u <= v]

        # Handle different edge types
        if G.is_multigraph():
            # Parallel edges
            if parallel_edges:
                for (u, v) in edges:
                    d = A[u, v]
                    if d.dtype.kind in ('i', 'u'):  # integer type
                        G.add_edges_from([(u, v)] * int(d))
                    else:
                        G.add_edge(u, v, weight=float(d))
            else:
                for (u, v) in edges:
                    G.add_edge(u, v, weight=float(A[u, v]))
        else:
            for (u, v) in edges:
                G.add_edge(u, v, weight=float(A[u, v]))

        return G