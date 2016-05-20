%-----------------
% Florian Mueller
% December 2014
%-----------------

% see report.pdf, section 5.1

classdef ReducedHydraulicData < Data

    properties (Constant)
        indexFields = {'i_e'};
    end
    
    properties
        c;
    end
    
    methods
        function rhd = ReducedHydraulicData()
        end

        function rhd = setNewYork(rhd,ld,hd,hs)
            rhd.c.i_e = int64(zeros(ld.c.E,1));
            for e=1:ld.c.E
                rhd.c.i_e(e) = int64(find(round(hs.c.x_i_e(:,e))));
            end

            rhd.c.vDotMin_e = hd.c.vDotMin_i(rhd.c.i_e);
            rhd.c.vDotMax_e = hd.c.vDotMax_i(rhd.c.i_e);

            rhd.c.a_k_e = hd.c.a_k_i(:,rhd.c.i_e);
            rhd.c.b_k_e = hd.c.b_k_i(:,rhd.c.i_e);
        end
    end
    
end