"""
============================
    vtk window short cuts
    ---------------------
    j: joystick (continuous) mode
    t: trackball mode
    c: camera move mode
    a: actor move mode
    left mouse: rotate x,y
    ctrl_left mouse: rotate z
    middle mouse: pan
    right mouse: zoom
    r: reset camera
    s/w: surface/wireframe
    u: command window
    e: exit


    RETURNS
    -------
    window with animation of stl file, points, or surfaces. All of them can be combined
    using the different geometry to actor functions following the examples given.

    INPUT / OUTPUT FILES
    --------------------
    -stl files
    -point list in csv format columns are: sen_x, sen_y and sen_z
    -surface list with 9 columns --> three points with 3 coordinates.

    SIDE EFFECTS
    ------------
    if no data file is given, the loaded geometry will not change color

============================

"""

import os
import math

import matplotlib.cm as cm
import pandas as pd
import numpy as np
import vtk

import cea.globalvar
import cea.inputlocator

__author__ = "Paul Neitzel"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Paul Neitzel"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"



def stl2actor(ageometry_path, ageometry_name, ageometry_color):

    appendfilter = vtk.vtkAppendPolyData()
    render_lib = vtk.vtkSTLReader()
    polydata = vtk.vtkPolyData()
    render_lib.SetFileName(os.path.join(ageometry_path, ageometry_name+".stl"))
    render_lib.Update()
    polydata.ShallowCopy(render_lib.GetOutput())
    appendfilter.AddInputConnection(polydata.GetProducerPort())
    appendfilter.Update()

    #  Remove any duplicate points.
    cleanfilter = vtk.vtkCleanPolyData()
    cleanfilter.SetInputConnection(appendfilter.GetOutputPort())
    cleanfilter.Update()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(cleanfilter.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(ageometry_color)

    return actor, polydata


def points2actor(xyz, apoint_size):
    import vtk
    points = vtk.vtkPoints()
    # Create the topology of the point (a vertex)
    vertices = vtk.vtkCellArray()
    # Add points
    for i in range(0, len(xyz)):
        p = xyz.loc[i].values.tolist()
        point_id = points.InsertNextPoint(p)
        vertices.InsertNextCell(1)
        vertices.InsertCellPoint(point_id)
    # Create a poly data object
    polydata = vtk.vtkPolyData()
    # Set the points and vertices we created as the geometry and topology of the polydata
    polydata.SetPoints(points)
    polydata.SetVerts(vertices)
    polydata.Modified()
    # Mapper for points
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInput(polydata)
    # ACTOR for points
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetPointSize(apoint_size)
    return actor, polydata


def face_points2actor(fps_df):

    cell_array = vtk.vtkCellArray()
    points = vtk.vtkPoints()
    point_id = 0
    for i in range(fps_df.shape[0]):
        polygon = vtk.vtkPolygon()
        polygon.GetPointIds().SetNumberOfIds(3)
        for n in range(3):
            points.InsertNextPoint(fps_df.ix[i, 0+3*n], fps_df.ix[i, 1+3*n], fps_df.ix[i, 2+3*n])
            polygon.GetPointIds().SetId(n, point_id)
            point_id += 1
        cell_array.InsertNextCell(polygon)
    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    polydata.SetPolys(cell_array)

    # mapper
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInput(polydata)
    # actor
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    return actor, polydata


def xy_axis(apoints_path):

    # print a green y-positive and a x-positive line in the centre
    sensor = pd.read_csv(apoints_path)
    mid_x = sensor[['sen_x']].mean(axis=0)
    mid_y = sensor[['sen_y']].mean(axis=0)
    mid_z = sensor[['sen_z']].mean(axis=0)
    min_z = sensor[['sen_z']].min(axis=0)
    max_x = sensor[['sen_x']].max(axis=0)
    max_y = sensor[['sen_y']].max(axis=0)
    pts = vtk.vtkPoints()
    pts.InsertNextPoint([mid_x, mid_y, min_z])
    pts.InsertNextPoint([max_x, mid_y, min_z])
    pts.InsertNextPoint([mid_x, max_y, min_z])
    # Setup two colors - one for each line
    red = [255, 0, 0]
    green = [0, 255, 0]
    colors = vtk.vtkUnsignedCharArray()
    colors.SetNumberOfComponents(3)
    colors.SetName("Colors")
    colors.InsertNextTupleValue(red)
    colors.InsertNextTupleValue(green)
    line0 = vtk.vtkLine()
    line0.GetPointIds().SetId(0, 0)
    line0.GetPointIds().SetId(1, 1)
    line1 = vtk.vtkLine()
    line1.GetPointIds().SetId(0, 0)
    line1.GetPointIds().SetId(1, 2)
    lines = vtk.vtkCellArray()
    lines.InsertNextCell(line0)
    lines.InsertNextCell(line1)
    linespolydata = vtk.vtkPolyData()
    linespolydata.SetPoints(pts)
    linespolydata.SetLines(lines)
    linespolydata.GetCellData().SetScalars(colors)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInput(linespolydata)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    mid_point = [mid_x, mid_y, mid_z]

    return actor, mid_point


def get_colors(irradiance_array, min_irr, max_irr):

    rgb = np.zeros((len(irradiance_array), 3))
    # scale irradiance values
    n_col = irradiance_array / max_irr
    # set rgb color scale from blue over green to red
    for k in range(0, len(irradiance_array)):
        col_map = cm.get_cmap('inferno')

        rgb[k][0] = col_map(n_col[k])[0]*255
        rgb[k][1] = col_map(n_col[k])[1]*255
        rgb[k][2] = col_map(n_col[k])[2]*255

    return rgb


def visualize(arepeating_timer):

    '''
    geometry_path: stl file directory or point and faces file path
    geometry_name: stl file list,
    data_path: data file path, txt document
    '''


    # =============================== timer event =============================== #
    class VtkTimerCallback:
        def __init__(self):
            self.timer_count = 0

        def execute(self, obj, event):
            print "\r", self.timer_count,
            for name in data_lib:
                data_array = data_lib[name][self.timer_count]
                data_max = np.max(data)
                rgb = get_colors(data_array, 0, data_max)

                colors = vtk.vtkUnsignedCharArray()
                colors.SetNumberOfComponents(3)
                colors.SetName("Colors")

                for l in range(0, len(rgb)):
                    for j in range(count_lib[name]):
                        colors.InsertNextTuple(rgb[l])
                    polydata_lib[name].GetCellData().SetScalars(colors)
                    polydata_lib[name].GetCellData().Update()

            if move_cam_bool is True:
                camera.SetPosition(camera_xyz[self.timer_count%360])
            camera.SetViewUp(0, 0, 1)
            camera.SetFocalPoint(mid_point[0], mid_point[1], mid_point[2])

            txt.SetInput("time: "+str(self.timer_count))

            render_window.Render()

            iren = obj
            iren.GetRenderWindow().Render()

            imageFilter.Modified()

            if self.timer_count < data_lib[name].shape[0]-1:
                self.timer_count += 1
            else:
                self.timer_count = 0

    # ============================== camera ============================== #
    camera = vtk.vtkCamera()
    if move_cam_bool is True:
        camera_xyz = []
        for i in range(start_angle, end_angle):
            phi = i * step_size
            camera_xyz.append(
                (mid_point[0] + radius * 6 * math.sin(phi), mid_point[1] + radius * 6 * math.cos(phi),
                 cam_height+mid_point[2]))


    # ============================== text ============================== #
    txt = vtk.vtkTextActor()
    txtprop = txt.GetTextProperty()
    txtprop.SetFontFamilyToArial()
    txtprop.SetFontSize(txt_font_size)
    txtprop.SetColor(txt_color)
    txt.SetDisplayPosition(2, 2)

    # =============================== initialize visualization =============================== #
    renderer = vtk.vtkRenderer()
    renderer.SetActiveCamera(camera)
    render_window = vtk.vtkRenderWindow()
    render_window_interactor = vtk.vtkRenderWindowInteractor()

    # Add actor to the scene
    renderer.AddActor(txt)
    cb = VtkTimerCallback()
    renderer.AddActor(axes)
    cb.actor = axes
    for name in actor_lib:
        renderer.AddActor(actor_lib[name])
        cb.actor = actor_lib[name]

    # Background
    renderer.SetBackground(background_color)
    # Reset camera
    renderer.ResetCamera()
    # Render window
    render_window.AddRenderer(renderer)
    # Interactor
    render_window_interactor.SetRenderWindow(render_window)
    # Begin interaction
    render_window.Render()
    # Initialize must be called prior to creating timer events.
    render_window_interactor.Initialize()
    # Sign up to receive TimerEvent
    render_window_interactor.AddObserver('TimerEvent', cb.execute)
    render_window_interactor.CreateRepeatingTimer(arepeating_timer)

    # Setup filter
    imageFilter = vtk.vtkWindowToImageFilter()
    imageFilter.SetInput(render_window)
    imageFilter.SetInputBufferTypeToRGB()
    imageFilter.ReadFrontBufferOff()
    imageFilter.Update()

    render_window_interactor.Start()


if __name__ == '__main__':

    move_cam_bool = False
    background_color = [1, 1, 1]

    # camera properties
    cam_height = 200
    radius = 50
    start_angle = 0
    end_angle = 360
    step_size = math.pi / 90
    repeating_timer = 20
    #text properties
    txt_font_size = 18
    txt_color = (0.4, 0.4, 0.4)

    # file paths
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario=scenario_path)
    in_path = locator.get_3D_geometry_folder()
    out_path = locator.get_solar_radiation_folder()
    geo_list = pd.read_csv(os.path.join(in_path, 'background_geometries.csv'))['name']
    sen_list = pd.read_csv(os.path.join(in_path, 'sensor_geometries.csv'))['name']

    # create actors to show including actors, polydata, data (for coloring) and count
    start_h = 3000
    nr_hours = 200
    actor_lib = {}
    polydata_lib = {}
    data_lib = {}
    count_lib = {}

    # stl example
    for name in geo_list:
        actor_lib[name], polydata_lib[name] = stl2actor(in_path, name, [0.7, .7, .7])
        count_lib[name] = polydata_lib[name].GetNumberOfCells()
        path = os.path.join(out_path, name,'res')

        #data = pd.read_csv(os.path.join(path, name+'.csv'), sep=',', skiprows=start_h, nrows=nr_hours, header=None)
        #data = data.astype(float)
        #data = data.as_matrix()
        #data_lib[name] = data


    # point example
    for name in sen_list:

        xyz = pd.read_csv(os.path.join(out_path, name+'_sen_df.csv'))[['sen_x', 'sen_y', 'sen_z']]
        actor_lib['pt_'+name], polydata_lib['pt_'+name] = points2actor(xyz, apoint_size=8)
        count_lib['pt_'+name] = 1
        path = os.path.join(out_path, name, 'res')
        data = pd.read_csv(os.path.join(path, name+'.ill'), sep=' ', skiprows=start_h, nrows=nr_hours, header=None).ix[: ,4:]
        data = data.astype(float)
        data = data.as_matrix()
        data_lib['pt_'+name] = data
    '''
    # face example
    for name in sen_list:

        fps_df = pd.read_csv(os.path.join(out_path,name+'_fps_df.csv'))
        actor_lib['f_'+name], polydata_lib['f_'+name] = face_points2actor(fps_df)
        count_lib['f_'+name] = 1
        path = os.path.join(out_path, name, 'res')
        data = pd.read_csv(os.path.join(path, name+'.ill'), sep=' ', skiprows=start_h, nrows=nr_hours,header=None).ix[:, 4:]
        data = data.astype(float)
        data = data.T
        data.reset_index(inplace=True)
        data.drop('index', axis=1, inplace=True)
        sensor = pd.read_csv(os.path.join(out_path, name+'_sen_df.csv'))['fac_int']
        data['fac_int'] = sensor
        data = data.groupby(['fac_int']).mean()
        data = data.as_matrix()
        data_lib['f_'+name] = data.T
    '''
    # give a path with "sen_x,..." columns to calculate where the camera focuses on
    axes, mid_point = xy_axis(os.path.join(out_path, sen_list[0]+'_sen_df.csv'))

    point_size = 5
    visualize(repeating_timer)


