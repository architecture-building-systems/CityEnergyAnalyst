classdef Gridlayout < Abstractlayout
% Provides a simple, (naive) grid layout for Graphlayout.   
% An uninitialized instance can be created to pass to the GraphLayout
% constructor by just calling Gridlayout without any parameters, e.g.
% Graphlayout('-adjMat',[0 1; 0 0], '-layout',Gridlayout);
%
% Matthew Dunham
% University of British Columbia 
% http://www.cs.ubc.ca/~mdunham/

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
        function obj = Gridlayout(name)
        
        % constructor
            if(nargin < 1)
                obj.name = 'Gridlayout';
            else
                obj.name = name;
            end
            load glicons;
            obj.image = icons.grid;
            obj.shortDescription = 'Grid Layout';
        end
     
    end
    
    
    methods(Access = 'protected')
       
        function calcLayout(obj)
            
            nnodes = size(obj.adjMatrix,1);
            obj.centers = zeros(nnodes,2);
            xspacePerNode = (obj.xmax - obj.xmin)/ceil(sqrt(nnodes));
            yspacePerNode = (obj.ymax - obj.ymin)/ceil(sqrt(nnodes));
            obj.nodeSize = min(min([xspacePerNode,yspacePerNode]./2),obj.maxNodeSize);
            xstart = obj.xmin + (xspacePerNode)/2;
            ystart = obj.ymin + (yspacePerNode)/2;
            counter = 1;
            for ypos=1:ceil(sqrt(nnodes))
                if(counter > nnodes),break,end
                for xpos=1:ceil(sqrt(nnodes))
                    obj.centers(counter,1) = xstart + (xpos-1)*xspacePerNode;
                    obj.centers(counter,2) = ystart + (ypos-1)*yspacePerNode;
                    positions(ypos,xpos) = counter; %#ok
                    counter = counter + 1;
                end
            end
            
            %swap out the center node for the node with the most edges,
            %(total of in and out). 
            edgeCounts = sum(obj.adjMatrix,1)' + sum(obj.adjMatrix,2);
            [vals ndx] = sort(edgeCounts,'descend');
            c = positions(ceil(size(positions,1)/2),ceil(size(positions,2)/2));
            if(c ~= 0)
                store = obj.centers(c,:);
                obj.centers(c,:) = obj.centers(ndx(1),:);
                obj.centers(ndx(1),:) = store;
            end
            
        end
        
        
    end
    
end