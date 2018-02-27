%% Validation script for looped networks

path = 'C:\Users\Lenny Ro\Dropbox\ETH\Master HS16\Master Thesis\Master-Thesis-LR\Thermal networks\Looped Networks\Validation\Outputs\Branch\N1_2P\'

%% setup network matrix A

% node equations
A = csvread(strcat(path,'DH__EdgeNode.csv'),1,1);

% pressure equations
%in N1 there are 3 fundamental loops:
%(0,1,2,3,4,5,6,7);(0,10,8,7);(1,2,9,10)
p_nodes = csvread(strcat(path,'DH__P_Supply_Pa.csv'),1,1);
% demand matrix
b_matrix = csvread(strcat(path,'Nominal_NodeMassFlow_DH_.csv'),1,1);

% read in mass flows
m_matrix = csvread(strcat(path,'Nominal_EdgeMassFlow_DH_.csv'),1,1);

% setup containers for solution storage
k1_difference = zeros(8760,11); %11 nodes
k2_difference = zeros(8760,3); %3 loops

%% setup and solve
for t = 1:8760
    p_edges=zeros(10,0);
    p_edges(1) = p_nodes(t, 2)-p_nodes(t, 1);
    p_edges(2) = p_nodes(t, 3)-p_nodes(t, 2);
    p_edges(3) = p_nodes(t, 6)-p_nodes(t, 3);
    p_edges(4) = p_nodes(t, 9)-p_nodes(t, 6);
    p_edges(5) = p_nodes(t, 8)-p_nodes(t, 9);
    p_edges(6) = p_nodes(t, 7)-p_nodes(t, 8);
    p_edges(7) = p_nodes(t, 4)-p_nodes(t, 7);
    p_edges(8) = p_nodes(t, 1)-p_nodes(t, 4);
    %shared nodes, careful with sign, always clockwise = positive, here for
    %loop (0,10,8,7)
    p_edges(9) = p_nodes(t, 4)-p_nodes(t, 5);
    p_edges(10) = p_nodes(t, 5)-p_nodes(t, 6);
    p_edges(11) = p_nodes(t, 5)-p_nodes(t, 2);


    % setup demand vector b
    b = (b_matrix(t, :));
    %setup mass flows m
    m = transpose(m_matrix(t, :));
    
    b_CEA = A*m;
    b_CEA = transpose(b_CEA);
    k1_difference(t,:) = b-b_CEA;
    
    k2_difference(t,:) = [p_edges(1)+p_edges(2)+p_edges(3)+p_edges(4)+ ...
        p_edges(5)+p_edges(6)+p_edges(7)+p_edges(8), p_edges(1)+p_edges(11)+ ...
        p_edges(9)+p_edges(8), p_edges(2)+p_edges(3)+p_edges(10)-p_edges(11)];
end

max(max(abs(k1_difference)))
max(max(abs(k2_difference)))


%% solve and compare to b