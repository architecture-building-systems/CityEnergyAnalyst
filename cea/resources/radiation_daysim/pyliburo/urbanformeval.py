# ==================================================================================================
#
#    Copyright (c) 2016, Chen Kian Wee (chenkianwee@gmail.com)
#
#    This file is part of pyliburo
#
#    pyliburo is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    pyliburo is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Dexen.  If not, see <http://www.gnu.org/licenses/>.
#
# ==================================================================================================
import os
import math
import networkx as nx
import matplotlib.pyplot as plt
import py3dmodel
import gml3dmodel
import py2radiance


def calculate_srfs_area(occ_srflist):
    area = 0
    for srf in occ_srflist:
        area = area + py3dmodel.calculate.face_area(srf)
        
    return area
    
def pyptlist2vertlist(pyptlist):
    vertlist = []
    for pypt in pyptlist:
        vert = py3dmodel.construct.make_vertex(pypt)
        vertlist.append(vert)
    return vertlist
    
#================================================================================================================
#FRONTAL AREA INDEX
#================================================================================================================
def frontal_area_index(building_occsolids, boundary_occface, wind_dir, xdim = 100, ydim = 100):
    '''
    Algorithm to calculate frontal area index for a design
    
    PARAMETERS
    ----------
    :param building_occsolids : a list of buildings occsolids
    :ptype: list(occsolid)
    
    :param boundary_occface: occface that is the boundary of the area
    :ptype: occface
    
    :param wind_dir: a 3d tuple specifying the direction of the wind is blowing from
    :ptype: tuple
    
    :param xdim: x dimension of the grid for the boundary occface, in metres (m)
    :ptype: float
    
    :param ydim: y dimension of the grid for the boundary occface, in metres (m)
    :ptype: float
    
    RETURNS
    -------
    :returns avg_fai: average frontal area index of the whole design
    :rtype: float
    
    :returns gridded_boundary: the grid of the frontal area index
    :rtype: list(occface)
    
    :returns fai_list: list of all the FAI of each plot
    :rtype: list(float)    
    
    :returns fs_list: the projected surfaces fused together
    :rtype: list(occface)
    
    :returns wp_list: the plane representing the direction of the wind
    :rtype: list(occface)
    
    :returns os_list: the facade surfaces that are projected
    :rtype: list(occface)
    
    '''
    fai_list = []
    fs_list = []
    wp_list = []
    os_list = []
    
    gridded_boundary = py3dmodel.construct.grid_face(boundary_occface, xdim, ydim)
    close_compound = py3dmodel.construct.make_compound(building_occsolids)
    gcnt = 0
    for grid in gridded_boundary:
        grid_extrude = py3dmodel.construct.extrude(grid, (0,0,1), 10000)
        common_shape = py3dmodel.construct.boolean_common(grid_extrude,close_compound)
        common_shape = py3dmodel.fetch.shape2shapetype(common_shape)
        compound_faces = py3dmodel.fetch.geom_explorer(common_shape, "face")
        facade_list, roof_list, ftprint_list = gml3dmodel.identify_srfs_according_2_angle(compound_faces)
        if facade_list:
            fai,fuse_srfs,wind_plane,origsrf_prj= frontal_area_index_aplot(facade_list, grid, (1,1,0))
            fai_list.append(fai)
            fs_list.extend(fuse_srfs)
            wp_list.append(wind_plane)
            os_list.extend(origsrf_prj)
        else:
            fai_list.append(0)
            
        gcnt+=1
        
    avg_fai = float(sum(fai_list))/float(len(fai_list))
    return avg_fai, gridded_boundary,fai_list, fs_list, wp_list, os_list
    
def frontal_area_index_aplot(facade_occpolygons, plane_occpolygon, wind_dir):
    '''
    Algorithm to calculate frontal area index for a single plot
    
    PARAMETERS
    ----------
    :param facet_occpolygons : a list of occ faces of vertical facades 
    :ptype: list(occface)
    
    :param plane_occpolygon: an occ face that is the horizontal plane buildings are sitting on 
    :ptype: occface
    
    :param wind_dir: a 3d tuple specifying the direction of the wind is blowing from
    :ptype: tuple
    
    RETURNS
    -------
    :returns fai: frontal area index 
    :rtype: float
    
    :returns fuse_srfs: the projected surfaces fused together
    :rtype: list(occface)
    
    
    :returns wind_plane: the plane representing the direction of the wind
    :rtype: occface
    
    :returns surfaces_projected: the facade surfaces that are projected
    :rtype: list(occface)
    
    '''
    facade_faces_compound = py3dmodel.construct.make_compound(facade_occpolygons)
     
    #create win dir plane
    #get the bounding box of the compound, so that the wind plane will be placed at the edge of the bounding box
    xmin, ymin, zmin, xmax, ymax, zmax = py3dmodel.calculate.get_bounding_box(facade_faces_compound)
    pymidpt = py3dmodel.calculate.get_centre_bbox(facade_faces_compound)
    #calculate the furthest distance of the bounding box
    pycornerpt = (xmin, ymin, 0)
    
    furtherest_dist = py3dmodel.calculate.distance_between_2_pts(pymidpt, pycornerpt)
    #create the wind plane 
    pt4plane = py3dmodel.modify.move_pt(pymidpt, wind_dir, furtherest_dist) 
    wind_plane = py3dmodel.construct.make_plane_w_dir(pt4plane, wind_dir)
    
    surfaces_projected = []
    projected_facet_faces = []
    for facade_face in facade_occpolygons:
        #srf_dir = py3dmodel.calculate.face_normal(facade_face)
        #angle = py3dmodel.calculate.angle_bw_2_vecs(wind_dir, srf_dir)
        #interpt, interface = py3dmodel.calculate.intersect_shape_with_ptdir(wind_plane, srf_midpt, srf_dir)
        #print "ANGLE",angle
        #if angle<90:
        surfaces_projected.append(facade_face)
        projected_pts = py3dmodel.calculate.project_face_on_faceplane(wind_plane, facade_face)
        projected_srf = py3dmodel.construct.make_polygon(py3dmodel.fetch.occptlist2pyptlist(projected_pts))
        if py3dmodel.calculate.face_area(projected_srf) >0:
            projected_facet_faces.append(projected_srf)
         
    npfaces = len(projected_facet_faces)
    if npfaces == 1:
        fuse_srfs = projected_facet_faces
    else:
        for psrf_cnt in range(npfaces-1):
            if psrf_cnt ==0:
                fuse_shape = py3dmodel.construct.boolean_fuse(projected_facet_faces[psrf_cnt], projected_facet_faces[psrf_cnt+1])
            else:
                fuse_shape = py3dmodel.construct.boolean_fuse(fuse_shape, projected_facet_faces[psrf_cnt+1])
                
        fuse_compound = py3dmodel.fetch.shape2shapetype(fuse_shape) 
        fuse_srfs = py3dmodel.fetch.geom_explorer(fuse_compound,"face")
    
    #calculate the frontal area index
    facet_area = calculate_srfs_area(fuse_srfs)
    plane_area = py3dmodel.calculate.face_area(plane_occpolygon)
    fai = facet_area/plane_area
    
    return fai, fuse_srfs, wind_plane, surfaces_projected
   
