
# Uncertainty Analysis

How to do Uncertainty Analysis:

1. Before doing the Analysis, update the database present in CEA -> databases -> Uncertainty -> uncertainty_distributions.xls
2. 

1. **Building retrofits**: Appliances and lighting, building envelope, HVAC systems (incl. Control strategies)
2. **Integration of local energy sources**: renewable and waste-to-heat energy sources.
3. **Infrastructure retrofits**: decentralized and centralized thermal micro-grids and conversion technologies.
4. **Modifications to urban form**: new zoning, changes in occupancy and building typology.

![](Screen Shot 2016-05-09 at 11.25.29 am.png)

## History

The City Energy Analyst launched at the end of 2015 with two objectives in mind. The first was to empower urban designers and energy engineers to create holistic plans for low-carbon cities. The second was to allow researchers of energy and the built environment to build on the-state-of-the-art more easily. [Dr. Jimeno A. Fonseca](http://www.fcl.ethz.ch/people/Researchers/JimenoFonseca.html), co-creator of the tool, spent years creating and coding both existing and new computational methods for the analysis of energy efficiency in city districts. We would have hated to put his research and byproducts (more than 5000 lines of python code) in the drawer.

Nowadays the City Energy analyst is maintained by the Chair of Architecture and building Systems at ETH Zurich and the [Future Cities Laboratory](http://www.fcl.ethz.ch) at the Singapore-ETH centre under the supervision of [Prof. Dr. Arno Schlueter](http://www.fcl.ethz.ch/people/CoreTeam/ArnoSchlueter.html) and [Dr. Jimeno A. Fonseca](http://www.fcl.ethz.ch/people/Researchers/JimenoFonseca.html).


## Features

The CEA is the first open-source initiative of computation tools for the design of low-carbon and highly efficient cities.

The CEA combines knowledge of urban planning and energy systems engineering into an integrated simulation platform. This allows to study the effects, trade-offs and synergies of urban design options and energy infrastructure plans.

In time-steps of an hour, the CEA calculates the combined processes of generating, distributing and consuming energy in an urban area. For this, the CEA uses the state-of-the-art in computational models made to this end. 

The CEA connects to a geographic information system (ArcGIS V10.4). The system allows to intuitively represent patterns of supply and demand in time and space. This feature will allow future practitioners to more easily discuss plans of energy efficiency to a non-expert audience.

## Limitations

The CEA is based on academic work and contributions of a wide range of users. The developing team made its best to create a reliable piece of software. It might have bugs here and there. Please report them at convenience. The Archetypes database shipped with the CEA V1.0b is only valid for the European context. It might not always be closely related to any other context. Users are advised to create their own database based on local measurements.

CEA V1.0b presents a series of limitations in terms of model accuracy, user experience and concept of operations.

Based on data of [1], the demand module of the CEA Toolbox has a mean error of 32% at the building scale and 5% at neighborhood scale (n=24). Future work to decrease this error might lie on calibration with sensor data and implementation of more advanced models for air-ventilation and occupancy.

The CEA toolbox V1.0b provides a limited analysis of alternatives for energy generation. It neglects the economics and technical restrictions of infrastructure during design and operation. The future implementation of thework of [1] and [2]  should address this limitation.

The toolbox presents low levels of automation in regards to reporting and generation of multiple scenarios.  Future tests with urban designers and energy systems engineers would help to identify other features that enhance user experience.


### Contributors to this manual
* [Dr. Amr Elesawy](http://www.systems.arch.ethz.ch/about-us/team/team-zurich/amr-elesawy.html) / Architecture and Building Systems - ETH-Zurich; 
* [Zhongming Shi](http://www.fcl.ethz.ch/people/Researchers/ShiZhongming.html/) / Future Cities Laboratory - Singapore-ETH Centre, 
* [Dr. Jimeno A. Fonseca](http://www.fcl.ethz.ch/people/Researchers/JimenoFonseca.html) / Future Cities Laboratory - Singapore-ETH Centre; 
* [Daren Thomas](http://www.systems.arch.ethz.ch/about-us/team/team-zurich/daren-thomas.html) / Architecture and Building Systems - ETH-Zurich; 



