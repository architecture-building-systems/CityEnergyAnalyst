Basic process:

1. Substations are calculated for all buildings. The highest temperature of the system is selected for every timestep as the temperature of the grid + a dT of 5 degrees (approach temperature)
2. Then we create a hydraulic model in Epanet with one reservoir.
3. Then we run the model for 8760 hours and extract the peak mass flow rates of the grid.
4. Based on the maximum velocity allowed in the grid (user input) and the maximum mass flow rate (Epanet output) we size the network.
5. With the new pipe sizes, we model the network again in Epanet. This time we vary the reservoir elevation to compensate the pressure drop required by the network every hour.
6. The Epanet model gives us pressure losses, and pumping requirements. We save the results.
7. Finally, we separately calculate the thermal losses of the grid using Fourier's heat transfer equations. We assume the average temperature of the entire network at every time-step and the temperature of the soil as boundary conditions.