%-----------------
% Florian Mueller
% December 2014
%-----------------

% see report.pdf, section 3.1

classdef LayoutData < Data

    properties (Constant)
        indexFields = {'sSpp_e','sRtn_e','nPl'};
    end
    
    properties
        c;
    end
    
    methods
        function ld = LayoutData()
        end
        
        function ld = setNewYork(ld)
            ld.c.N      = int64(20);
            ld.c.E      = int64(21);
            ld.c.sSpp_e = int64([  1,  2;
                                   2,  3;
                                   3,  4;
                                   4,  5;
                                   5,  6;
                                   6,  7;
                                   7,  8;
                                   8,  9;
                                   9,  10;
                                   11, 9; 
                                   12, 11;
                                   13, 12;
                                   14, 13;
                                   15, 14;
                                   1,  15;
                                   10, 17;
                                   12, 18;
                                   18, 19;
                                   11, 20;
                                   20, 16;
                                   9,  16]);
            ld.c.sRtn_e = fliplr(ld.c.sSpp_e);
            ld.c.nPl    = int64(1);
        end
    end
    
end

