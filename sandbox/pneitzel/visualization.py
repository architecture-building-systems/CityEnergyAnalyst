import os
import math
import pandas as pd

def stl2actor(ageometry_path, ageometry_name, ageometry_color):
    import vtk

    if len(ageometry_name) > 1:
        appendfilter = vtk.vtkAppendPolyData()
        render_lib = {}
        polydata = {}
        bui_int = 0
        for building in ageometry_name:
            render_lib[building] = vtk.vtkSTLReader()
            polydata[building] = vtk.vtkPolyData()
            render_lib[building].SetFileName(os.path.join(ageometry_path, building+".stl"))
            render_lib[building].Update()
            polydata[building].ShallowCopy(render_lib[building].GetOutput())
            appendfilter.AddInputConnection(polydata[building].GetProducerPort())
            appendfilter.Update()
            bui_int += 1

        #  Remove any duplicate points.
        cleanfilter = vtk.vtkCleanPolyData()
        cleanfilter.SetInputConnection(appendfilter.GetOutputPort())
        cleanfilter.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(cleanfilter.GetOutputPort())

    else:
        filename = os.path.join(ageometry_path, ageometry_name[0])
        reader = vtk.vtkSTLReader()
        reader.SetFileName(filename)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInput(reader.GetOutput())
        polydata = ""

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
        p = xyz[i]
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


def face_points2actor(faces_points):



    import vtk
    cell_array = vtk.vtkCellArray()
    points = vtk.vtkPoints()



    #nr_faces = int(faces_points[1].iloc[-1]) + 1

    nr_faces = faces_points[1][len(faces_points)-1]+1

    point_id = 0
    triangle_order = [1,2,0,3]

    for i in range(nr_faces):
        faces_point = faces_points.loc[faces_points[1] == i].values.tolist()

        #faces_point = faces_points[i*3:(i+1)*3].reset_index()

        polygon = vtk.vtkPolygon()
        polygon.GetPointIds().SetNumberOfIds(len(faces_point))
        for n in range(len(faces_point)):

            points.InsertNextPoint(faces_point[n][2], faces_point[n][3], faces_point[n][4])

            if len(faces_point) == 4:

                polygon.GetPointIds().SetId(triangle_order[n], point_id)
            else:

                polygon.GetPointIds().SetId(n, point_id)
            point_id += 1

        '''
        points.InsertNextPoint(faces_point[0][1], faces_point[0][2], faces_point[0][3])
        points.InsertNextPoint(faces_point[1][1], faces_point[1][2], faces_point[1][3])
        points.InsertNextPoint(faces_point[2][1], faces_point[2][2], faces_point[2][3])
        points.InsertNextPoint(faces_point[3][1], faces_point[3][2], faces_point[3][3])


        if len(faces_point) == 4:
            polygon = vtk.vtkPolygon()
            polygon.GetPointIds().SetNumberOfIds(4)
            polygon.GetPointIds().SetId(0, i * 4 + 0)
            polygon.GetPointIds().SetId(3, i * 4 + 1)
            polygon.GetPointIds().SetId(2, i * 4 + 2)
            polygon.GetPointIds().SetId(1, i * 4 + 3)
        '''



        '''
        triangle = vtk.vtkTriangle()
        triangle.GetPointIds().SetId(0, i * 3 + 0)
        triangle.GetPointIds().SetId(1, i * 3 + 1)
        triangle.GetPointIds().SetId(2, i * 3 + 2)
        '''
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
    import vtk
    import pandas as pd

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
    import numpy as np
    rgb = np.zeros((len(irradiance_array), 3))
    # scale irradiance values
    # n_col = (irradiance_array-min_irr) / (max_irr-min_irr)
    n_col = irradiance_array / max_irr
    # set rgb color scale from blue over green to red
    for k in range(0, len(irradiance_array)):
        if irradiance_array[k] < 15:
            rgb[k][0] = 0
            rgb[k][1] = 0
            rgb[k][2] = 0
        elif 0 <= n_col[k] < 0.25:
            rgb[k][0] = 0
            rgb[k][1] = 255 * n_col[k] * 4
            rgb[k][2] = 255
        elif 0.25 <= n_col[k] < 0.5:
            rgb[k][0] = 0
            rgb[k][1] = 255
            rgb[k][2] = 255 * (1 - 4 * (n_col[k] - 0.25))
        elif 0.5 <= n_col[k] < 0.75:
            rgb[k][0] = 255 * 4 * (n_col[k] - 0.5)
            rgb[k][1] = 255
            rgb[k][2] = 0
        else:
            rgb[k][0] = 255
            rgb[k][1] = 255 * (1 - 4 * (n_col[k] - 0.75))
            rgb[k][2] = 0
    return rgb


