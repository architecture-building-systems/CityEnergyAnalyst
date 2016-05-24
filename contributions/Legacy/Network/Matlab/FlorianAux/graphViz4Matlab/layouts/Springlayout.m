classdef Springlayout < Gvizlayout
% A layout that also uses graphviz but calls twopi instead of neato to 
% to display the graph like a tree. 
%
% Matthew Dunham
% University of British Columbia 
% http://www.cs.ubc.ca/~mdunham/  
    methods
       function obj = Springlayout(name)
            if(nargin < 1)
                obj.name = 'springlayout';
            else
                obj.name = name;
            end
            load glicons;
            obj.image = icons.spring;
            obj.shortDescription = 'Spring Layout (GraphViz)'; 
       end
       
       function available = isavailable(obj)
        % Make sure graphViz is available. 
            available = Gvizlayout.queryGviz('fdp');
            if(not(available))
                 fprintf('Please install or upgrade graphViz\n');
            end
        end
       
    end
    
    methods(Access = 'protected')
      
       function callGraphViz(obj)
       % Call GraphViz to determine an optimal layout. Write this layout in
       % layout.dot for later parsing. 
           err = system(['fdp -Tdot -Gmaxiter=5000 -Gstart=7 -o ',obj.layoutFile,' ',obj.adjFile]);
           if(err),error('Sorry, unknown GraphViz failure, try another layout'); end
       end
       
       
      
    end
   
end