#================================================================================================================
#ROUTE DIRECTNESS INDEX
#================================================================================================================
def route_directness(network_occedgelist, plot_occfacelist, boundary_occface, obstruction_occfacelist = [], rdi_threshold = 1.6):
    '''
    Algorithm for Route Directness Test  
    Stangl, P.. 2012 the pedestrian route directness test: A new level of service model.
    urban design international 17, 228-238
    
    A test that measures the connectivity of street network in a neighbourhood
    measuring route directness for each parcel to each of a series
    of points around the periphery of the study area,
    and identifying the percentage of parcels for which
    any of these measures exceed 1.6. Urban area is 1.3, suburban is 1.6
    
    PARAMETERS
    ----------
    :param network_occedgelist : a list of occedges that is the network to be analysed, clearly define network with
        nodes and edges
    :ptype: list(occedge)
    
    :param plot_occfacelist: a list of occfaces that is the land use plots
    :ptype: list(occface)
    
    :param boundary_occface: occface that is the boundary of the area
    :ptype: occface
    
    :param route_directness_threshold: a float specifying the route directness threshold, default value 1.6
    :ptype: float
    
    RETURNS
    -------
    :returns route_directness_measure: route_directness_measure
    :rtype: float
    
    :returns failed_plots: plots that fail the route directness measure
    :rtype: list(occface)
    
    :returns successful_plots: plots that pass the route directness measure
    :rtype: list(occface)
    
    :returns peripheral_pts: peripheral pts
    :rtype: list(occpts)
    
    '''
    ndecimal = 2
    precision = 1e-02
    #======================================================================
    #designate peripheral points
    #======================================================================
    peripheral_ptlist, pedgelist, interptlist = designate_peripheral_pts(boundary_occface, network_occedgelist, precision)
        
    #======================================================================
    #connect the street network: connect midpt of each plot to the street network
    #======================================================================
    inter_peri_ptlist = peripheral_ptlist + interptlist
    new_network_occedgelist, midpt2_network_edgelist, plot_midptlist = connect_street_network2plot(network_occedgelist, plot_occfacelist, inter_peri_ptlist, precision)
    
    #======================================================================
    #construct the networkx network
    #======================================================================
    #create a graph
    G = nx.Graph()
    #add all the edges for the boundary
    edges4_networkx = new_network_occedgelist + pedgelist + midpt2_network_edgelist
    
    network_pts = []
    for ne in edges4_networkx:
        occptlist = py3dmodel.fetch.points_from_edge(ne)
        npyptlist = py3dmodel.fetch.occptlist2pyptlist(occptlist)
        network_pts.extend(npyptlist)
        
    fused_ntpts = py3dmodel.modify.rmv_duplicated_pts_by_distance(network_pts, tolerance = precision)
    fused_ntpts = py3dmodel.modify.round_pyptlist(fused_ntpts, ndecimal)
    
    total_edge_nodes = []
    for x_edge in edges4_networkx:
        edge_nodes = py3dmodel.fetch.occptlist2pyptlist(py3dmodel.fetch.points_from_edge(x_edge))
        edge_nodes = py3dmodel.modify.round_pyptlist(edge_nodes, ndecimal)
        total_edge_nodes.extend(edge_nodes)
        xdmin,xdmax = py3dmodel.fetch.edge_domain(x_edge)
        length = py3dmodel.calculate.edgelength(xdmin,xdmax,x_edge)
        node1 = fused_ntpts.index(edge_nodes[0])
        node2 = fused_ntpts.index(edge_nodes[1])
        G.add_edge(node1,node2, distance = length)
        
    #sp = nx.shortest_path(G,source = 4, target = 224)
    #print sp
    #======================================================================
    #measure route directness
    #======================================================================
    #loop thru all the midpts of the plot
    pass_plots = plot_occfacelist[:]
    fail_plots = []
    display_plots = []
    total_route_directness_aplot = []

    plcnt = 0
    for midpt in plot_midptlist:
        midpt = py3dmodel.modify.round_pypt(midpt,ndecimal)
        #check if the plot is a dead plot with no free edges
        plof_occface = plot_occfacelist[plcnt]
        if midpt not in fused_ntpts:
            fail_plots.append(plof_occface)
            pass_plots.remove(plof_occface)
        else:        
            #measure the direct distance crow flies distance
            plot_area = py3dmodel.calculate.face_area(plof_occface) 
            display_plots.append(plof_occface)
            aplot_avg_rdi_list = []
            #1/2 acre
            #if plot_area <= 2023: 
            for perpypt in peripheral_ptlist:
                perpypt = py3dmodel.modify.round_pypt(perpypt,ndecimal)
                route_directness = calculate_route_directness(midpt, perpypt, obstruction_occfacelist,G, fused_ntpts, plot_area = plot_area)
                aplot_avg_rdi_list.append(route_directness)
                if route_directness > rdi_threshold:
                    fail_plots.append(plof_occface)
                    pass_plots.remove(plof_occface)
                    break
                
            for perpypt in peripheral_ptlist:
                perpypt = py3dmodel.modify.round_pypt(perpypt,ndecimal)
                route_directness = calculate_route_directness(midpt, perpypt, obstruction_occfacelist,G, fused_ntpts)
                #print "rdi, plcnt", route_directness, plcnt
                aplot_avg_rdi_list.append(route_directness)
                
            max_rdi_aplot = max(aplot_avg_rdi_list)
            total_route_directness_aplot.append(max_rdi_aplot)
        plcnt += 1
    
    avg_rdi = float(sum(total_route_directness_aplot))/float(len(total_route_directness_aplot))
    rdi_percentage = float(len(pass_plots))/float((len(fail_plots) + len(pass_plots))) * 100
    circles_peri_pts = py3dmodel.construct.circles_frm_pyptlist(peripheral_ptlist, 5)    
    #circles_inter_pts = py3dmodel.construct.circles_frm_pyptlist(py3dmodel.construct.make_gppntlist(midptlist), 5)  
    return avg_rdi, rdi_percentage, display_plots, pass_plots, fail_plots, total_route_directness_aplot, edges4_networkx, circles_peri_pts 

    
