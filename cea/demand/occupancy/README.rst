.. image:: https://static1.squarespace.com/static/587d65bdbebafb893ba24447/t/587d845d29687f2d2febee75/1492591264954/?format=1500w
    :height: 50 px
    :width: 150 px
    :scale: 50 %
    :alt: City Energy Analyst (CEA) logo
    :target: https://www.cityenergyanalyst.com

The  `City Energy Analyst (CEA) <https://www.cityenergyanalyst.com/>`_ includes two building occupancy models found in
`occupancy_model.py`: a deterministic model based on standard schedules and a stochastic model based on the work of Page
et al. (2008). Running the CEA demand script generates a set of schedules for each building that are exported to the
folder `outputs\data\schedules`. Both of these models use the archetypal schedules in the CEA database found in the file
`archetypes\occupancy_schedules.xlsx`.

Alternatively, users can input their own building schedules by placing these as csv files in the folder
`inputs\building-schedules`. For a given building, if schedules are found in the input folder, CEA will override the
step that produces the building schedules.

As a final option, CEA includes a script to import a population from agent-based transportation simulation MATSim as a
source for the occupancy schedules used in cea (`occupancy_from_transportation_data.py`). This script requires two
additional inputs (`inputs\transportation-data`):
- a MATSim population file (`population.xml`) containing a list of agents, their occupation, their activities and their location in a case study;
- a csv file (`facilities.csv`) that matches a MATSim facility id to a building name in the CEA case study.
The latter file is required given that MATSim facilities often do not match buildings one-to-one, e.g. by clustering
groups of buildings as a single facility. `facilities.csv` should therefore contain at least two columns: one column
labeled `Name` that corresponds to the names of the buildings in the CEA case study, and one labeled `id` that
corresponds to the facility id's in the MATSim case study. At the moment, supported user types are limited to students
and employees, and these are assumed to carry out their activities in certain building spaces only (`'student'`:
`['SCHOOL', 'UNIVERSITY']`; `'employee'`: `['OFFICE', 'LAB', 'HOSPITAL', 'INDUSTRIAL']`). As a result, CEA schedules
are generated for each building included in the MATSim population file and placed in the CEA inputs folder
(`inputs\building-schedules`) to be used by the CEA demand tool.
