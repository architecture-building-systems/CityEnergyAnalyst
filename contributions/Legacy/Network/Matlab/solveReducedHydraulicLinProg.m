%-----------------
% Florian Mueller
% December 2014
%-----------------

function rhs = solveReducedHydraulicLinProg(ld,hd,rhd,rhs)
    % reduced hydraulic variables (see report.pdf, section 5.2)
    % x = [vDot_e;p_n];

    % lower and upper bounds (see report.pdf, expr 11,12,13)
    lb = [rhd.c.vDotMin_e;        hd.c.pRq_n];
    ub = [rhd.c.vDotMax_e;Inf*ones(ld.c.N,1)];
    
    % help
    H = zeros(ld.c.E,ld.c.N);
    for e=1:ld.c.E
        H(e,ld.c.sSpp_e(e,:)) = [-1,1];
    end

    % inequality constraints (see report.pdf, expr 14)
    A = zeros(hd.c.K*ld.c.E,ld.c.E+ld.c.N);
    b = -reshape(rhd.c.b_k_e,[hd.c.K*ld.c.E,1]);
    A(:,1:ld.c.E) = sparse(double(1:hd.c.K*ld.c.E),kron(double(1:ld.c.E),ones(1,hd.c.K)),double(reshape(rhd.c.a_k_e,[hd.c.K*ld.c.E,1])));
    A(:,ld.c.E+1:ld.c.E+ld.c.N) = kron(diag(1./hd.c.L_e)*H,ones(hd.c.K,1));

    % equality constraints (see report.pdf, expr 15)
    Aeq = zeros(ld.c.N,ld.c.E+ld.c.N);
    beq = -hd.c.vDotRq_n;
    Aeq(:,1:ld.c.E) = H';
    Aeq = Aeq(1:ld.c.N~=ld.c.nPl,:);
    beq = beq(1:ld.c.N~=ld.c.nPl);

    % objective (see report.pdf, expr 10)
    f = zeros(ld.c.E+ld.c.N,1);
    f(ld.c.E+ld.c.nPl,1) = 2*hd.c.vDotPl*hd.c.cPump/hd.c.etaPump;

    % solve the linear program
    options = optimoptions('linprog');
    options.Display = 'iter';
    [x,fval,exitflag,output] = linprog(f,A,b,Aeq,beq,lb,ub,[],options);
    disp(output);
    rhs = set(rhs,x,fval,exitflag,ld);
    check(rhs,[],lb,ub,A,b,Aeq,beq);
end