def designate_peripheral_pts(boundary_occface, network_occedgelist, precision):
    peripheral_ptlist = []
    peripheral_parmlist = []
    peripheral_parmlist4network = []
    boundary_pyptlist = py3dmodel.fetch.pyptlist_frm_occface(boundary_occface)
    boundary_pyptlist.append(boundary_pyptlist[0])
    #extract the wire from the face and convert it to a bspline curve
    bedge = py3dmodel.construct.make_bspline_edge(boundary_pyptlist, mindegree=1, maxdegree=1)
    
    #get all the intersection points 
    interptlist = []
    for network_occedge in network_occedgelist:
        intersect_pts = py3dmodel.calculate.intersect_edge_with_edge(bedge, network_occedge, tolerance=precision)
        if intersect_pts!=None:
            interptlist.extend(intersect_pts)
            
    #remove all duplicate points    
    fused_interptlist = py3dmodel.modify.rmv_duplicated_pts_by_distance(interptlist, tolerance = precision)
    
    #translate all the points to parameter
    ulist = []
    for fused_interpt in fused_interptlist:
        parmu = py3dmodel.calculate.pt2edgeparameter(fused_interpt,bedge)
        ulist.append(parmu)
    
    ulist = sorted(ulist)
    nulist = len(ulist)
    #place a marker at the midpt between these intersection
    midptlist = []
    mulist = []
    bedge_lbound, bedge_ubound = py3dmodel.fetch.edge_domain(bedge)

    for ucnt in range(nulist):
        curparm = ulist[ucnt]
        
        if ucnt == nulist-1:
            if curparm == bedge_ubound and ulist[0] != bedge_lbound:
                terange = ulist[0]-0
                temidparm = terange/2
                
            elif curparm !=bedge_ubound and ulist[0] != bedge_lbound:
                terange1 = 1-curparm
                terange2 =  ulist[0]-0
                terange3 = terange1+terange2
                temidparm = curparm + (terange3/2)
                if temidparm > 1:
                    temidparm = temidparm-1
                
            elif curparm !=bedge_ubound and ulist[0] == bedge_lbound:
                terange = 1-curparm
                temidparm = terange/2

        else:
            terange = ulist[ucnt+1]-curparm
            temidparm = curparm + (terange/2)
        
        temid = py3dmodel.calculate.edgeparameter2pt(temidparm, bedge)            
        midptlist.append(temid)
        mulist.append(temidparm)
    
    #check the spacing of all the points to ensure they are not more than 106m (350')
    #if they are divide them as accordingly
    umulist = sorted(mulist + ulist)
    numulist = len(umulist)
    for mcnt in range(numulist):
        mcurparm = umulist[mcnt]
        
        if mcnt == numulist-1:
            if mcurparm == bedge_ubound and umulist[0] != bedge_lbound:
                mcurparm = 0
                mnextparm = umulist[0]
                mrange = mnextparm - mcurparm
                mlength = py3dmodel.calculate.edgelength(mcurparm,mnextparm, bedge)
                
            elif mcurparm !=bedge_ubound and umulist[0] != bedge_lbound:
                mlength1 = py3dmodel.calculate.edgelength(mcurparm,1, bedge)
                mlength2 = py3dmodel.calculate.edgelength(0,umulist[0], bedge)
                mrange1 = 1-mcurparm
                mrange2 = umulist[0]-0
                mrange = mrange1+mrange2
                mlength = mlength1+mlength2
        else:
            mnextparm = umulist[mcnt+1]
            mrange = mnextparm - mcurparm
            mlength = py3dmodel.calculate.edgelength(mcurparm,mnextparm, bedge)
            
        if mlength > 106:
            #divide the segment into 106m segments
            nsegments = math.ceil((mlength)/106.0)
            segment = mrange/nsegments
            for scnt in range(int(nsegments)-1):
                divparm = mcurparm + ((scnt+1)*segment)
                if divparm >1:
                    divparm = divparm - 1
                
                peripheral_parmlist.append(divparm)
            
    peripheral_parmlist4network = peripheral_parmlist + umulist
    peripheral_parmlist4network.sort()
    #reconstruct the boundary into curve segments 
    pcurvelist = []
    nplist = len(peripheral_parmlist4network)
    for pcnt in range(nplist):
        pcurparm = peripheral_parmlist4network[pcnt]
        if pcnt == nplist-1:
            if pcurparm == bedge_ubound and peripheral_parmlist4network[0] != bedge_lbound:
                pcurparm = 0
                pnextparm = peripheral_parmlist4network[0]
                pcurve = py3dmodel.modify.trimedge(pcurparm, pnextparm, bedge)
                pcurvelist.append(pcurve)
                
            elif pcurparm !=bedge_ubound and peripheral_parmlist4network[0] != bedge_lbound:
                pcurve1 = py3dmodel.modify.trimedge(pcurparm, 1, bedge)
                pcurve2 = py3dmodel.modify.trimedge(0, peripheral_parmlist4network[0], bedge)
                pcurvelist.append(pcurve1)
                pcurvelist.append(pcurve2)
        else:
            pnextparm = peripheral_parmlist4network[pcnt+1]
            pcurve = py3dmodel.modify.trimedge(pcurparm, pnextparm, bedge)
            pcurvelist.append(pcurve)
            
    #===========================================================================
    peripheral_parmlist.extend(mulist)
    peripheral_parmlist.sort()
    for pparm in peripheral_parmlist:
        peripheral_pt = py3dmodel.calculate.edgeparameter2pt(pparm, bedge)
        peripheral_ptlist.append(peripheral_pt)
        
    pedgelist = []
    ppoles_all = []
    for pc in pcurvelist:
        ppoles = py3dmodel.fetch.poles_from_bsplinecurve_edge(pc)
        ppoles_all.append(ppoles)
        pwire = py3dmodel.construct.make_wire(ppoles)
        pedges = py3dmodel.fetch.edges_frm_wire(pwire)
        pedgelist.extend(pedges)
        
    return peripheral_ptlist, pedgelist, fused_interptlist
    
