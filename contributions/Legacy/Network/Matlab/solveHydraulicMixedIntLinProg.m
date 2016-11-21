%-----------------
% Florian Mueller
% December 2014
%-----------------

function hs = solveHydraulicMixedIntLinProg(ld,hd,hs)
    % hydraulic variables (see report.pdf, section 4.2)
    % x = [x_i_e;vDot_i_e;p_n];

    % integer constraints (see report.pdf, expr 2)
    intcon = double(1:hd.c.I*ld.c.E);

    % lower and upper bounds (see report.pdf, expr 3,4)
    lb = [zeros(hd.c.I*ld.c.E,1);-Inf*ones(hd.c.I*ld.c.E,1);        hd.c.pRq_n];
    ub = [ ones(hd.c.I*ld.c.E,1); Inf*ones(hd.c.I*ld.c.E,1);Inf*ones(ld.c.N,1)];

    % inequality constraints (see report.pdf, expr 5)
    A1 = zeros(hd.c.I*ld.c.E,2*hd.c.I*ld.c.E+ld.c.N);
    b1 = zeros(hd.c.I*ld.c.E,1);
    A1(:,1:hd.c.I*ld.c.E)       = diag(repmat(hd.c.vDotMin_i,[ld.c.E,1]));
    A1(:,hd.c.I*ld.c.E+1:2*hd.c.I*ld.c.E) = -eye(hd.c.I*ld.c.E);

    % inequality constraints (see report.pdf, expr 6)
    A2 = zeros(hd.c.I*ld.c.E,2*hd.c.I*ld.c.E+ld.c.N);
    b2 = zeros(hd.c.I*ld.c.E,1);
    A2(:,1:hd.c.I*ld.c.E)       = -diag(repmat(hd.c.vDotMax_i,[ld.c.E,1]));
    A2(:,hd.c.I*ld.c.E+1:2*hd.c.I*ld.c.E) = eye(hd.c.I*ld.c.E);

    % help
    H = zeros(ld.c.E,ld.c.N);
    for e=1:ld.c.E
        H(e,ld.c.sSpp_e(e,:)) = [-1,1];
    end

    % inequality constraints (see report.pdf, expr 7)
    A3 = zeros(hd.c.K*ld.c.E,2*hd.c.I*ld.c.E+ld.c.N);
    b3 = zeros(hd.c.K*ld.c.E,1);
    A3(:,1:hd.c.I*ld.c.E) = kron(eye(ld.c.E),hd.c.b_k_i);
    A3(:,hd.c.I*ld.c.E+1:2*hd.c.I*ld.c.E) = kron(eye(ld.c.E),hd.c.a_k_i);
    A3(:,2*hd.c.I*ld.c.E+1:2*hd.c.I*ld.c.E+ld.c.N) = kron(diag(1./hd.c.L_e)*H,ones(hd.c.K,1));

    % equality constraints (see report.pdf, expr 8)
    Aeq1 = zeros(ld.c.E,2*hd.c.I*ld.c.E+ld.c.N);
    beq1 = ones(ld.c.E,1);
    Aeq1(:,1:hd.c.I*ld.c.E) = kron(eye(ld.c.E),ones(1,hd.c.I));

    % equality constraints (see report.pdf, expr 9)
    Aeq2 = zeros(ld.c.N,2*hd.c.I*ld.c.E+ld.c.N);
    beq2 = -hd.c.vDotRq_n;
    Aeq2(:,hd.c.I*ld.c.E+1:2*hd.c.I*ld.c.E) = kron(H',ones(1,hd.c.I));
    Aeq2 = Aeq2(1:ld.c.N~=ld.c.nPl,:);
    beq2 = beq2(1:ld.c.N~=ld.c.nPl);

    % objective (see report.pdf, expr 1)
    f = zeros(2*hd.c.I*ld.c.E+ld.c.N,1);
    f(1:hd.c.I*ld.c.E,1)   = kron(hd.c.L_e,hd.c.c_i);
    f(2*hd.c.I*ld.c.E+ld.c.nPl,1) = 2*hd.c.vDotPl*hd.c.cPump/hd.c.etaPump;

    % assemble
    A   = [A1;A2;A3];
    b   = [b1;b2;b3];
    Aeq = [Aeq1;Aeq2];
    beq = [beq1;beq2];

    % solve the mixed integer linear program
    options = optimoptions('intlinprog');
    options.CutGeneration = 'advanced';
%     options.IPPreprocess = 'advanced';
%     options.CutGenMaxIter = 25;
%     options.Heuristics = 'rins';
    options.RelObjThreshold = 1e-6;
%     options.TolGapRel = 1e-7;
%     options.TolInteger = 1e-6;
    [x,fval,exitflag,output] = intlinprog(f,intcon,A,b,Aeq,beq,lb,ub,options);
    disp(output);
    hs = set(hs,x,fval,exitflag,ld,hd);
    check(hs,intcon,lb,ub,A,b,Aeq,beq);
end

