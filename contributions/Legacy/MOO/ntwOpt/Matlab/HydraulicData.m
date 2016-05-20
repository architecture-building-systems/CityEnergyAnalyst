%-----------------
% Florian Mueller
% December 2014
%-----------------

% see report.pdf, section 4.1

classdef HydraulicData < Data

    properties (Constant)
        indexFields = {};
    end
    
    properties
        c;
    end
        
    methods
        function hd = HydraulicData()
        end

        function hd = setNewYork(hd,ld)
            hd.c.rho         = 1000;
            hd.c.nu          = 1e-6;
            hd.c.etaPump     = 0.8;
            hd.c.cPump       = 1e-3*0.25*24*365; 
            hd.c.pRq_n       = zeros(ld.c.N,1);

            hd.c.vDotRq_n    = -[0; 2.61647694; 2.61647694; 2.49754617; 2.49754617; 2.49754617; 2.49754617; 2.49754617; 4.81386450; 0.02831685; 4.81386450; 3.31590314; 3.31590314; 2.61647694; 2.61647694; 4.81386450; 1.62821888; 3.31590314; 3.31590314; 4.81386450];
            hd.c.vDotRq_n    = hd.c.vDotRq_n/1000;
            hd.c.vDotPl      = -sum(hd.c.vDotRq_n(1:ld.c.N~=ld.c.nPl));

            hd.c.L_e         = [3535.69; 6035.06; 2225.05; 2529.85; 2621.29; 5821.70; 2926.09; 3810.01; 2926.09; 3413.77; 4419.61; 3718.57; 7345.70; 6431.30; 4724.42; 8046.75; 9509.79; 7315.22; 4389.13; 11704.36; 8046.75];
            hd.c.L_e         = hd.c.L_e;
            
            hd.c.I           = int64(15);
            hd.c.d_i         = [0.02  ,0.025 ,0.032 ,0.040 ,0.050 ,0.065 ,0.08  ,0.1   ,0.125 ,0.15  ,0.2   ,0.25  ,0.3   ,0.35   ,0.4  ]';
            hd.c.c_i         = [73    ,80    ,92    ,127   ,165   ,254   ,370   ,567   ,882   ,1250  ,1500  ,2500  ,3000  ,3500   ,4000 ]'./60;
            hd.c.r_i         = [0.0018,0.0018,0.0018,0.0018,0.0018,0.0018,0.0018,0.0018,0.0018,0.0018,0.0048,0.0048,0.0048,0.0048,0.0048]';
            o_i              = [26.9  ,33.7  ,43.4  ,48.4  , 60.3 ,76.1  ,88.9  ,114.3 ,139.7 ,168.3 ,219.1 ,273   ,323.9 ,355.6  ,406.4]';
            w_i              = [2.6   ,2.6   ,2.6   ,2.6   ,2.9   ,2.9   ,3.2   ,3.6   ,4.6   ,4     ,4.5   ,5     ,5.6   ,5.6    ,6.3  ]';
            vMin_i           = 0.3*ones(hd.c.I,1);
            vMax_i           = 0.4066*(o_i-w_i).^0.412;
            hd.c.vDotMin_i   = vMin_i.*hd.c.d_i.^2./4*pi;
            hd.c.vDotMax_i   = vMax_i.*hd.c.d_i.^2./4*pi;

            hd.c.K           = int64(10);
            vDotLin_k_i = zeros(hd.c.K,hd.c.I);
            for i=1:hd.c.I
                vDotLin_k_i(:,i) = linspace(hd.c.vDotMin_i(i),hd.c.vDotMax_i(i),hd.c.K)';
            end
            hd.c.a_k_i       = zeros(hd.c.K,hd.c.I);
            hd.c.b_k_i       = zeros(hd.c.K,hd.c.I);
            for i=1:hd.c.I
                for k=1:hd.c.K
                    phi1      = (0.25./hd.c.d_i(i).*hd.c.rho./2);
                    phi2      = (1./log(10).*log(hd.c.r_i(i)./(3.7.*hd.c.d_i(i))+5.74.*(4.*vDotLin_k_i(k,i)./(hd.c.d_i(i).*pi.*hd.c.nu)).^(-0.9))).^(-2);
                    phi3      = (4.*vDotLin_k_i(k,i)./(hd.c.d_i(i).^2.*pi)).^2;
                    phi       = (phi1.*phi2.*phi3);
                    dphi2     = (-2.*(1./log(10).*log(hd.c.r_i(i)./(3.7.*hd.c.d_i(i))+5.74.*(4.*vDotLin_k_i(k,i)./(hd.c.d_i(i).*pi.*hd.c.nu)).^(-0.9))).^(-3).*1./log(10).*1./(hd.c.r_i(i)./(3.7.*hd.c.d_i(i))+5.74.*(4.*vDotLin_k_i(k,i)./(hd.c.d_i(i).*pi.*hd.c.nu)).^(-0.9)).*(-0.9).*5.74.*(4.*vDotLin_k_i(k,i)./(hd.c.d_i(i).*pi.*hd.c.nu)).^(-1.9).*4./(hd.c.d_i(i).*pi.*hd.c.nu));
                    dphi3     = (2.*(16.*vDotLin_k_i(k,i)./(hd.c.d_i(i).^4.*pi.^2)));
                    dphi      = (phi1.*(dphi2.*phi3+phi2.*dphi3));
                    hd.c.a_k_i(k,i) = dphi;
                    hd.c.b_k_i(k,i) = phi-hd.c.a_k_i(k,i).*vDotLin_k_i(k,i);
                end
            end
        end
    end
    
end