def connect_street_network2plot(network_occedgelist, plot_occfacelist, peripheral_n_inter_ptlist, precision):
    plot_edgeptlist = []
    plot_midptlist = []
    network_ptlist = []
    midpt2_network_edgelist = []
    network_compound = construct_network_compound(network_occedgelist, 10)
    #get the mid point of the plot
    for plot_occface in plot_occfacelist:
        pymidpt = py3dmodel.calculate.face_midpt(plot_occface)
        plot_midptlist.append(pymidpt)
        plot_edgeptlist.append([])
        #get all the edges of the plot 
        plotedgelist = py3dmodel.fetch.geom_explorer(plot_occface, "edge")
        #extrude the plot into a solid
        pextrude = py3dmodel.fetch.shape2shapetype(py3dmodel.construct.extrude(plot_occface,(0,0,1), 10))
        #face_list = py3dmodel.fetch.geom_explorer(pextrude, "face")
        for pedge in plotedgelist:
            #find the midpt of the edge 
            pedge_midpypt = py3dmodel.calculate.edge_midpt(pedge)
            #connect the midpt towards the pedge_midpypt
            midpt2pedge = py3dmodel.construct.make_edge(pymidpt, pedge_midpypt)
            midpt2_network_edgelist.append(midpt2pedge)
            #get the normal direction of the edge, then use the normal direction 
            #to project the point into network edges
            gpvec = py3dmodel.construct.make_vector(pymidpt,pedge_midpypt)
            pyvec = py3dmodel.modify.normalise_vec(gpvec)
            inter_occpt, inter_face = py3dmodel.calculate.intersect_shape_with_ptdir(pextrude, pymidpt, pyvec) 
            pydir = py3dmodel.calculate.face_normal(inter_face)
            #project pedge_midpypt to the network edges
            inter_occpt2, inter_face2 = py3dmodel.calculate.intersect_shape_with_ptdir(network_compound, pedge_midpypt, pydir)             
            
            if inter_occpt2 !=None:
                #it means according to the normal direction of the surface it will hit a network edge
                inter_pypt = py3dmodel.fetch.occpt2pypt(inter_occpt2)
                pedge2network = py3dmodel.construct.make_edge(pedge_midpypt, inter_pypt)
                network_ptlist.append(inter_pypt)
                midpt2_network_edgelist.append(pedge2network)
                plot_edgeptlist[-1].append(pedge_midpypt)
                #make sure the plot edge is a free edge
                #if it cuts any of the plots it means it is not a free edge
                for plot_occface2 in plot_occfacelist:
                    dmin,dmax = py3dmodel.fetch.edge_domain(pedge2network)
                    drange = dmax-dmin
                    dquantum = 0.1*drange
                    pypt1 = py3dmodel.calculate.edgeparameter2pt(dmin+dquantum, pedge2network)
                    pypt2 = py3dmodel.calculate.edgeparameter2pt(dmax, pedge2network)
                    pedge2network2 = py3dmodel.construct.make_edge(pypt1, pypt2)
                    is_intersecting = py3dmodel.construct.boolean_common(plot_occface2,pedge2network2)
                    if not py3dmodel.fetch.is_compound_null(is_intersecting):
                        #it is not a free edge
                        midpt2_network_edgelist.remove(midpt2pedge)
                        midpt2_network_edgelist.remove(pedge2network)
                        network_ptlist.remove(inter_pypt)
                        plot_edgeptlist[-1].remove(pedge_midpypt)
                        break

            else:
                #it means according to the normal direction of the surface this plot edge is a deadend 
                midpt2_network_edgelist.remove(midpt2pedge)

    #reconstruct the network edges with the new network_ptlist
    new_network_occedgelist = network_occedgelist[:]
    network_ptlist = network_ptlist + peripheral_n_inter_ptlist
    for networkpt in network_ptlist:
        network_vert = py3dmodel.construct.make_vertex(networkpt)
        for nedge in new_network_occedgelist:
            #find the edge the point belongs to 
            env_mindist = py3dmodel.calculate.minimum_distance(network_vert,nedge)
            if env_mindist <= precision:
                #that means the point belongs to this edge
                #remove the original edge
                new_network_occedgelist.remove(nedge)
                #find the parameter then reconstruct the edge accordingly
                dmin, dmax = py3dmodel.fetch.edge_domain(nedge)
                domain_list = [dmin, dmax]
                inter_parm = py3dmodel.calculate.pt2edgeparameter(networkpt, nedge)
                domain_list.append(inter_parm)
                domain_list.sort()
                #reconstruct the edge 
                pypt1 = py3dmodel.calculate.edgeparameter2pt(domain_list[0], nedge)
                pypt2 = py3dmodel.calculate.edgeparameter2pt(domain_list[1], nedge)
                pypt3 = py3dmodel.calculate.edgeparameter2pt(domain_list[2], nedge)
                n_nedge1 = py3dmodel.construct.make_edge(pypt1, pypt2)
                new_network_occedgelist.append(n_nedge1)
                n_nedge2 = py3dmodel.construct.make_edge(pypt2, pypt3)
                new_network_occedgelist.append(n_nedge2)
                break
            
    return new_network_occedgelist, midpt2_network_edgelist, plot_midptlist
    
def calculate_route_directness(startpypt, peripheralpypt, obstruction_occfacelist,G,index_list, plot_area = None):
    crow_wire = py3dmodel.construct.make_wire([startpypt, peripheralpypt])   
    #need to check if the crow edge intersect any obstruction
    rerouted_wire = crow_wire 
    for obface in obstruction_occfacelist:
        common_compound = py3dmodel.construct.boolean_common(obface, rerouted_wire)
        is_comp_null = py3dmodel.fetch.is_compound_null(common_compound)
        if not is_comp_null:
            #means there is an intersection
            #need to reconstruct the distance
            rerouted_wire = route_ard_obstruction(obface, crow_wire)
            
    #measure the direct distance
    direct_distance = py3dmodel.calculate.wirelength(rerouted_wire)
    #measure the route distance
    perpypt_index = index_list.index(peripheralpypt)
    startpypt_index = index_list.index(startpypt)
    shortest_path = nx.shortest_path(G,source=startpypt_index,target=perpypt_index, weight = "distance")
    nshortpath = len(shortest_path)
    route_distance = 0
    
    for scnt in range(nshortpath):
        if scnt != nshortpath-1:
            network_edge = G[shortest_path[scnt]][shortest_path[scnt+1]]
            route_distance = route_distance + network_edge["distance"]
            
    if plot_area != None:
        if plot_area <= 2023:#1/2 acre
            #the route distance is from the frontage edge not from the midpt
            #so we will minus of the distance from the midpt to the frontage
            midpt_2_edge = G[shortest_path[0]][shortest_path[1]]
            m2e_dist = midpt_2_edge["distance"]
            route_distance = route_distance - m2e_dist
            
    route_directness = route_distance/direct_distance
    return route_directness
    
