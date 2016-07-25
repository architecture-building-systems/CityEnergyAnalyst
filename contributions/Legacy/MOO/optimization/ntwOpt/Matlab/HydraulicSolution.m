%-----------------
% Florian Mueller
% December 2014
%-----------------

classdef HydraulicSolution < Solution

    properties (Constant)
        indexFields={};
    end
    
    properties
        c;
    end
    
    methods
        function hs = HydraulicSolution()
        end
        
        function hs = set(hs,x,fval,exitflag,ld,hd)
            hs.c.x        = x;
            hs.c.fval     = fval;
            hs.c.exitflag = exitflag;
            % hydraulic variables (see report.pdf, section 4.2)
            hs.c.x_i_e    = reshape(x(1:hd.c.I*ld.c.E),[hd.c.I,ld.c.E]);
            hs.c.vDot_i_e = reshape(x(hd.c.I*ld.c.E+1:2*hd.c.I*ld.c.E),[hd.c.I,ld.c.E]);
            hs.c.p_n      = x(2*hd.c.I*ld.c.E+1:2*hd.c.I*ld.c.E+ld.c.N);
        end
    end
    
end

