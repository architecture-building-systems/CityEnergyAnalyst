:orphan:

How to Run MPC Building Toolbox
===============================
The MPC Building Toolbox minimize the electricity costs for cooling when the electricity prices are flunctuating.

Input
-----
#. Range of the building temperature according to thermal comfort standard. 
#. Hourly electricity price.

Prerequisites
-------------
#. Install the license of Gurobi in your computer. you can obtain one in gurobi.com for free for academic purposes.
#. Add Gurobi package to the cea environment::
   
   *open anaconda
   *do ``conda env update``
   *do ``activate cea``
   *do ``grbgetkey xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`` 
   (where xxxxxxxxxxxxxxxxxxxxxxxxxx is the key of your license.)
   
#. If you are having problems running from pycharm. get today's version 06.03.2019 or later one. This includes a fix to paths in conda.


Steps
-----
#. Assign optimization parameters in ``cea.config``
#. Run `cea\optimization\flexibility_model\mpc_building\operation_main.py`
#. Check results from optimization in ``...scenario\outputs\mpc-building``


Outputs
-------
The results from the optimization are saved for each building. In ``Bxxx_outputs.csv`` you will find:

* Hourly temperature set-points for each function in the building
* Hourly air flows
* Hourly electricity consumption for cooling


Calculation flowchart
---------------------

.. image:: flowchart_mpc_building.png
    :align: center

