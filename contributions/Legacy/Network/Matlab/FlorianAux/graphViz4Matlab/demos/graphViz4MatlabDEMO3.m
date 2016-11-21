adj = rand(4) > 0.5;
descriptions = {'First Random Node','Yet another node','The thrid one','The final node'};
colors = [0 0.5 0.2];  % either use string names for colors or normalized rgb values
graphViz4Matlab('-adjMat',adj,'-nodeDescriptions',descriptions,'-nodeColors',colors);

% double click on the nodes to see and edit descriptions. 