def route_ard_obstruction(obstruction_face, crow_wire):        
    res = py3dmodel.fetch.shape2shapetype(py3dmodel.construct.boolean_common(obstruction_face,crow_wire))
    res2 =py3dmodel.fetch.shape2shapetype(py3dmodel.construct.boolean_difference(crow_wire,obstruction_face))
    edgelist = py3dmodel.fetch.geom_explorer(res, "edge")
    edgelist2 = py3dmodel.fetch.geom_explorer(res2, "edge")
    
    wire = py3dmodel.fetch.wires_frm_face(obstruction_face)[0]
    #turn the wire into a degree1 bspline curve edge
    pyptlist = py3dmodel.fetch.occptlist2pyptlist(py3dmodel.fetch.points_frm_wire(wire))
    pyptlist.append(pyptlist[0])
    bspline_edge  = py3dmodel.construct.make_bspline_edge(pyptlist, mindegree=1, maxdegree=1)
    
    interptlist = []
    for edge in edgelist:
        interpts = py3dmodel.calculate.intersect_edge_with_edge(bspline_edge, edge)
        interptlist.extend(interpts)
    
    interptlist = py3dmodel.modify.rmv_duplicated_pts(interptlist)
    eparmlist = []
    
    for interpt in interptlist:
        eparm = py3dmodel.calculate.pt2edgeparameter(interpt, bspline_edge)
        eparmlist.append(eparm)
        
    eparmlist.sort()
    edmin,edmax = py3dmodel.fetch.edge_domain(bspline_edge)
    eparm_range1 = eparmlist[-1] - eparmlist[0]
    eparm_range21 = eparmlist[0] - edmin
    eparm_range22 = edmax-eparmlist[-1]
    eparm_range2 = eparm_range21 + eparm_range22
    
    if eparm_range1 < eparm_range2 or eparm_range1 == eparm_range2 :
        te = py3dmodel.modify.trimedge(eparmlist[0],eparmlist[-1], bspline_edge)
        edgelist2.append(te)
        sorted_edge2dlist = py3dmodel.calculate.sort_edges_into_order(edgelist2)
        
    if eparm_range1 > eparm_range2:
        te1 = py3dmodel.modify.trimedge(edmin, eparmlist[0], bspline_edge)
        te2 = py3dmodel.modify.trimedge(eparmlist[-1], edmax, bspline_edge)
        edgelist2.append(te1)
        edgelist2.append(te2)
        sorted_edge2dlist = py3dmodel.calculate.sort_edges_into_order(edgelist2)
        
    sorted_edgelist = sorted_edge2dlist[0]
    
    #turn the wire into a degree1 bspline curve edge
    new_pyptlist = []
    for sorted_edge in sorted_edgelist:
        if py3dmodel.fetch.is_edge_bspline(sorted_edge):
            pts = py3dmodel.fetch.poles_from_bsplinecurve_edge(sorted_edge)
        if py3dmodel.fetch.is_edge_line(sorted_edge):
            pts = py3dmodel.fetch.occptlist2pyptlist(py3dmodel.fetch.points_from_edge(sorted_edge))
            
        new_pyptlist.extend(pts)
        
    new_bwire = py3dmodel.construct.make_wire(new_pyptlist)
    return new_bwire
    
def generate_directions(rot_degree):
    #generate the direction from the midpt to the plot edges 
    orig_vert = py3dmodel.construct.make_vertex((0,1,0))
    pydirlist = []
    for dircnt in range(int(360/rot_degree)):
        degree = rot_degree*dircnt
        rot_vert = py3dmodel.modify.rotate(orig_vert, (0,0,0), (0,0,1), degree)
        gppt = py3dmodel.fetch.vertex2point(rot_vert)
        pypt = py3dmodel.fetch.occpt2pypt(gppt)
        pydirlist.append(pypt)
        
    return pydirlist
    
def construct_network_compound(network_occedgelist, extrusion_height):
    nfacelist = []
    for nedge in network_occedgelist:
        #move the edge upwards then loft it to make a face
        nface = py3dmodel.construct.extrude_edge(nedge, (0,0,1), 10)
        nfacelist.append(nface)

    network_compound = py3dmodel.construct.make_compound(nfacelist)
    return network_compound
    
def draw_street_graph(networkx_graph, node_index):
    node_pos = {}
    ntcnt = 0
    for np in node_index:
        node_pos[ntcnt] = (np[0],np[1])
        ntcnt+=1

    nx.draw_networkx_labels(networkx_graph,pos=node_pos)
    nx.draw_networkx_nodes(networkx_graph,node_pos, node_size  = 10)
    nx.draw_networkx_edges(networkx_graph,node_pos,width=1.0,alpha=0.5)
    plt.show()

#================================================================================================================
#SOLAR ANALYSES
#================================================================================================================
def shgfavi(building_occsolids, irrad_threshold, epwweatherfile, xdim, ydim,
            rad_folderpath, shgfavi_threshold = None):
    '''
    Algorithm to calculate Solar Heat Gain Facade Area to Volume Index
    
    Solar Heat Gain Facade Area to Volume Index (SHGFAVI) calculates the ratio of facade area that 
    receives irradiation above a specified level over the building volume.    
    
    Solar Heat Gain Facade Area Index (SHGFAI) calculates the ratio of facade area that 
    receives irradiation below a specified level over the net facade area. 
    
    PARAMETERS
    ----------
    :param building_occsolids : a list of buildings occsolids
    :ptype: list(occsolid)
    
    :param irrad_threshold: a solar irradiance threshold value
    :ptype: float
    
    :param epwweatherfile: file path of the epw weatherfile
    :ptype: string
    
    :param xdim: x dimension grid size
    :ptype: float
    
    :param ydim: y dimension grid size
    :ptype: float
    
    :param shgfavi_threshold: a shgfavi threshold value for calculating the shgfavi_percent
    :ptype: float
    
    RETURNS
    -------
    :returns shgfavi: average solar heat gain facade area volume index
    :rtype: float
    
    :returns shgfavi_percent: percentage of buildings achieving the shgfavi_threshold
    :rtype: float
    
    :returns shgfai: shgfai value 
    :rtype: float
    
    :returns sensor_srflist: surfaces of the grid used for solar irradiation calculation, for visualisation purpose
    :rtype: list(occface)
    
    :returns irrad_ress: solar irradiation results from the simulation, for visualisation purpose
    :rtype: list(float)
    '''
    #sort and process the surfaces into radiance ready surfaces
    rad, sensor_ptlist, sensor_dirlist, sensor_srflist, bldgdict_list = initialise_vol_indexes(building_occsolids, 
                                                                                               xdim, ydim, 
                                                                                               rad_folderpath)   
    
    #execute gencumulative sky rtrace
    irrad_ress = execute_cummulative_radiance(rad,1,12, 1,31,0, 24, epwweatherfile)
    
    sorted_bldgdict_list = get_vol2srfs_dict(irrad_ress, sensor_srflist, bldgdict_list, surface = "all_surfaces")
    
    #calculate avg shgfavi 
    avg_shgfavi, shgfavi_percent, shgfa_list, total_vol_list = calculate_avi(sorted_bldgdict_list, irrad_threshold, 
                                                                             avi_threshold = None)
              
    #calculate shgfai
    shgfai, shgfa, total_srfarea = calculate_fai(sorted_bldgdict_list,irrad_threshold)
    
    return avg_shgfavi, shgfavi_percent, shgfai, sensor_srflist, irrad_ress
    
