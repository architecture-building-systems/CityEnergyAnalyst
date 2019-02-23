import pandapower as pp
import re

def powerflow_mp(ind, points_on_line, idx_edge, dict_length, df_line_parameter):
    v_base = 20.

    # Filter intersections
    points_on_line = points_on_line[points_on_line['Type'].notnull()]

    # Create an empty network.
    net = pp.create_empty_network()

    # Create buses.
    for node_idx, node in points_on_line.iterrows():
        # pp.create_bus(net, name=node['Name'], vn_kv=v_base, geodata=(node.values[1].x, node.values[1].y))
        pp.create_bus(net, name=node['Name'], vn_kv=v_base)

    # create loads and external grid connections.
    for node_idx, node in points_on_line.iterrows():
        if node['Type'] == 'CONSUMER':
            load = (node['GRID0_kW'])  # TODO just example load
            pp.create_load(net, bus=int(node['Name'][4:]), p_kw=load, name=points_on_line['Name'])
        elif node['Type'] == 'PLANT':
            pp.create_ext_grid(net, bus=int(node['Name'][4:]), vm_pu=1.02, name=points_on_line['Name'])

    # Create lines.
    for idx_gene, gene in enumerate(ind):
        if gene > 0:
            start_node = idx_edge[idx_gene][0]
            end_node = idx_edge[idx_gene][1]
            length = dict_length[start_node][end_node]

            pp.create_line_from_parameters(net,
                                           name='Linetype' + str(gene),
                                           from_bus=start_node,
                                           to_bus=end_node,
                                           length_km=length/1000.0,
                                           r_ohm_per_km=df_line_parameter.loc[gene, 'r_ohm_per_km'],
                                           x_ohm_per_km=df_line_parameter.loc[gene, 'x_ohm_per_km'],
                                           c_nf_per_km=df_line_parameter.loc[gene, 'C_microF_per_km']*1000.0,
                                           max_i_ka=df_line_parameter.loc[gene, 'I_max_A']/1000.0,
                                           )

    # Runs PANDAPOWER DC Flow
    pp.rundcpp(net)
    # Runs PANDAPOWER AC Flow
    # pp.runpp(net)

    return net


def powerflow_lp(m, points_on_line, dict_length, df_line_parameter):
    v_base = 20.
    var_x = m.var_x.values()

    # Filter intersections
    points_on_line = points_on_line[points_on_line['Type'].notnull()]

    # Create an empty network.
    net = pp.create_empty_network()

    # Create buses.
    for node_idx, node in points_on_line.iterrows():
        # pp.create_bus(net, name=node['Name'], vn_kv=v_base, geodata=(node.values[1].x, node.values[1].y))
        pp.create_bus(net, name=node['Name'], vn_kv=v_base)

    # create loads and external grid connections.
    for node_idx, node in points_on_line.iterrows():
        if node['Type'] == 'CONSUMER':
            load = (node['GRID0_kW'])  # TODO just example load
            pp.create_load(net, bus=int(node['Name'][4:]), p_kw=load, name=points_on_line['Name'])
        elif node['Type'] == 'PLANT':
            pp.create_ext_grid(net, bus=int(node['Name'][4:]), vm_pu=1.02, name=points_on_line['Name'])

    # Create lines.
    for idx_x, x in enumerate(var_x):
        if x.value > 0.5:
            node_int = re.findall(r'\d+', x.local_name)

            start_node = int(node_int[0])
            end_node = int(node_int[1])
            linetype = int(node_int[2])
            length = dict_length[start_node][end_node]

            pp.create_line_from_parameters(net,
                                           name='Linetype' + str(linetype),
                                           from_bus=start_node,
                                           to_bus=end_node,
                                           length_km=length/1000.0,
                                           r_ohm_per_km=df_line_parameter.loc[linetype, 'r_ohm_per_km'],
                                           x_ohm_per_km=df_line_parameter.loc[linetype, 'x_ohm_per_km'],
                                           c_nf_per_km=df_line_parameter.loc[linetype, 'C_microF_per_km']*1000.0,
                                           max_i_ka=df_line_parameter.loc[linetype, 'I_max_A']/1000.0,
                                           )

    # Runs PANDAPOWER DC Flow
    pp.rundcpp(net)
    # Runs PANDAPOWER AC Flow
    # pp.runpp(net)

    return net

