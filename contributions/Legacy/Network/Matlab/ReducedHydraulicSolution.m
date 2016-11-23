%-----------------
% Florian Mueller
% December 2014
%-----------------

classdef ReducedHydraulicSolution < Solution

    properties (Constant)
        indexFields={};
    end
    
    properties
        c;
    end
    
    methods
        function rhs = ReducedHydraulicSolution()
        end
        
        function rhs = set(rhs,x,fval,exitflag,ld)
            rhs.c.x        = x;
            rhs.c.fval     = fval;
            rhs.c.exitflag = exitflag;
            % reduced hydraulic variables (see report.pdf, section 5.2)
            rhs.c.vDot_e = x(1:ld.c.E);
            rhs.c.p_n    = x(ld.c.E+1:ld.c.E+ld.c.N);
        end
    end
    
end

