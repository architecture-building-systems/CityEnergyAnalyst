Glossary
========
This glossary contains all the input and output variables used by CEA. These variables are stored in databases,
themed by the type of information they contain. There are five main types of database in CEA:

    - **Input**

        These databases contain all necessary input data for each individual building and district
        and are used to define all optimisation variables.

    - **Case Specific**

        These are databases are relevant to the specified location and assumed operating conditions of the
        district. They consist of assumed archetypes, benchmarks, economic factors and lifecycle values specific to the
        case study.

    - **System**

        These databases contain variables which are related to the input and case specific databases and serve to combine
        all the relevant emission and construction variables into a single source ??.

    - **Uncertainty**

        This database is used for uncertainty distribution analysis and stores information regarding the probability
        density functions of several input parameters (such as the infiltration, window to wall ratio etc...).

    - **Output**

        The output databases store all the variables calculated by the CEA modules, which are subsequently used to plot various
        relationships (such as the pareto front of optimisation results).

.. toctree::

   databases
   codes_ref