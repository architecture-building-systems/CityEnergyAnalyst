%-----------------
% Florian Mueller
% December 2014
%-----------------

classdef Solution < Data

    properties (Abstract,Constant)
        indexFields;
    end
    
    properties (Abstract)
        c;
    end
    
    methods
        function s = Solution()
        end
        
        function check(s,intcon,lb,ub,A,b,Aeq,beq)
            if ~isempty(intcon)
                disp('max(max(abs(x(intcon)-round(x(intcon))))) = ');
                disp(max(max(abs(s.c.x(intcon)-round(s.c.x(intcon))))));
            end
            if ~isempty(lb)
                disp('max(max(-x+lb)) = ');
                disp(max(max(-s.c.x+lb)));
            end
            if ~isempty(ub)
                disp('max(max(x-ub)) = ');
                disp(max(max(s.c.x-ub)));
            end
            if ~isempty(A)
                disp('max(max(A*x-b)) = ');
                disp(max(max(A*s.c.x-b)));
            end
            if ~isempty(Aeq)
                disp('max(max(abs(Aeq*x-beq))) = ');
                disp(max(max(abs(Aeq*s.c.x-beq))));
            end
        end
    end
    
end

