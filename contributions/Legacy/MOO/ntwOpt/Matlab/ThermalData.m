%-----------------
% Florian Mueller
% December 2014
%-----------------

% see report.pdf, section 6.1

classdef ThermalData < Data

    properties (Constant)
        indexFields = {};
    end
    
    properties
        c;
    end
    
    methods
        function td = ThermalData()
        end

        function td = setNewYork(td,ld,hd,rhd,rhs)
            td.c.cp      = 4185.5;
            td.c.etaHeat = 0.8;
            td.c.cHeat   = 1e-3*0.25*24*365;
            td.c.TRq_n   = 80*ones(ld.c.N,1);
            td.c.dT_n    = 20*ones(ld.c.N,1);

            h_i           = 13.9*pi*hd.c.d_i;
            td.c.h_e      = h_i(rhd.c.i_e);

            td.c.vDot_e = rhs.c.vDot_e;
        end
     end

end