classdef Circlelayout < Abstractlayout
% A simple layout which places node onto a scaled unit circle. 
%
% Matthew Dunham
% University of British Columbia 
     properties
        xmin;               % The left most point on the graph axis in data units           
        xmax;               % The right most point on the graph axis in data units
        ymin;               % The bottom most point on the graph axis in data units
        ymax;               % The top most point on the graph axis in data units
        adjMatrix;          % The adjacency matrix
        maxNodeSize;        % The maximum diameter of a node in data units
        image;              % An image for the button that will lanuch this layout
        name;               % A unique name for instances of this class
        shortDescription;   % A description for use in the tooltips
        nodeSize;           % The calculated node size, call dolayout() before accessing
        centers;            % The calculated node centers in an n-by-2 matrix
     end
    
     methods     
         function obj = Circlelayout(name)
         % constructor
            if(nargin < 1)
                obj.name = 'circlelayout';
            else
                obj.name = name;
            end
            load glicons;
            obj.image = icons.circle;
            obj.shortDescription = 'Simple Circle Layout'; 
         end
     end
     
     methods(Access = 'protected')
       
        function calcLayout(obj)
            nnodes = size(obj.adjMatrix,1);
            step = 2*pi/(nnodes);
            t = 0:step:2*pi;
            x = 0.4*sin(t)+0.5;
            y = 0.4*cos(t)+0.5;
           
            x = obj.xmin + x ./ (obj.xmax - obj.xmin);
            y = obj.ymin + y ./ (obj.ymax - obj.ymin);
            obj.centers = [x',y'];
            d = sqrt((x(2)- x(1))^2 + (y(2) - y(1))^2);
            obj.nodeSize = min(2*d/3,obj.maxNodeSize);
        end
    
     end
    
    
    
end