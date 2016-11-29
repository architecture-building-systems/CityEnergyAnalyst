classdef Abstractlayout < handle
% This class represents an abstract graph layout. Subclass to create actual
% layouts.  

  properties(Abstract = true)
     xmin;               % The left most point on the graph axis in data units           
     xmax;               % The right most point on the graph axis in data units
     ymin;               % The bottom most point on the graph axis in data units
     ymax;               % The top most point on the graph axis in data units
     adjMatrix;          % The adjacency matrix
     maxNodeSize;        % The maximum diameter of a node in data units
     image;              % A 20-by-20-by-3 array specifying an image for 
                         % the smartgraph button that will launch this
                         % layout.
     name;               % A unique name for instances of this class. 
     shortDescription;   % A short description used for tooltips.
     nodeSize;           % The calculated node size, call dolayout() before accessing
     centers;            % The calculated node centers in an n-by-2 matrix
  end
    
   methods
       function dolayout(obj,adjMatrix,graphAxis,maxNodeSize)
       % Calculate the node centers and an optimal size
            obj.adjMatrix = adjMatrix;
            obj.maxNodeSize = maxNodeSize;
            xlimits = get(graphAxis,'XLim');
            ylimits = get(graphAxis,'YLim');
            obj.xmin = xlimits(1); obj.xmax = xlimits(2);
            obj.ymin = xlimits(1); obj.ymax = ylimits(2);
            obj.calcLayout();
       end
       
       function available = isavailable(obj)
       % Test to see if this layout is available.    
           available = true;
       end
       
   end
   
   methods(Access = 'protected')
      
       function setImage(obj,color)
       % Sets the image to a grid with the specified color in rgb normalized
       % units, i.e. [0.2 0.5 0.9].
            obj.image = cat(3,color(1)*ones(20,20),color(2)*ones(20,20),color(3)*ones(20,20));
            obj.image(1:4:20,:,:) = 0;
            obj.image(:,1:4:20,:) = 0;
       end
       
       
   end
   
   methods(Abstract = true, Access = 'protected')
       calcLayout(obj);     % do the actual work
   end
    
end