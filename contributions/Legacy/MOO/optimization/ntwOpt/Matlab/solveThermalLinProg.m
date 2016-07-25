%-----------------
% Florian Mueller
% December 2014
%-----------------

function ts = solveThermalLinProg(ld,hd,td,ts)
    % thermal variables (see report.pdf, section 6.2)
    % x = [TSpp_n;TRtn_n];
    
    % lower and upper bounds (see report.pdf, expr 17)
    lb = [td.c.TRq_n        ;-Inf*ones(ld.c.N,1)];
    ub = [Inf*ones(ld.c.N,1); Inf*ones(ld.c.N,1)];
    
    % help 
    H    = zeros(ld.c.N,ld.c.N);
    for e=1:ld.c.E
        i      = ld.c.sSpp_e(e,1);
        j      = ld.c.sSpp_e(e,2);
        H(i,i) = H(i,i) - td.c.vDot_e(e);
        H(j,i) = H(j,i) + td.c.vDot_e(e)*exp(-td.c.h_e(e)*hd.c.L_e(e)/(td.c.cp*hd.c.rho*td.c.vDot_e(e)));
    end
    H = H + diag(hd.c.vDotRq_n);
    
    % equality constraints (see report.pdf, expr 18)
    Aeq1           = zeros(ld.c.N,2*ld.c.N);
    Aeq1(:,1:ld.c.N) = H;
    beq1           = zeros(ld.c.N,1);
    Aeq1           = Aeq1(1:ld.c.N~=ld.c.nPl,:);
    beq1           = beq1(1:ld.c.N~=ld.c.nPl);
    
    % help 
    H    = zeros(ld.c.N,ld.c.N);
    for e=1:ld.c.E
        i      = ld.c.sRtn_e(e,1);
        j      = ld.c.sRtn_e(e,2);
        H(i,i) = H(i,i) - td.c.vDot_e(e);
        H(j,i) = H(j,i) + td.c.vDot_e(e)*exp(-td.c.h_e(e)*hd.c.L_e(e)/(td.c.cp*hd.c.rho*td.c.vDot_e(e)));
    end
    H(ld.c.nPl,ld.c.nPl) = H(ld.c.nPl,ld.c.nPl)-hd.c.vDotPl;
    
    % equality constraints (see report.pdf, expr 19,20)
    Aeq2 = zeros(ld.c.N,2*ld.c.N);
    Aeq2(:,ld.c.N+1:2*ld.c.N) = H;
    hd.c.vDotRq_n(ld.c.nPl) = 0;
    Aeq2(:,1:ld.c.N) = -diag(hd.c.vDotRq_n);
    beq2 = -td.c.dT_n.*hd.c.vDotRq_n;
    
    % objective (see report.pdf, expr 16)
    f = zeros(2*ld.c.N,1);
    f(ld.c.nPl,1) = hd.c.rho*hd.c.vDotPl*td.c.cHeat/td.c.etaHeat;

    % assemble
    Aeq = [Aeq1;Aeq2];
    beq = [beq1;beq2];
    
    % solve the linear program
    options = optimoptions('linprog');
    options.Display = 'iter';
    [x,fval,exitflag,output] = linprog(f,[],[],Aeq,beq,lb,ub,[],options);
    disp(output);
    ts = set(ts,x,fval,exitflag,ld);
    check(ts,[],lb,ub,[],[],Aeq,beq);
end