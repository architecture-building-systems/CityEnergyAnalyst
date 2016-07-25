%-----------------
% Florian Mueller
% December 2014
%-----------------

classdef ThermalSolution < Solution

    properties (Constant)
        indexFields={};
    end
    
    properties
        c;
    end
    
    methods
        function ts = ThermalSolution()
        end
        
        function ts = set(ts,x,fval,exitflag,ld)
            ts.c.x        = x;
            ts.c.fval     = fval;
            ts.c.exitflag = exitflag;
            % thermal variables (see report.pdf, section 6.2)
            ts.c.TSpp_n   = x(1:ld.c.N);
            ts.c.TRtn_n   = x(ld.c.N+1:2*ld.c.N);
        end
    end
    
end

