classdef Treelayout < Gvizlayout
% A layout that also uses graphviz but calls dot instead of neato to 
% to display the graph like a tree.
%
% Matthew Dunham
% University of British Columbia 
% http://www.cs.ubc.ca/~mdunham/
  
    methods
       function obj = Treelayout(name)
            if(nargin < 1)
                obj.name = 'Treelayout';
            else
                obj.name = name;
            end
           %obj.setImage([0,153,102]/255);
           load glicons;
           obj.image = icons.tree;
           obj.shortDescription = 'Tree Layout (GraphViz)'; 
       end
       
       function available = isavailable(obj)
        % Make sure graphViz is available. 
            available = Gvizlayout.queryGviz('dot');
            if(not(available))
                 fprintf('Please install or upgrade graphViz\n');
            end
        end
       
    end
    
    methods(Access = 'protected')
      
       function callGraphViz(obj)
       % Call GraphViz to determine an optimal layout. Write this layout in
       % layout.dot for later parsing. 
           err = system(['dot -Tdot -Gmaxiter=5000 -Gstart=7 -o ',obj.layoutFile,' ',obj.adjFile]);
           if(err),error('Sorry, unknown GraphViz failure, try another layout'); end
       end
       
       
      
    end
    
    
   
    
    
    
    
end