def visualize(ageometry_path, ageometry_name, apoints_path, afaces_path, aterrrain_path, aterrain_name, avisual_style,
              apoint_size, adata_path, ast_row, aend_row, arepeating_timer):

    '''
    geometry_path: stl file directory or point and faces file path
    geometry_name: stl file list,
    data_path: data file path, txt document
    '''

    import vtk
    import pandas as pd
    from OCC import TopoDS
    from OCC.StlAPI import StlAPI_Reader
    import numpy as np
    import py3dmodel

    print "visualize", avisual_style
    # =============================== timer event =============================== #

    class VtkTimerCallback:
        def __init__(self):
            self.timer_count = 0

        def execute(self, obj, event):
            print "\r", self.timer_count,
            data_array = data[self.timer_count]

            rgb = get_colors(data_array, 0, data_max)

            if avisual_style == "buildings":

                for k in range(0, len(rgb)):
                    colors = vtk.vtkUnsignedCharArray()
                    colors.SetNumberOfComponents(3)
                    colors.SetName("Colors")
                    for j in range(0, face_nr_list[k]):
                        colors.InsertNextTuple(rgb[k])
                    polydata[ageometry_name[k]].GetCellData().SetScalars(colors)
                    polydata[ageometry_name[k]].GetCellData().Update()

            else:
                colors = vtk.vtkUnsignedCharArray()
                colors.SetNumberOfComponents(3)
                colors.SetName("Colors")
                for l in range(0, len(rgb)):
                    colors.InsertNextTuple(rgb[l])
                    polydata.GetCellData().SetScalars(colors)

            ''''''
            camera.SetPosition(camera_xyz[self.timer_count])
            camera.SetViewUp(0, 0, 1)
            camera.SetFocalPoint(mid_point[0], mid_point[1], mid_point[2])

            txt.SetInput("time: "+str(self.timer_count))

            render_window.Render()


            iren = obj
            iren.GetRenderWindow().Render()

            imageFilter.Modified()
            writer.Write()

            if self.timer_count < data.shape[0]-1:
                self.timer_count += 1
            else:
                #writer.End()
                self.timer_count = 0


    # =============================== Geomerty =============================== #


    if avisual_style == "buildings" or "points":
        bui_actor, polydata = stl2actor(ageometry_path, ageometry_name, building_color)
        building_solids = []
        for bui in ageometry_name:
            filepath = os.path.join(ageometry_path, bui + ".stl")
            building_solid = TopoDS.TopoDS_Solid()
            StlAPI_Reader().Read(building_solid, str(filepath))
            building_solids.append(building_solid)
        face_nr_list = []
        for b_solid in building_solids:

            face_list = py3dmodel.fetch.faces_frm_solid(b_solid)
            face_nr_list.append(len(face_list))

    if avisual_style == "faces":
        faces_points = pd.read_csv(afaces_path, header=None)

        face_actor, polydata = face_points2actor(faces_points)

    if avisual_style == "points":
        sensor = pd.read_csv(apoints_path)
        xyz = sensor.loc[:, ['sen_x', 'sen_y', 'sen_z']].values.tolist()
        sen_actor, polydata = points2actor(xyz, apoint_size)

    # =============================== data =============================== #
    nr_rows = aend_row-ast_row
    data = pd.read_csv(adata_path, sep=',', skiprows=ast_row, nrows=nr_rows, header=None)


    data = data.as_matrix()
    data_max = np.max(data)

    # =============================== axes =============================== #
    axes, mid_point = xy_axis(apoints_path)

    # ============================== camera ============================== #
    camera = vtk.vtkCamera()
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

    #terrain, polydata_dummy = stl2actor(aterrrain_path, aterrain_name, terrain_color)
    terrain_path = os.path.join(results_path, "temp", 'terrain_points_0.csv')
    terrain_points = pd.read_csv(terrain_path, header=None)
    #terrain, polydata_dummy = face_points2actor(terrain_points)

    # =============================== initialize visualization =============================== #
    renderer = vtk.vtkRenderer()
    if move_cam_bool is True:
        renderer.SetActiveCamera(camera)
    render_window = vtk.vtkRenderWindow()
    render_window_interactor = vtk.vtkRenderWindowInteractor()

    # Add actor to the scene
    renderer.AddActor(txt)
    cb = VtkTimerCallback()

    if axes_bool is True:
        renderer.AddActor(axes)
    if terrain_bool is True:
        renderer.AddActor(terrain)

    if avisual_style == "points":
        renderer.AddActor(bui_actor)
        renderer.AddActor(sen_actor)
        cb.actor = sen_actor
    if avisual_style == "buildings":
        renderer.AddActor(bui_actor)
        cb.actor = bui_actor
    if avisual_style == "faces":
        renderer.AddActor(face_actor)
        cb.actor = face_actor

    # ============================== movie ============================== #

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

    # Setup movie writer

    writer = vtk.vtkAVIWriter()
    writer.SetInputConnection(imageFilter.GetOutputPort())
    writer.SetFileName(os.path.join(results_path, project_name+".avi"))
    writer.Start()


    render_window_interactor.Start()



