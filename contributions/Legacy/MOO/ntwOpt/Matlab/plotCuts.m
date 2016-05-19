%-----------------
% Florian Mueller
% December 2014
%-----------------

function plotCuts(hd,i,figDir,figName)
    set(0,'defaulttextinterpreter','none');
    
    h = figure();
    for k=1:hd.c.K
        plot([hd.c.vDotMin_i(i),hd.c.vDotMax_i(i)],[hd.c.a_k_i(k,i)*hd.c.vDotMin_i(i)+hd.c.b_k_i(k,i),hd.c.a_k_i(k,i)*hd.c.vDotMax_i(i)+hd.c.b_k_i(k,i)],...
            'LineStyle','--','color', [0.5 0.5 0.5]); hold on;
    end
    
    KK = 10*hd.c.K;
    vDot_kk = linspace(hd.c.vDotMin_i(i),hd.c.vDotMax_i(i),KK)';
    phi_kk = zeros(KK,1);
    for kk=1:KK
        phi1       = (0.25./hd.c.d_i(i).*hd.c.rho./2);
        phi2       = (1./log(10).*log(hd.c.r_i(i)./(3.7.*hd.c.d_i(i))+5.74.*(4.*vDot_kk(kk)./(hd.c.d_i(i).*pi.*hd.c.nu)).^(-0.9))).^(-2);
        phi3       = (4.*vDot_kk(kk)./(hd.c.d_i(i).^2.*pi)).^2;
        phi        = (phi1.*phi2.*phi3);
        phi_kk(kk) = phi;
    end
    plot(vDot_kk,phi_kk,'k');
    grid on;
    xlabel('$\dot{m}$');
    ylabel('$\frac{\Delta p}{L}$');
    addpath('Aux/laprint');
    %storeSinglePlotLaprint(h,figDir,figName,16,[],[]);
    rmpath('Aux/laprint');
end