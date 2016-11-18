%-----------------
% Florian Mueller
% December 2014
%-----------------

classdef Data
    
    properties (Abstract,Constant)
        indexFields;
    end
    
    properties (Abstract)
        c;
    end
    
    methods
        function d = Data()
            d.c.zeroBasedIndexing = false;
        end
        
        function d = setFromMat(d,matPath)
            d.c = load(matPath);
            if d.c.zeroBasedIndexing
                for field = d.indexFields
                    d.c.(field{1}) = d.c.(field{1})+int64(1);
                end
                d.c.zeroBasedIndexing = false;
            end
        end
        
        function d = writeToMat(d,matPath)
            c = d.c;
            save(matPath,'-struct','c');
        end
        
        % for testing only
        function difference(d,d_)
            for field = fields(d.c)'
               disp(['d.c.',field{1},'-','d_.c.',field{1},'=']);
               disp(d.c.(field{1})-d_.c.(field{1}));
            end
        end
    end
    
end

