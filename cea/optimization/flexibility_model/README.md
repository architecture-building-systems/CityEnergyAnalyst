# '''CONCEPT - Connecting District Energy and Power Systems in Future Singaporean New Towns
    mpc-buiding folder:
    1. MPC model
    2. Objective function for optimization: Operation cost
    3. Constraints: Building Comfort constraints
    4. We dont consider the electric grid, we assume that electricity will be available from some source, and no line constraints
    
    mpc-district folder:
    1. MPC model
    2. Objective function for optimization: Investment costs for electric lines, substation, Maintenance costs + Operation Costs
    3. Constraints: Capacity limits corresponding to electric grids, Iine types, Building Comfort constraints
    4. This is the overall electric grid planning, including the buildings connected, and investment costs and the electricity costs (operation costs)
'''
## Prerequisites

1. Install the license of Gurobi in your computer. you can obtain one in gurobi.com for free for academic purposes
        
        do conda env update
        do activate cea
        do grbgetkey xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    
    where xxxxxxxxxxxxxxxxxxxxxxxxxx is the key of your license. 

2. If you are having problems running from pycharm. get today's version 06.03.2019 or later one. This includes a fix to paths in conda.
    you should be able to run it from the comand line anywise