def calculate_epv(sensor_srflist,irrad_ress):
    '''
    epv is energy produced by pv (kwh/yr)
    
    eqn to calculate the energy produce by pv
    epv = apv*fpv*gt*nmod*ninv
    apv is area of pv (m2)
    fpv is faction of surface with active solar cells (ratio)
    gt is total annual solar radiation energy incident on pv (kwh/m2/yr)
    nmod is the pv efficiency (12%)
    ninv is the avg inverter efficiency (90%)
    '''
    apv = gml3dmodel.faces_surface_area(sensor_srflist)
    fpv = 0.8
    gt = (sum(irrad_ress))/(float(len(irrad_ress)))
    nmod = 0.12
    ninv = 0.9
    epv = apv*fpv*gt*nmod*ninv
    return epv
    
def pvavi(building_occsolids, irrad_threshold, epwweatherfile, xdim, ydim,
            rad_folderpath, mode = "roof", pvavi_threshold = None):
                
    """
    PV Area to Volume  Index (PVAVI) calculates the ratio of roof/facade area that 
    receives irradiation above a specified level over the building volume. 
    
    epv calculates the potential electricity 
    that can be generated on the buildings annually. (kWh/yr.)
    
    PV Area Index (PVAI) calculates the ratio of  area that 
    receives irradiation above a specified level over the net envelope/roof/facade area.         
        
    PARAMETERS
    ----------
    :param building_occsolids : a list of buildings occsolids
    :ptype: list(occsolid)
    
    :param irrad_threshold: a solar irradiance threshold value
    :ptype: float
    
    :param epwweatherfile: file path of the epw weatherfile
    :ptype: string
    
    :param xdim: x dimension grid size
    :ptype: float
    
    :param ydim: y dimension grid size
    :ptype: float
    
    :param pvavi_threshold: a pvavi threshold value for calculating the pvavi_percent
    :ptype: float
    
    RETURNS
    -------
    :returns avg_pvavi: average pvavi facade area volume index
    :rtype: float
    
    :returns pvavi_percent: percentage of buildings achieving the pvavi_threshold
    :rtype: float
    
    :returns pvai: pvai value 
    :rtype: float
    
    :returns epv: potential electricity that can be generated on the buildings annually. (kWh/yr.)
    :rtype: float
    
    :returns sensor_srflist: surfaces of the grid used for solar irradiation calculation, for visualisation purpose
    :rtype: list(occface)
    
    :returns irrad_ress: solar irradiance results from the simulation, for visualisation purpose
    :rtype: list(float)
    """    
    #sort and process the surfaces into radiance ready surfaces
    rad, sensor_ptlist, sensor_dirlist, sensor_srflist, bldgdict_list = initialise_vol_indexes(building_occsolids, xdim, ydim, 
                                                                                      rad_folderpath, surface = mode)   
    #execute gencumulative sky rtrace
    irrad_ress = execute_cummulative_radiance(rad,1,12, 1,31,0, 24, epwweatherfile)
    
    sorted_bldgdict_list = get_vol2srfs_dict(irrad_ress, sensor_srflist, bldgdict_list, surface = "all_surfaces")    
    
    #calculate avg pvavi 
    avg_pvavi, pvavi_percent, pva_list, total_vol_list = calculate_avi(sorted_bldgdict_list, irrad_threshold, avi_threshold = None)
              
    #calculate pvai
    pvai, pva, total_area = calculate_fai(sorted_bldgdict_list,irrad_threshold)
    
    #calculate the potential energy generated from pv 
    epv = calculate_epv(sensor_srflist,irrad_ress)
    
    
    return avg_pvavi, pvavi_percent, pvai, epv, sensor_srflist, irrad_ress
    
            
