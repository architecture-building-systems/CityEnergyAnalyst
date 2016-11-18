classdef Randlayout < Abstractlayout
% A greedy, random layout - gives a different layout each time its called. 
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
        seed;               % The seed used to generate the last layout. 
     end
    
    
     
     methods
         
         function obj = Randlayout(name,seed)
         % constructor - seed is optional. 
            if(nargin < 1)
                obj.name = 'Randlayout';
            else
                obj.name = name;
            end
            if(nargin < 2)
                seed = 31;
            end
            obj.seed = seed;
            load glicons
            obj.image = icons.random;
            obj.shortDescription = 'Random Greedy Layout';
             
         end
     end
     
     methods(Access = 'protected')
       
         function calcLayout(obj)
             rand('twister',obj.seed); randn('state',obj.seed);
             obj.seed = obj.seed + 1;
             nnodes = size(obj.adjMatrix,1);
             obj.nodeSize = min(obj.maxNodeSize,2*(obj.xmax-obj.xmin)/nnodes);
             npoints = 25;
             locdist = ones(npoints,npoints);
             c = floor(0.4*npoints):ceil(0.6*npoints);
             locdist(c,c) = 1.5;                 % slightly favour the center
             locdist = locdist./sum(locdist(:)); % discrete distribution over locations
             locations = zeros(nnodes,2);        % holds indices into locdist
             nsize = ceil(npoints*(obj.nodeSize/2)/(obj.xmax - obj.xmin+obj.nodeSize));
             for i=1:nnodes
                while(true)
                    [xcandidate,ycandidate] = obj.sample(locdist);
                    [valid,locdist] = obj.isfree(xcandidate,ycandidate,locdist,nsize);
                    if(valid)
                       locations(i,:) = [xcandidate,ycandidate];
                       locdist = obj.radiate(locdist,locations,npoints);
                       break; 
                    end
                end
             end
             nedges = sum(obj.adjMatrix,1) + sum(obj.adjMatrix,2)';
             [val,perm] = sort(nedges,'descend');
             locations = locations(perm,:);
             obj.mapLocationsToAxes(locations,npoints);
         end
         
         function mapLocationsToAxes(obj,locations,npoints)
         % Map sampled locations on a grid to actual points on the graph
         % axes. 
             xndx = locations(:,1); yndx = locations(:,2);
             xmin = obj.xmin + obj.nodeSize/2;
             xmax = obj.xmax - obj.nodeSize/2;
             ymin = obj.ymin + obj.nodeSize/2;
             ymax = obj.ymax - obj.nodeSize/2;
             xstep = (xmax - xmin) /npoints;
             ystep = (ymax - ymin) /npoints;
             xpos = xmin+xstep:xstep:xmax;
             ypos = ymin+ystep:ystep:ymax;
             obj.centers =  [xpos(xndx)',ypos(yndx)'];
         end
         
         function [valid,locdist2] = isfree(obj,xcandidate,ycandidate,locdist,nsize)
         % Check if the sampled location is valid. Regardless, zero out the
         % spot so that we don't sample from here again. 
             xndx = max(1,xcandidate-nsize):min(xcandidate+nsize,size(locdist,2));
             yndx = max(1,ycandidate-nsize):min(ycandidate+nsize,size(locdist,1));
             nodeArea = locdist(xndx,yndx);
             valid = all(nodeArea(:));
             locdist2 = locdist;
             locdist2(xndx,yndx) = 0;
             locdist2 = locdist2 ./sum(locdist(:));
         end
         
         function locdist = radiate(obj,locdist,locations,npoints)
         % Update the location probability distribution.
             n = nnz(locations(:,1));
             loczeros = locdist == 0;
             for i=1:n             
                 [x y] = meshgrid(1:npoints,1:npoints);
                 x = x(:); y = y(:);
                 dist = sqrt((x-locations(i,1)).^2 + (y-locations(i,2)).^2);
                 locdist = locdist +  reshape(dist,npoints,npoints)';       
             end
             locdist(loczeros) = 0;
             locdist = locdist ./sum(locdist(:));
         end
 
        function [xndx,yndx] = sample(obj,dist)
        % Sample a single value from the non-uniform discrete distribution. 
            if(isnan(dist(1)))
                perm = randperm(size(dist,1));
                xndx = perm(1);
                yndx = perm(2);
                return;
            end
            r = rand;
            cumprob = cumsum(dist(:));
            s = sum(r > cumprob(1:end-1)) + 1;
            [xndx,yndx] = ind2sub(size(dist),s);
        end
        
     end
    
    
    
end