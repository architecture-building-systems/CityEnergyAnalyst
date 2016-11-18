%-----------------
% Florian Mueller
% December 2014
%-----------------

ld = LayoutData();
ld = setNewYork(ld);
hd = HydraulicData();
hd = setNewYork(hd,ld);

plotCuts(hd,int64(10),'Plots/','cuts');
plotLayout(ld,'Plots/','layout');
close all;

hs = HydraulicSolution();
fprintf('\nsolve hydraulic mixed integer linear program ...\n\n');
hs = solveHydraulicMixedIntLinProg(ld,hd,hs);

rhd = ReducedHydraulicData();
rhd = setNewYork(rhd,ld,hd,hs);

rhs = ReducedHydraulicSolution();
fprintf('\nsolve reduced hydraulic linear program ...\n\n');
rhs = solveReducedHydraulicLinProg(ld,hd,rhd,rhs);

td = ThermalData();
td = setNewYork(td,ld,hd,rhd,rhs);

ts = ThermalSolution();
fprintf('\nsolve thermal linear program ...\n\n');
ts = solveThermalLinProg(ld,hd,td,ts);

writeToMat(ld,'Mat/ld');
writeToMat(hd,'Mat/hd');
writeToMat(rhd,'Mat/rhd');
writeToMat(td,'Mat/td');
writeToMat(hs,'Mat/hs');
writeToMat(rhs,'Mat/rhs');
writeToMat(ts,'Mat/ts');