def pveavi(building_occsolids, roof_irrad_threshold, facade_irrad_threshold, epwweatherfile, xdim, ydim,
            rad_folderpath, pvravi_threshold = None, pvfavi_threshold = None, pveavi_threshold = None):
                
    """
    PV Envelope Area to Volume  Index (PVEAVI) calculates the ratio of envelope area that 
    receives irradiation above a specified level over the building volume. 
    
    epv calculates the potential electricity 
    that can be generated on the buildings annually. (kWh/yr.)
    
    PV Area Index (PVEAI) calculates the ratio of  area that 
    receives irradiation above a specified level over the net envelope area.                 
        
    PARAMETERS
    ----------
    :param building_occsolids : a list of buildings occsolids
    :ptype: list(occsolid)
    
    :param irrad_threshold: a solar irradiance threshold value
    :ptype: float
    
    :param epwweatherfile: file path of the epw weatherfile
    :ptype: string
    
    :param xdim: x dimension grid size
    :ptype: float
    
    :param ydim: y dimension grid size
    :ptype: float
    
    :param pvravi_threshold: a pvravi threshold value for calculating the pvravi_percent
    :ptype: float
    
    :param pvfavi_threshold: a pvravi threshold value for calculating the pvfavi_percent
    :ptype: float
    
    :param pveavi_threshold: a pvravi threshold value for calculating the pveavi_percent
    :ptype: float
    
    RETURNS
    -------
    :returns list of avi averages: average avi values of pveavi, pvravi, pvfavi 
    :rtype: list(float, float, float)
    
    :returns list of avi_percent: percentage of buildings achieving the avi_threshold, pveavi_percent, pvravi_percent, pvfavi_percent
    :rtype: list(float, float, float)
    
    :returns list of fai values: fai values of pveai, pvrai, pvfai
    :rtype: list(float, float, float)
    
    :returns epv: potential electricity that can be generated on the buildings annually. (kWh/yr.)
    :rtype: float
    
    :returns sensor_srflist: surfaces of the grid used for solar irradiation calculation, for visualisation purpose
    :rtype: list(occface)
    
    :returns irrad_ress: solar irradiance results from the simulation, for visualisation purpose
    :rtype: list(float)
    """    
    #sort and process the surfaces into radiance ready surfaces
    rad, sensor_ptlist, sensor_dirlist, sensor_srflist, bldgdict_list = initialise_vol_indexes(building_occsolids, xdim, ydim, 
                                                                                      rad_folderpath, surface = "envelope")   
    #execute gencumulative sky rtrace
    irrad_ress = execute_cummulative_radiance(rad,1,12, 1,31,0, 24, epwweatherfile)
    
    sorted_bldgdict_listr = get_vol2srfs_dict(irrad_ress, sensor_srflist, bldgdict_list, surface = "roof")
    sorted_bldgdict_listf = get_vol2srfs_dict(irrad_ress, sensor_srflist, bldgdict_list, surface = "facade")
    
    #calculate avg pvavi 
    avg_pvravi, pvravi_percent, pvra_list, total_vol_list = calculate_avi(sorted_bldgdict_listr, roof_irrad_threshold, 
                                               avi_threshold = pvravi_threshold)
                         
    avg_pvfavi, pvfavi_percent, pvfa_list, total_vol_list  = calculate_avi(sorted_bldgdict_listf, facade_irrad_threshold, 
                                               avi_threshold = pvfavi_threshold)
                                               
    pveavi_list = []
    compared_list = []
    for pv_cnt in range(len(pvra_list)):
        pveavi = (pvra_list[pv_cnt] + pvfa_list[pv_cnt])/total_vol_list[pv_cnt]
        pveavi_list.append(pveavi)
        if pveavi_threshold != None:
            if pveavi >= pveavi_threshold:
                compared_list.append(pveavi)
        
    
    avg_pveavi = float(sum(pveavi_list))/float(len(pveavi_list))
    pveavi_percent = (float(len(compared_list))/float(len(pveavi_list)))*100
    
    #calculate pvai
    pvrai, pvra, total_rarea = calculate_fai(sorted_bldgdict_listr,roof_irrad_threshold)
    pvfai, pvfa, total_farea = calculate_fai(sorted_bldgdict_listf,facade_irrad_threshold)
    pveai = ((pvra+pvfa)/(total_rarea + total_farea))*100
    #calculate the potential energy generated from pv 
    epv = calculate_epv(sensor_srflist,irrad_ress)
    
    return [avg_pveavi, avg_pvravi,avg_pvfavi],[pveavi_percent,pvravi_percent,pvfavi_percent], [pveai, pvrai,pvfai], epv, sensor_srflist, irrad_ress
    
def dfavi(building_occsolids, illum_threshold, epwweatherfile, xdim, ydim,
            rad_folderpath,daysim_folderpath, dfavi_threshold = None):
    '''
    Daylighting Facade Area to Volume Index (DFAVI) calculates the ratio of facade area that 
    receives daylighting above a specified level over the volume of the building. 
    
    Daylighting Facade Area Index (DFAI) calculates the ratio of facade area that 
    receives daylighting above a specified level over the total facade area. 
    
    PARAMETERS
    ----------
    :param building_occsolids : a list of buildings occsolids
    :ptype: list(occsolid)
    
    :param illum_threshold: a solar illuminance threshold value
    :ptype: float
    
    :param epwweatherfile: file path of the epw weatherfile
    :ptype: string
    
    :param xdim: x dimension grid size
    :ptype: float
    
    :param ydim: y dimension grid size
    :ptype: float
    
    :param dfavi_threshold: a shgfavi threshold value
    :ptype: float
    
    RETURNS
    -------
    :returns dfavi: average dfavi facade area volume index
    :rtype: float
    
    :returns dfavi_percent: percentage of buildings achieving the dfavi_threshold
    :rtype: float
    
    :returns dfai: dfai value
    :rtype: float
    
    :returns sensor_srflist: surfaces of the grid used for solar irradiation calculation, for visualisation purpose
    :rtype: list(occface)
    
    :returns mean illum_ress: mean illuminance results from the simulation, for visualisation purpose
    :rtype: list(float)
    '''
    
    rad, sensor_ptlist, sensor_dirlist, sensor_srflist, bldgdict_list = initialise_vol_indexes(building_occsolids, 
                                                                                      xdim, ydim, rad_folderpath)   
    
    illum_ress = execute_cummulative_radiance(rad,1,12, 1,31,0, 24, epwweatherfile, mode = "illuminance")
    
    rad.initialise_daysim(daysim_folderpath)
    #a 60min weatherfile is generated
    rad.execute_epw2wea(epwweatherfile)
    sunuphrs = rad.sunuphrs
    
    #ge the mean_illum_ress
    mean_illum_ress = []
    for illum in illum_ress:
        mean_illum = illum/float(sunuphrs)
        mean_illum_ress.append(mean_illum)
        
    sorted_bldgdict_list = get_vol2srfs_dict(mean_illum_ress, sensor_srflist, bldgdict_list, surface = "all_surfaces")
    
    avg_dfavi, dfavi_percent, dfa_list, total_vol_list = calculate_avi(sorted_bldgdict_list, illum_threshold, 
                                                                       avi_threshold = None)
                                                                       
    dfai, dfa, total_area = calculate_fai(sorted_bldgdict_list,illum_threshold)
    
    return avg_dfavi, dfavi_percent, dfai, sensor_srflist, mean_illum_ress
    
