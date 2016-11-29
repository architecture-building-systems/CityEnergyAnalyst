classdef graphViz4Matlab < handle    
% Visualize a graph in a Matlab figure window by specifying an
% adjacency matrix and optionally node labels, descriptions, colors and the
% the layout algorithm. The best layout algorithms require that graphViz be
% installed, available free at <http://www.graphviz.org>.
%
% Matthew Dunham
% University of British Columbia 
% Last Updated: January 14th, 2010
% Requires Matlab version 2008a or newer.
% 
% Syntax (see more examples below):
% graphViz4Matlab('-adjMat',adj,'-nodeLabels',labels,'-nodeColors',colors);
% 
% Self loops are removed and not represented on the graph.
% 
% Once the graph is displayed, there are several operations you can perform
% with the mouse.
% (1) Move a single node around.
% (2) Draw a mouse box around several nodes and move them all together.
% (3) Enter a description for a node by double clicking it. 
% (4) Shade the node by right clicking it
% (5) Display a node's properties on the console by shift clicking it. 
% (6) Increase or decrease the font size 
% (7) Increase or decrease the node size
% (8) Tighten the axes and relax the square aspect ratio.
% (9) Ask the current layout algorithm to layout the nodes as though the
%     arrows were pointing the other way. This only affects some of the
%     layouts. 
% (10) Change the layout algorithm and refresh the graph
%
% Additionally, any operation you could do with a regular Matlab figure can
% be done here, e.g. annotating or saving as a pdf. 
% 
% Options are specified via name value pairs in any order. 
% [] denote defaults. 
%
% '-adjMat'           [example matrix] The adjacency matrix
%
% '-layout'            [Gvizlayout if graphViz installed, else Gridlayout] 
%                      A layout object, i.e. Gvizlayout | Gridlayout | Circlelayout
%                     (See knownLayouts Property)
%
% '-nodeLabels'        ['1':'n'] A cell array of labels for the nodes
%
% '-nodeDescriptions'  [{}] Longer descriptions for the nodes, displayed when
%                      double clicking on a node.
% 
% '-nodeColors'        ['c'] A cell array or n-by-3 matrix specifying colors
%                      for the nodes. If fewer colors than nodes are specified, 
%                      the specified colors are reused and cycled through.
%
% '-undirected'        [false] If true, no arrows are displayed. 
% 
% '-edgeColors'        [] An n-by-3 cell array listing
%                         {fromName,toName,color} for each row. You can
%                         list only the n < numel(edges) edges you want to 
%                         color. If you do not label the nodes, graphViz4Matlab
%                         uses '1','2','3', etc, in which case use these.
%                         You can specify the text 'all' in place of toName,
%                         to mean all nodes, i.e. {fromName,'all',color}
%                        
% 
% '-splitLabels'       [true] If true, long node labels are split into
%                       several rows
%
% '-doubleClickFn'     (by default, double clicking a node brings up 
%                      an edit box for the node's description, but you
%                      can pass in a custom function handle. The function
%                      gets passed the node's label.
% Examples:
% 
% adj = rand(5,5) > 0.8;
% labels = {'First','Second','Third','Fourth','Fifth'};
% colors = {'g','b'};    % will cycle through
% s = graphViz4Matlab('-adjMat',adj,'-nodeLabels',labels,'-nodeColors',colors);
% freeze(s); % convert to an image
%
% If you are only specifying an adjacency matrix, you can omit the
% '-adjMat' name as in graphViz4Matlab(adj).
%
% Calling graphViz4Matlab without any parameters displays an example graph. 
%


    properties(GetAccess = 'public', SetAccess = 'private')
    % read only
       path         = addpath(genpath(fileparts(which(mfilename))));  % automatically adds subdirectories to path
       graphVizPath = setupPath(); 
       nnodes       = 0;      % The number of nodes
       nedges       = 0;      % The number of edges
       currentLayout= [];     % The current layout object
       layouts      = [];     % List currently added layout objects
       adjMatrix    = [];     % The adjacency matrix
       isvisible    = false;  % True iff the graph is being displayed
       nodeArray    = [];     % The nodes
       edgeArray    = [];     % The edges
       fig          = [];     % The main window
       ax           = [];     % The main axes
       doubleClickFn = [];    % function to execute when a user double clicks on a node, (must be a function handle that takes in the node name
       selectedNode = [];     % The selected node, if any   
       minNodeSize  = [];     % A minimum size for the nodes
       maxNodeSize  = [];     % A maximum size for the nodes
       undirected   = false;  % If undirected, arrows are not displayed
       flipped      = false;  % If true, layout is done as though edge directions were reversed. 
                              % (does not affect the logical layout).
       knownLayouts = {Gvizlayout  ,...   % add your own layout here or use
                       Treelayout  ,...   % the addLayout() method
                       Radiallayout,...
                       Circularlayout,...
                       Springlayout,...
                       Circlelayout,...
                       Gridlayout  ,...
                       Randlayout  };
        defaultEdgeColor  = [0,0,0];%[20,43,140]/255;   
        edgeColors;
        square      = true;  % amounts to a the call "axis square"
        splitLabels = true;
    end
     
    properties(GetAccess = 'private', SetAccess = 'private')
    % These values store the initial values not the current ones. 
        nodeLabels          = {};    
        nodeDescriptions    = {};
        nodeColors          = {};
    end
    
    properties(GetAccess = 'protected',SetAccess = 'protected')
        toolbar;                    % The button toolbar
        layoutButtons;              % The layout buttons
        fontSize;                   % last calculated optimal font size
        selectedFontSize;           % 
        
        previousMouseLocation;      % last mouse location relative to the axes
        groupSelectionMode = 0;     % current stage in a group selection task
        groupSelectedNodes;         % selected nodes in a group selection
        groupSelectedDims;          % size of enclosing rectangle of selected nodes 
        groupSelectedRect;          % a bounding rectangle for the selected nodes
    end
 
    methods
        
        function obj = graphViz4Matlab(varargin)
        % graphViz4Matlab constructor
            if(~exist('processArgs','file')), error('Requires processArgs() function');            end
            obj.addKnownLayouts();
            obj.processInputs(varargin{:})
            obj.addNodes();
            obj.addEdges();
            obj.draw();
        end
       
        function draw(obj)          
        % Draw the graph
            if(obj.isvisible)
                obj.erase()
            end
           obj.createWindow();
           obj.calculateMinMaxNodeSize();
           obj.layoutNodes();
           obj.displayGraph();  
           obj.isvisible = true;
           obj.paperCrop();
        end
        
        function fig = freeze(obj)
        % Freeze the current image into a regular Matlab figure    
            figure(obj.fig);
            print tmp.png -dpng -r300
            fig = figure;
            image(imread('tmp.png'));
            axis off;
            delete tmp.png;
            close(obj.fig);
        end
        
        function redraw(obj)
        % Redraw the graph. (You could also call draw() again but then the
        % window is recreated as well and it doesn't look as nice).
            if(~obj.isvisible)
                obj.draw();
                return;
            end
            cla(obj.ax);
            obj.clearGroupSelection();
            obj.createAxes();
            obj.calculateMinMaxNodeSize();
            obj.layoutNodes();
            obj.displayGraph(); 
        end
        
        function flip(obj,varargin)
        % Have the layout algorithms layout the graph as though the arrows 
        % were pointing in the opposite direction. The node connectivity
        % remains the same and if node one pointed to node 2 before, it
        % still does after. This is useful for tree layout, for example to
        % turn the tree on its head. Calling it twice flips it back.
            obj.flipped = ~obj.flipped;
            if(obj.isvisible)
                obj.redraw();
            end
        end
        
        function erase(obj)
        % Erase the graph but maintain the state so that it can be redrawn.
           if(obj.isvisible)
               obj.clearGroupSelection();
               delete(obj.fig);
               obj.isvisible = false;
             
           end
        end
        
        function nodeSelected(obj,node)
        % This function is called by nodes when they are selected by the
        % mouse. It should not be called manually. 
            if(obj.groupSelectionMode == 1)
                obj.groupSelectionStage1();
                return;
            end
            if(~isempty(obj.selectedNode))
                node.deselect();
                obj.selectedNode = [];
                return;
            end
            switch get(obj.fig,'SelectionType')     
                case 'normal' 
                   obj.singleClick(node);
                case 'open'  
                    obj.doubleClick(node);
                case 'alt'
                    obj.rightClick(node);
                otherwise    
                    obj.shiftClick(node);
            end
        end
        
        function addLayout(obj,layout)
        % Let the graph know about a new layout you have created so that it
        % will be available via a toolbar button. The layout object must be
        % a descendant of the Abstractlayout class. This method does not have
        % to be called for existing layouts, nor does it need to be called
        % if you passed the new layout to the constructor or to the
        % setLayout() method. It will not add two layouts with the same
        % name property. 
            if(~ismember(layout.name,fieldnames(obj.layouts)))
                if(layout.isavailable())
                    obj.layouts.(layout.name) = layout;
                    if(obj.isvisible)
                        obj.addButtons();
                    end
                else
                    warning('graphViz4Matlab:layout','This layout is not available');
                end
            end
        end
        
        function setLayout(obj,layout)
        % Set a new layout algorithm and refresh the graph. 
            if(layout.isavailable())
                obj.addLayout(layout);
                obj.currentLayout = obj.layouts.(layout.name);
                obj.redraw();
            else
                warning('graphViz4Matlab:layout','Sorry, this layout is not available');
            end
        end
        
         function squareAxes(obj,varargin)
        % Toggle the axes from square to normal and vice versa.
            obj.clearGroupSelection();
            if(obj.square)
               axis(obj.ax,'normal');
               obj.square = false;
            else
               axis(obj.ax,'square');
               obj.square = true;
            end
            
        end
        
        function tightenAxes(obj,varargin)
         % Tighten the axes as much as possible.
             obj.clearGroupSelection();
             xpos = vertcat(obj.nodeArray.xpos);
             ypos = vertcat(obj.nodeArray.ypos);
             r = obj.nodeArray(1).width/2;
             axis(obj.ax,[min(xpos)-r,max(xpos)+r,min(ypos)-r,max(ypos)+r]);
             axis normal;
        end
        
        
        
        
    end % end of public methods
        
 
    methods(Access = 'protected')
        
        function addKnownLayouts(obj)
        % Add all of the known layouts
            obj.layouts = struct;
            for i=1:numel(obj.knownLayouts)
                layout = obj.knownLayouts{i};
                if(layout.isavailable())
                   obj.layouts.(layout.name) = layout; 
                end
            end
        end
        
        function processInputs(obj,varargin)
        % Process the inputs and perform error checking    
            labels = {'adj', 'adjMatrix', 'adjMat', 'layout', 'nodeLabels', 'nodeDescriptions', 'nodeColors', 'undirected', 'edgeColors', 'splitLabels', 'doubleClickFn'};
            for i=1:numel(varargin)
                arg = varargin{i};
                if ~ischar(arg), continue; end
                for j = 1:numel(labels)
                    if strcmpi(arg, labels{i});
                        varargin{i} = ['-', arg];
                    end
                    if strcmpi(arg, '-adj') || strcmpi(arg, '-adjMatrix')
                        varargin{i} = '-adjMat';
                    end
                end
            end
            
            [adjMatrix, currentLayout, nodeLabels, nodeDescriptions, nodeColors,obj.undirected,obj.edgeColors,obj.splitLabels,obj.doubleClickFn] = processArgs(varargin,... 
                '-adjMat'               , []     ,...
                '-layout'               , []     ,...
                '-nodeLabels'           , {}     ,...
                '-nodeDescriptions'     , {}     ,...
                '-nodeColors'           , {}     ,...    
                '-undirected'           , false  ,...
                '-edgeColors'           , []     ,...
                '-splitLabels'          , true   ,...
                '-doubleClickFn'        , []     ); 
            
            
            if(~isempty(currentLayout) && ~isavailable(currentLayout))
              currentLayout = [];
            end
            if(isempty(adjMatrix))
                adjMatrix = [0 0 0 0; 1 0 0 0; 1 1 0 0; 1 1 1 0]; % example graph
            end
            
            if(isempty(currentLayout))
                fields = fieldnames(obj.layouts);
                currentLayout = obj.layouts.(fields{1});
            else
                obj.addLayout(currentLayout);
            end
            obj.nnodes = size(adjMatrix,1);
            obj.adjMatrix = adjMatrix;
            if(isempty(nodeDescriptions))
                nodeDescriptions = repmat({'Enter a description here...'},size(adjMatrix,1),1);
            end
            obj.nodeDescriptions = nodeDescriptions;
            obj.nodeColors = nodeColors;
                            
            if(isempty(nodeLabels))
                nodeLabels = cellfun(@(x)num2str(x),mat2cell(1:obj.nnodes,1,ones(1,obj.nnodes)),'UniformOutput',false);
            end
          
            obj.nodeLabels = nodeLabels;
            if(~isequal(numel(obj.nodeLabels),size(adjMatrix,1),size(adjMatrix,2)))
                error('graphViz4Matlab:dimMismatch','The number of labels must match the dimensions of adjmatrix.');
            end
             obj.currentLayout = currentLayout;
        end
     
        function createWindow(obj)
        % Create the main window
            obj.fig = figure(floor(1000*rand) + 1000);
            set(obj.fig,'Name','graphViz4Matlab',...
                        'NumberTitle' ,'off',...
                        'Color','w'   ,'Toolbar','none');
            obj.createAxes();
            ssize = get(0,'ScreenSize');
            pos = [ssize(3)/2,50,-20+ssize(3)/2,ssize(4)-200];
            set(obj.fig,'Position',pos);
            obj.setCallbacks();
            obj.addButtons();
            
        end
        
        function createAxes(obj)
        % Create the axes upon which the graph will be displayed.     
            obj.ax = axes('Parent',obj.fig,'box','on','UserData','main');
            outerpos = get(obj.ax,'OuterPosition');
            
            axis manual
            if(obj.square)
                axis square
            end
            set(obj.ax,'Position',outerpos,'XTick',[],'YTick',[],'LineWidth',0.5);
            set(obj.ax,'ButtonDownFcn',@obj.axPressed);
        end
        
        function setCallbacks(obj)
        % Set the callback functions for the figure, i.e. functions that
        % will be called when the user performs various actions. 
            set(obj.fig,'ResizeFcn'             ,@obj.windowResized);
            set(obj.fig,'WindowButtonMotionFcn' ,@obj.mouseMoved);
            set(obj.fig,'WindowButtonUpFcn'     ,@obj.buttonUp);
            set(obj.fig,'DeleteFcn'             ,@obj.deleted);
        end
         
        function addNodes(obj)
        % Add all of the nodes to the graph structure, but don't display
        % them yet. 
            obj.nodeArray = [];
            for i=1:obj.nnodes
                newnode = graphViz4MatlabNode(obj.nodeLabels{i});
                newnode.containingGraph = obj;
                newnode.showFullLabel = ~obj.splitLabels;
                obj.nodeArray = [obj.nodeArray newnode];
            end
            obj.addNodeDescriptions(obj.nodeDescriptions);
            obj.addNodeColors(obj.nodeColors);
        end
        
        function addNodeDescriptions(obj,nodeDescriptions)
        % Add any descriptions to the newly created nodes.     
            if(~isempty(nodeDescriptions))
               if(numel(nodeDescriptions) == 1)
                    nodeDescriptions = repmat(nodeDescriptions,obj.nnodes,1);
               end 
               for i=1:obj.nnodes
                  obj.nodeArray(i).description = nodeDescriptions{i}; 
               end
            end
        end
        
        function addNodeColors(obj,nodeColors)
        % Shade the nodes according to the specified colors. If too few
        % colors are specified, they are cycled through. 
            if(~isempty(nodeColors))
               if(~iscell(nodeColors))
                   nodeColors = mat2cell(nodeColors,ones(1,size(nodeColors,1)),size(nodeColors,2));
               end
               if(size(nodeColors,2) > size(nodeColors,1))
                   nodeColors = nodeColors';
               end
               if(numel(nodeColors) < obj.nnodes)
                   nodeColors = repmat(nodeColors,ceil(obj.nnodes/numel(nodeColors)),1);
                   nodeColors = nodeColors(1:obj.nnodes); 
               end
               for i=1:obj.nnodes
                    obj.nodeArray(i).shade(nodeColors{i}); 
               end
               obj.nodeColors = nodeColors;
            end
        end
        
        function addEdges(obj)
        % Add all of the edges to the graph structure, but don't display
        % them yet. 
            if(any(diag(obj.adjMatrix)))
                fprintf('\nRemoving Self Loops\n');
                obj.adjMatrix = obj.adjMatrix - diag(diag(obj.adjMatrix));
            end   
            obj.edgeArray = struct('from',[],'to',[],'arrow',[]);
            counter = 1;
            for i=1:obj.nnodes
                for j=1:obj.nnodes
                    if(obj.adjMatrix(i,j))
                        obj.edgeArray(counter) = struct('from',obj.nodeArray(i),'to',obj.nodeArray(j),'arrow',-1);
                        obj.nodeArray(i).outedges = [obj.nodeArray(i).outedges,counter];
                        obj.nodeArray(j).inedges =  [obj.nodeArray(j).inedges,counter];
                        counter = counter + 1;
                    end
                end
            end
            obj.nedges = counter -1;
        end
        
        function calculateMinMaxNodeSize(obj)
        % calculates the maximum and minimum node sizes in data units    
            SCREEN_PROPORTION_MAX = 1/10;
            SCREEN_PROPORTION_MIN = 1/35;
            units = get(0,'Units');
            set(0,'Units','pixels');
            screensize = get(0,'ScreenSize');
            set(0,'Units',units);
            axunits = get(obj.ax,'Units');
            set(obj.ax,'Units','pixels');
            axsize = get(obj.ax,'Position');
            set(obj.ax,'Units',axunits);
            if(screensize(3) < screensize(4))
                dataUnitsPerPixel = abs(diff(xlim))/axsize(3);
                obj.minNodeSize = (SCREEN_PROPORTION_MIN*screensize(3))*dataUnitsPerPixel;
                obj.maxNodeSize = (SCREEN_PROPORTION_MAX*screensize(3))*dataUnitsPerPixel;
            else
                dataUnitsPerPixel = abs(diff(ylim))/axsize(4);
                obj.minNodeSize = (SCREEN_PROPORTION_MIN*screensize(4))*dataUnitsPerPixel;
                obj.maxNodeSize = (SCREEN_PROPORTION_MAX*screensize(4))*dataUnitsPerPixel;
            end
        end
      
        function layoutNodes(obj)
        % Layout the nodes and edges according to the current layout
        % algorithm. 
             if(obj.flipped)
                 adj = obj.adjMatrix';
             else
                 adj = obj.adjMatrix;
             end
             obj.currentLayout.dolayout(adj,obj.ax,obj.maxNodeSize);
             nodesize = obj.currentLayout.nodeSize();
             locs = obj.currentLayout.centers();
              for i=1:obj.nnodes
                node = obj.nodeArray(i);
                node.resize(nodesize);
                node.move(locs(i,1),locs(i,2));
             end
        end
        
        function displayGraph(obj)
        % Display all of the nodes and edges. 
            cla(obj.ax);
            obj.setFontSize();
            for i=1:obj.nnodes
               node = obj.nodeArray(i);
               node.fontSize = obj.fontSize;
               node.draw(obj.ax);
            end
            displayEdges(obj);
        end
        
        function displayEdges(obj,indices)
        % Display or refresh the specified edges. If none specified, all 
        % are refreshed. Currently only works with round nodes.
            figure(obj.fig);
            if(nargin < 2)
                indices = 1:obj.nedges;
            else
                indices = unique(indices);
            end
            for i=1:numel(indices)
               edge = obj.edgeArray(indices(i));
               [X,Y,Xarrow,Yarrow] = obj.calcPositions(edge);
               if(ishandle(edge.arrow))
                   delete(edge.arrow)
               end
               hold on;
               edgeColor = obj.defaultEdgeColor;
               if ~isempty(obj.edgeColors)
                  candidates = obj.edgeColors(findString(edge.from.label,obj.edgeColors(:,1)),:);
                  if size(candidates,1)==1 && strcmpi(candidates(1,2),'all')
                      edgeColor = candidates{1,3};
                  else
                    edgeCol = candidates(findString(edge.to.label,candidates(:,2)),3);
                    if ~isempty(edgeCol); edgeColor = edgeCol{1}; end
                  end
               end
               edge.arrow = plot(X,Y,'LineWidth',2,'HitTest','off','Color',edgeColor);
               if(~obj.undirected)
                  arrowHead = obj.displayArrowHead(X,Y,Xarrow,Yarrow,edgeColor); 
                  edge.arrow = [edge.arrow arrowHead];
               end
               hold off;
               obj.edgeArray(indices(i)) = edge;
            end
        end
        
        function arrowHead = displayArrowHead(obj,X,Y,Xarrow,Yarrow,arrowColor)   %#ok
        % Displays the arrow head given the appropriate coordinates
        % calculated via the calcPositions() function. 
            
            arrowHead = patch('Faces'      ,[1,2,3]                                             ,...
                              'Vertices'  ,[Xarrow(1) Yarrow(1); Xarrow(2) Yarrow(2) ;X(2) Y(2)],...
                              'FaceColor' ,arrowColor);
        end
        
        function [X,Y,Xarrow,Yarrow] = calcPositions(obj,edge)
        % Helper function for displayEdges() - calculates edge and arrow
        % start and end positions in data units.
            X = [edge.from.xpos edge.to.xpos];
            Y = [edge.from.ypos edge.to.ypos];
            ratio = (Y(2) - Y(1))/(X(2)-X(1));
            if(isinf(ratio))
                ratio = realmax;
            end
            % dx:  x-distance from node1 center to perimeter in direction of node2
            % dy:  y-distance from node1 center to perimeter in direction of node2
            % ddx: x-distance from node1 perimeter to base of arrow head
            % ddy: y-distance from node1 perimeter to base of arrow head
            % dpx: x-offset away from edge in perpendicular direction, for arrow head
            % dpy: y-offset away from edge in perpendicular direction, for arrow head
            
            arrowSize = obj.maxNodeSize/10;            
            [dx,dy] = pol2cart(atan(ratio),edge.from.width/2);
            [ddx,ddy] = pol2cart(atan(ratio),arrowSize);
            ratio = 1/ratio; % now work out perpendicular directions. 
            if(isinf(ratio))
                ratio = realmax;
            end
            [dpx dpy] = pol2cart(atan(ratio),arrowSize/2);
            ddx = abs(ddx); ddy = abs(ddy); dpx = abs(dpx); dpy = abs(dpy);
            dx = abs(dx); dy = abs(dy);
            if(X(1) < X(2))
                X(1) = X(1) + dx; X(2) = X(2) - dx;
            else
                X(1) = X(1) - dx; X(2) = X(2) + dx;
            end
            if(Y(1) < Y(2))
                Y(1) = Y(1) + dy; Y(2) = Y(2) - dy;
            else
                Y(1) = Y(1) - dy; Y(2) = Y(2) + dy;
            end
            if(X(1) <= X(2) && Y(1) <= Y(2))
                Xarrow(1) = X(2) - ddx - dpx; Xarrow(2) = X(2) - ddx + dpx;
                Yarrow(1) = Y(2) - ddy + dpy; Yarrow(2) = Y(2) - ddy - dpy;
            elseif(X(1) <= X(2) && Y(1) >= Y(2))
                Xarrow(1) = X(2) - ddx - dpx; Xarrow(2) = X(2) - ddx + dpx;
                Yarrow(1) = Y(2) + ddy - dpy; Yarrow(2) = Y(2) + ddy + dpy;
            elseif(X(1) >= X(2) && Y(1) <= Y(2))
                Xarrow(1) = X(2) + ddx - dpx; Xarrow(2) = X(2) + ddx + dpx;
                Yarrow(1) = Y(2) - ddy - dpy; Yarrow(2) = Y(2) - ddy + dpy;
            else % (X(1) >= (X(2) && Y(1) >= Y(2))
                Xarrow(1) = X(2) + ddx - dpx; Xarrow(2) = X(2) + ddx + dpx;
                Yarrow(1) = Y(2) + ddy + dpy; Yarrow(2) = Y(2) + ddy - dpy;
            end
        end

         function addButtons(obj)
         % Add user interface buttons.
             if(~isempty(obj.toolbar))
                 if(ishandle(obj.toolbar))
                    delete(obj.toolbar);
                    obj.toolbar = [];
                 end
             end
             obj.toolbar = uitoolbar(obj.fig);
               
             % button icons
             load glicons;
            
             uipushtool(obj.toolbar,...
                  'ClickedCallback'   ,@obj.decreaseFontSize,...
                  'TooltipString'     ,'Decrease Font Size',...
                  'CData'             ,icons.downblue);
             
             uipushtool(obj.toolbar,...
                  'ClickedCallback'   ,@obj.increaseFontSize,...
                  'TooltipString'     ,'Increase Font Size',...
                  'CData'             ,icons.upblue);
              
              uipushtool(obj.toolbar,...
                  'ClickedCallback'   ,@obj.tightenAxes,...
                  'TooltipString'     ,'Tighten Axes',...
                  'CData'             ,icons.expand);
             
              uipushtool(obj.toolbar,...
                    'ClickedCallback' ,@obj.flip,...
                    'TooltipString'   ,'Flip/Reset Layout',...
                    'CData'           , icons.flip);
           
             uipushtool(obj.toolbar,...
                    'ClickedCallback' ,@obj.shrinkNodes,...
                    'TooltipString'   ,'Decrease Node Size',...
                    'CData'           , icons.downdarkblue);

             uipushtool(obj.toolbar,...
                    'ClickedCallback' ,@obj.growNodes,...
                    'TooltipString'   ,'Increase Node Size',...
                    'CData'           , icons.updarkblue);
                       
             if(~isempty(obj.layoutButtons))
                 for i=1:numel(obj.layoutButtons)
                     if(ishandle(obj.layoutButtons(i)))
                         delete(obj.layoutButtons(i));
                     end
                 end
                 obj.layoutButtons = [];
             end
             
             layoutNames = fieldnames(obj.layouts);
             for i=1:numel(layoutNames)
                layout = obj.layouts.(layoutNames{i});
                layoutButton = uipushtool(obj.toolbar,...
                    'ClickedCallback', @obj.layoutButtonPushed,...
                    'TooltipString', layout.shortDescription,...
                    'UserData'     , layoutNames{i},...
                    'Separator'    , 'on',...
                    'CData'        , layout.image);
                 obj.layoutButtons = [obj.layoutButtons,layoutButton];
             end
         end
         
         function setFontSize(obj)
         % fontsize = obj.maxFontSize;
           fontSize = 20;
           maxchars = size(char(obj.nodeLabels),2);
           width = obj.nodeArray(1).width;
           height = obj.nodeArray(1).height;
           xpos = -10; ypos = -10;
           t = text(xpos,ypos,repmat('g',1,maxchars),...
                'FontUnits'           , 'points'    ,...
                'Units'               , 'data'      ,...
                'HorizontalAlignment' , 'center'    ,...
                'VerticalAlignment'   , 'middle'    ,...
                'FontWeight'          , 'demi'      ,...
                'LineStyle'           , 'none'      ,...
                'Margin'              , 0.01        ,...
                'FontSize'            , fontSize    ,...
                'Color'               , 'w'         );
            
           extent = get(t,'Extent');
 
           while(extent(3) > width || extent(4) > height)
                fontSize = fontSize - 1;
                if(fontSize < 2), break,end
                set(t,'FontSize',fontSize);
                extent = get(t,'Extent');
           end    
           obj.fontSize = fontSize;
             
         end
         
         function asp = aspectRatio(obj)
         % Return the current aspect ratio of the figure, width/height
            
            units = get(obj.ax,'Units');
            set(obj.ax,'Units','pixels');
            pos = get(obj.ax,'Position');
            set(obj.ax,'Units',units);
            asp = (pos(3)/pos(4));
             
         end
         
         function paperCrop(obj)
         % Make the papersize the same as the the figure size. This is
         % useful when saving as pdf. 
           units = get(obj.fig,'Units');
           set(obj.fig,'Units','inches');
           pos = get(obj.fig,'Position');
           set(obj.fig,'Units',units);
           set(obj.fig,'PaperPositionMode','auto','PaperSize',pos(3:4)); 
         end
%%     
% Callbacks
       
       function layoutButtonPushed(obj,buttonPushed,varargin)
       % Called when a layout button is pushed.
            name = get(buttonPushed,'UserData');
            obj.currentLayout = obj.layouts.(name);
            axis square;
            obj.redraw;
       end

        function windowResized(obj,varargin)
        % This function is called whenever the window is resized. It
        % redraws the whole graph. 
            if(obj.isvisible)
                  obj.redraw;
                  obj.paperCrop();
            end
           
        end
        
        function mouseMoved(obj,varargin)
        % This function is called whenever the mouse moves within the
        % figure. 
           if(obj.groupSelectionMode == 2)
               % Move all of the nodes & rectangle
               currentPoint = get(obj.ax,'CurrentPoint');
               xlimits = get(obj.ax,'XLim');
               ylimits = get(obj.ax,'YLim');
               sdims = obj.groupSelectedDims;
               xdiff = currentPoint(1,1) - obj.previousMouseLocation(1,1);
               ydiff = currentPoint(1,2) - obj.previousMouseLocation(1,2);

                if(xdiff <=0)
                    xdiff = max(xdiff,(xlimits(1)-sdims(1)));
                else
                    xdiff = min(xdiff,xlimits(2)-sdims(2)); 
                end
                if(ydiff <=0)
                    ydiff = max(ydiff,(ylimits(1)-sdims(3)));
                else
                    ydiff = min(ydiff,ylimits(2)-sdims(4));
                end
               xnodepos = vertcat(obj.groupSelectedNodes.xpos) + xdiff;
               ynodepos = vertcat(obj.groupSelectedNodes.ypos) + ydiff;
               for i=1:numel(obj.groupSelectedNodes)
                  obj.groupSelectedNodes(i).move(xnodepos(i),ynodepos(i)); 
               end
               recpos = get(obj.groupSelectedRect,'Position');
               recpos(1) = recpos(1) + xdiff;
               recpos(2) = recpos(2) + ydiff;
               obj.groupSelectedDims = [recpos(1),recpos(1)+recpos(3),recpos(2),recpos(2)+recpos(4)];
               set(obj.groupSelectedRect,'Position',recpos);
               edges = [obj.groupSelectedNodes.inedges,obj.groupSelectedNodes.outedges];
               obj.displayEdges(edges);
               obj.previousMouseLocation = currentPoint;
           else
                if(isempty(obj.selectedNode)), return,end
                currentPoint = get(obj.ax,'CurrentPoint');
                x = currentPoint(1,1); y = currentPoint(1,2);
                xl = xlim + [obj.selectedNode.width,-obj.selectedNode.width]/2;
                yl = ylim + [obj.selectedNode.height,-obj.selectedNode.height]/2;
                x = min(max(xl(1),x),xl(2));
                y = min(max(yl(1),y),yl(2));
                obj.selectedNode.move(x,y);    
                obj.displayEdges([obj.selectedNode.inedges,obj.selectedNode.outedges]); 
           end
        end
        
        function buttonUp(obj,varargin)
        % This function executes when the mouse button is released. 
            if(obj.groupSelectionMode == 2)
               obj.clearGroupSelection();
               return;
            end
            if(isempty(obj.selectedNode)),return,end
             obj.selectedNode.deselect();
             
             obj.selectedNode.useFullLabel = false;
             obj.selectedNode.fontSize = obj.selectedFontSize;
             obj.selectedNode.redraw();
             obj.selectedNode = [];
             set(gcf,'Pointer','arrow');
        end
    
         function axPressed(obj,varargin)
         % Called when the user selects the axes but not a node
             switch obj.groupSelectionMode
                 case 0         % hasn't been selected yet
                    xpos = vertcat(obj.nodeArray.xpos);
                    ypos = vertcat(obj.nodeArray.ypos);
                    p1 = get(obj.ax,'CurrentPoint');    
                    rbbox;               % returns after box drawn    
                    p2 = get(obj.ax,'CurrentPoint');    
                    xleft  = min(p1(1,1),p2(1,1));
                    xright = max(p1(1,1),p2(1,1));
                    ylower = min(p1(1,2),p2(1,2));
                    yupper = max(p1(1,2),p2(1,2));
                    selectedX = (xpos <= xright) & (xpos >= xleft);
                    selectedY = (ypos <= yupper) & (ypos >= ylower);
                    selected = selectedX & selectedY;
                    if(~any(selected)),return,end
                    obj.groupSelectionMode = 1;    
                    obj.groupSelectedNodes = obj.nodeArray(selected);
                    for i=1:numel(obj.groupSelectedNodes)
                       node = obj.groupSelectedNodes(i);
                       node.select(); 
                       node.redraw();
                    end
                    
                    w = obj.groupSelectedNodes(1).width/2;
                    h = obj.groupSelectedNodes(1).height/2;
                    x = vertcat(obj.groupSelectedNodes.xpos);
                    y = vertcat(obj.groupSelectedNodes.ypos);
                    minx = min(x)-w; maxx = max(x)+w; miny = min(y)-h; maxy = max(y)+h;
                    obj.groupSelectedDims = [minx,maxx,miny,maxy];
                    obj.groupSelectedRect = rectangle('Position',[minx,miny,maxx-minx,maxy-miny],'LineStyle','--','EdgeColor','r');
                 case 1         % nodes selected 
                     obj.groupSelectionStage1();
                 case 2         %not ever reached in this function
                     obj.clearGroupSelection();
             end
         end
         
         function groupSelectionStage1(obj)
         % Called after a group of nodes has been selected and the mouse
         % button has been pressed somewhere on the axes, (or on a node).
            p = get(obj.ax,'CurrentPoint');
            obj.previousMouseLocation = p;
            dims = obj.groupSelectedDims;
                if(p(1,1) >= dims(1) && p(1,1) <= dims(2) && p(1,2) >= dims(3) && p(1,2) <=dims(4))
                    set(gcf,'Pointer','hand');
                    obj.groupSelectionMode = 2;
                else
                    obj.clearGroupSelection();
                end
         end
        
         function clearGroupSelection(obj)
         % Clear a group selection
            if(ishandle(obj.groupSelectedRect))
                delete(obj.groupSelectedRect);
            end
            obj.groupSelectedRect = [];
            for i=1:numel(obj.groupSelectedNodes)
               obj.groupSelectedNodes(i).deselect(); 
            end
           obj.groupSelectedNodes = [];
           obj.groupSelectedDims = [];
           obj.groupSelectionMode = 0;
           set(gcf,'Pointer','arrow');
         end
  
        function deleted(obj,varargin)
        % Called when the figure is deleted by the user. 
           obj.isvisible = false; 
           obj.clearGroupSelection();
        end
        
        function singleClick(obj,node)
        % Called when a user single clicks on a node. 
            obj.selectedNode = node;
            node.select();
            set(gcf,'Pointer','hand');
            obj.selectedFontSize = node.fontSize;
            node.useFullLabel = true;
            node.fontSize = max(15,node.fontSize*1.5);
            node.redraw();
        end
        
        function doubleClick(obj,node)                
        % Called when a user double clicks on a node
            if isempty(obj.doubleClickFn)
            description = node.description;
            if(~iscell(description))
                description = {description};
            end
            answer = inputdlg('',node.label,4,description);
            if(~isempty(answer))
                node.description = answer;
            end
            else
               obj.doubleClickFn(node.label); 
            end
        end
        
        function rightClick(obj,node)                 %#ok
        % Called when a user right clicks on a node    
            if(node.isshaded)
                node.unshade();
            else
                node.shade();
            end
        end
        
        function shiftClick(obj,node)                 %#ok
        % Called when a user shift clicks on a node    
            display(node);
        end
        
       
    end
       
    methods
    % Callbacks that can be called by the user programmatically.    
        function shrinkNodes(obj,varargin)
        % Shrink the nodes to 95% of their original size, (but not smaller 
        % than a calculated minimum.
           obj.clearGroupSelection();
            s = max(0.8*obj.nodeArray(1).width,obj.minNodeSize);
            obj.nodeArray(1).resize(s);
            obj.setFontSize();
            for i=1:obj.nnodes
                node = obj.nodeArray(i);
                node.fontSize = obj.fontSize;
                node.resize(s);
            end
            obj.displayEdges();
        end
        
        function growNodes(obj,varargin)
        % Grow the nodes to 1/0.95 times their original size, (but not 
        % larger than a calculated maximum. 
            obj.clearGroupSelection();
            s = min(obj.nodeArray(1).width/0.8,1.5*obj.maxNodeSize);
            obj.nodeArray(1).resize(s);
            obj.setFontSize();
            for i=1:obj.nnodes
                node = obj.nodeArray(i);
                node.fontSize = obj.fontSize;
                node.resize(s);
            end
            obj.displayEdges();
        end
        
        function increaseFontSize(obj,varargin)
        % Increase the fontsize of all the nodes by 0.5 points.
           current = get(obj.nodeArray(1).labelhandle,'FontSize');
           newsize = current + 1;
           for i=1:numel(obj.nodeArray)
              node = obj.nodeArray(i);
              node.fontSize = newsize;
              node.redraw();
           end
        end
        
         function decreaseFontSize(obj,varargin)
        % Decrease the fontsize of all the nodes by 0.5 points.
           current = get(obj.nodeArray(1).labelhandle,'FontSize');
           newsize = max(current - 1,1);
           for i=1:numel(obj.nodeArray)
              node = obj.nodeArray(i);
              node.fontSize = newsize;
              node.redraw();
           end
        end
        
    end
   
end
