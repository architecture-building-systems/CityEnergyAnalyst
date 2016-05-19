function r = graphViz4MatlabRoot()
% Return directory name where graphlayout is stored
[pathstr,name,ext,versn] = fileparts(which(mfilename));
r = pathstr;
end