def initialise_vol_indexes(building_occsolids, xdim, ydim, rad_folderpath, surface = "facade"):
    #initialise py2radiance 
    rad_base_filepath = os.path.join(os.path.dirname(__file__),'py2radiance','base.rad')
    rad = py2radiance.Rad(rad_base_filepath, rad_folderpath)
    srfmat = "RAL2012"
    
    sensor_ptlist = []
    sensor_dirlist = []
    sensor_surfacelist = []
    
    bldg_dictlist = []
    
    gsrf_index_cnt = 0
    bldg_cnt = 0
    for bsolid in building_occsolids:
        gsrf_cnt = 0
        #separate the solid into facade footprint and roof
        bldg_dict = {}
        facades, roofs, footprints = gml3dmodel.identify_building_surfaces(bsolid)
        bsrflist = facades + roofs + footprints
        #measure the volume of the solid
        bvol = py3dmodel.calculate.solid_volume(bsolid)
        bldg_dict["volume"] = bvol
        if surface == "roof" or surface == "envelope":
            for roof in roofs:
                sensor_surfaces, sensor_pts, sensor_dirs = gml3dmodel.generate_sensor_surfaces(roof, xdim, ydim)
                sensor_ptlist.extend(sensor_pts)
                sensor_dirlist.extend(sensor_dirs)
                sensor_surfacelist.extend(sensor_surfaces)
                
                gsrf_cnt += len(sensor_surfaces)
                
            if surface == "envelope":
                roof_index1 = gsrf_index_cnt
                roof_index2 = gsrf_index_cnt + gsrf_cnt
             
        if surface == "facade" or surface == "envelope":
            for facade in facades:
                sensor_surfaces, sensor_pts, sensor_dirs = gml3dmodel.generate_sensor_surfaces(facade, xdim, ydim)
                sensor_ptlist.extend(sensor_pts)
                sensor_dirlist.extend(sensor_dirs)
                sensor_surfacelist.extend(sensor_surfaces)
                
                gsrf_cnt += len(sensor_surfaces)
                
            if surface == "envelope":
                facade_index1 = roof_index2
                facade_index2 = gsrf_index_cnt + gsrf_cnt
             
        bsrf_cnt = 0
        for bsrf in bsrflist:
            pypolygon = py3dmodel.fetch.pyptlist_frm_occface(bsrf)
            srfname = "srf" + str(bldg_cnt) + str(bsrf_cnt)
            py2radiance.RadSurface(srfname, pypolygon, srfmat, rad)
            bsrf_cnt+=1
            
        gsrf_range1 = gsrf_index_cnt
        gsrf_range2= gsrf_index_cnt + gsrf_cnt
        
        
        if surface == "envelope":
            bldg_dict["surface_index"] = [gsrf_range1, gsrf_range2,roof_index1,roof_index2,facade_index1,facade_index2]
        else:
             bldg_dict["surface_index"] = [gsrf_range1, gsrf_range2]
             
        bldg_dictlist.append(bldg_dict)
        gsrf_index_cnt +=  gsrf_cnt 
        bldg_cnt += 1 
        
    
    #get the sensor grid points
    rad.set_sensor_points(sensor_ptlist, sensor_dirlist)
    rad.create_sensor_input_file()
    #create the geometry files
    rad.create_rad_input_file()
    return rad, sensor_ptlist, sensor_dirlist, sensor_surfacelist, bldg_dictlist
    
def execute_cummulative_radiance(rad,start_mth,end_mth, start_date,end_date,start_hr, end_hr, 
                                 epwweatherfile, mode = "irradiance"):
    time = str(start_hr) + " " + str(end_hr)
    date = str(start_mth) + " " + str(start_date) + " " + str(end_mth) + " " + str(end_date)
    
    if mode == "irradiance":
        rad.execute_cumulative_oconv(time, date, epwweatherfile)
        #execute cumulative_rtrace
        rad.execute_cumulative_rtrace(str(2))#EXECUTE!! 
        #retrieve the results
        irrad_ress = rad.eval_cumulative_rad()
        return irrad_ress
    if mode == "illuminance":
        rad.execute_cumulative_oconv(time, date, epwweatherfile, output = "illuminance")
        #execute cumulative_rtrace
        rad.execute_cumulative_rtrace(str(2))#EXECUTE!! 
        #retrieve the results
        illum_ress = rad.eval_cumulative_rad(output = "illuminance")   
        return illum_ress
    
def calculate_avi(bldgdict_list, result_threshold, avi_threshold = None):
    avi_list = []
    compared_avi_list = []
    vol_list = []
    sa_list = []
    for bldgdict in bldgdict_list:
        bvol = bldgdict["volume"]
        vol_list.append(bvol)
        result_list = bldgdict["result"]
        surface_list = bldgdict["surface"]
        
        high_res = []
        high_res_srf = []
        bradcnt = 0
        for res in result_list:
            if res >= result_threshold:
                high_res.append(res)
                high_res_srf.append(surface_list[bradcnt])
            bradcnt+=1

        high_res_area = gml3dmodel.faces_surface_area(high_res_srf)
        sa_list.append(high_res_area)
        
        avi = high_res_area/bvol
        avi_list.append(avi)

        if avi_threshold != None:
            if avi >= avi_threshold:
                compared_avi_list.append(avi)
        
    avg_avi = sum(avi_list)/float(len(avi_list))
    if avi_threshold != None:
        avi_percent = float(len(compared_avi_list))/float(len(avi_list))
    else:
        avi_percent = None
    return avg_avi, avi_percent, sa_list, vol_list
    
def calculate_fai(bldgdict_list, result_threshold):
    high_res = []
    high_res_srf = []
    sensor_srflist = []

    for bldgdict in bldgdict_list:
        result_list = bldgdict["result"]
        surface_list = bldgdict["surface"]
        sensor_srflist.extend(surface_list)
        bradcnt = 0
        for res in result_list:
            if res > result_threshold:
                high_res.append(res)
                high_res_srf.append(surface_list[bradcnt])
            bradcnt+=1
        
    total_area = gml3dmodel.faces_surface_area(sensor_srflist)
    high_res_area = gml3dmodel.faces_surface_area(high_res_srf)
    fai = (high_res_area/total_area) * 100
    return fai, high_res_area, total_area
    
def get_vol2srfs_dict(result_list, sensor_srflist, bldgdict_list, surface = "all_surfaces"):
    """
    rearrange the surfaces of a building accordingly for calculate_avi function 
    """
    sorted_bldgdict_list = []
    for bldgdict in bldgdict_list:
        sorted_bldgdict = {}
        surface_index = bldgdict["surface_index"]
        bvol = bldgdict["volume"]
        sorted_bldgdict["volume"] = bvol
        if surface == "all_surfaces":
            sorted_bldgdict["result"] = result_list[surface_index[0]:surface_index[1]]
            sorted_bldgdict["surface"] = sensor_srflist[surface_index[0]:surface_index[1]]
        if surface == "roof":
            sorted_bldgdict["result"] = result_list[surface_index[2]:surface_index[3]]
            sorted_bldgdict["surface"] = sensor_srflist[surface_index[2]:surface_index[3]]
        if surface == "facade":
            sorted_bldgdict["result"] = result_list[surface_index[4]:surface_index[5]]
            sorted_bldgdict["surface"] = sensor_srflist[surface_index[4]:surface_index[5]]
        sorted_bldgdict_list.append(sorted_bldgdict)
            
    return sorted_bldgdict_list