# ============================================================== #
#                                Main                            #
# ============================================================== #


terrain_bool = False
move_cam_bool = False
axes_bool = True
background_color = [1, 1, 1]
building_color = [0.7, .7, .7]
terrain_name = ["terrain2d.stl"]
terrain_color = (0.3, 0.3, 0.3)


cam_height = 400
radius = 50
start_angle = 0
end_angle = 365
step_size = math.pi / 90

repeating_timer = 50

txt_font_size = 18
txt_color = (0.8, 0.8, 0.8)

project_name = 'trial'
n_cores = 1
terrain_folder = "terrain"
current_path = os.path.dirname(__file__)
results_path = os.path.join(current_path, project_name)
input_path = 'C:\\Users\\lensa\\polybox\\Master_IBS\\04_semester\\masterthesis\\02_Simulation\\01_testcase\\' \
             'cea-reference-case\\reference-case\\baseline\\1-inputs'
terrrain_path = os.path.join(input_path, terrain_folder)
''''''
geometry_path = os.path.join(results_path, "temp", "geometry")


geometry_name = []
for file_name in os.listdir(geometry_path):
    if file_name.endswith(".stl"):
        root, ext = os.path.splitext(file_name)
        geometry_name.append(root)


faces_all = pd.DataFrame()
for n in range(n_cores):
    faces = pd.read_csv(os.path.join(results_path, "temp", 'bui_id_df_'+str(n)+'.csv'), sep=',')
    faces_all = pd.concat((faces_all, faces), axis=0)
faces_all.to_csv(os.path.join(results_path, 'bui_id_df.csv'), header=True, index=None)

points_path = os.path.join(results_path, 'bui_id_df.csv')



faces_all = pd.DataFrame()
for n in range(n_cores):
    faces = pd.read_csv(os.path.join(results_path, "temp", 'building_points_'+str(n)+'.csv'), sep=',', header=None)

    faces_all = pd.concat((faces_all, faces), axis=0)
int_list = faces_all[1].tolist()
last_int = int_list[0]

integer = 0
int_list_new = []
for i in range(len(int_list)):
    now_int = int_list[i]
    if now_int != last_int:
        integer += 1
    last_int = int_list[i]
    int_list_new.append(integer)


print int_list_new
faces_all[1] = int_list_new
faces_all.to_csv(os.path.join(results_path, 'building_points.csv'), header=None, index=None)



faces_path = os.path.join(results_path, 'building_points.csv')


visual_style = "faces"

point_size = 5

data_path = os.path.join(results_path, 'bui_fac_month.csv')

visualize(geometry_path, geometry_name, points_path, faces_path,  terrrain_path, terrain_name, visual_style,
          point_size, data_path, 1, 12, repeating_timer)

'''
'''