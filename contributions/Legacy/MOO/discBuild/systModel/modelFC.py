# -*- coding: utf-8 -*-

"""
==========================
System Modeling: Fuel Cell
==========================

"""

def FuelCell_Cost(P_design, gV):
    """
    Calculates the cost of a Fuel Cell in CHF
    
    http://hexis.com/sites/default/files/media/publikationen/140623_hexis_galileo_ibb_profitpaket.pdf?utm_source=HEXIS+Mitarbeitende&utm_campaign=06d2c528a5-1_Newsletter_2014_Mitarbeitende_DE&utm_medium=email&utm_term=0_e97bc1703e-06d2c528a5-
    
    Parameters
    ----------
    P_design : float
        Design THERMAL Load of Fuel Cell [W_th]
    
    Returns
    -------
    InvC_return : float
        total investment Cost 
    
    InvCa : float
        annualized investment costs in CHF
        
    """
    
    InvC = (1+gV.FC_overhead) * gV.FC_stack_cost * P_design / 1000 # FC_stack_cost = 55'000 CHF  / kW_therm, 10 % extra (overhead) cost
    
    InvCa =  InvC * gV.FC_i * (1+ gV.FC_i) ** gV.FC_n / ((1+gV.FC_i) ** gV.FC_n - 1) 
    
    
    return InvCa



def FC_operation(Q_load, Q_design, phi_threshold, approach_call):

    """
    VALID FOR Q in range of 1-10kW_el !
    Compared to LHV of NG
    
    Efficiency for operation of a SOFC (based on LHV of nat. gas)
    
    Includes all auxillary losses
    
    Fuel = Natural Gas 
    
    Modeled after: 
        Approach A:
            http://energy.gov/eere/fuelcells/distributedstationary-fuel-cell-systems
            and
            NREL : p.5  of http://www.nrel.gov/vehiclesandfuels/energystorage/pdfs/36169.pdf
            
        Approach B:
            http://etheses.bham.ac.uk/641/1/Staffell10PhD.pdf
    
    Parameters
    ----------
    Q_load : float
        Load of time step
        
    Q_design : float
        Design Load of FC
        
    phi_threshold : float
        where Maximum Efficiency is reached, used for Approach A
        
    approach_call : string
        choose "A" or "B": A = NREL-Approach, B = Empiric Approach
     
    Returns
    -------
    eta_el : float
        electric efficiency of FC (Lower Heating Value), in abs. numbers
    
    Q_fuel : float
        Heat dem from fuel (in Watt)
    
    
    
    """
    phi = 0.0


    """ APPROACH A - AFTER NREL """
    if approach_call == "A":
                
        phi = float (Q_load) / float(Q_design)
        eta_max = 0.425 # from energy.gov
        
        if phi >= phi_threshold: # from NREL-Shape
            eta_el = eta_max - ((1/6.0 * eta_max)/ (1.0-phi_threshold) )* abs(phi-phi_threshold)
    
        
        if phi < phi_threshold:
            if phi <= 118/520.0 * phi_threshold:
                eta_el = eta_max * 2/3 * (phi / (phi_threshold*118/520.0))
    
            
            if phi < 0.5 * phi_threshold and phi >= 118/520.0 * phi_threshold:
                eta_el = eta_max * 2/3.0 + eta_max * 0.25 * (phi-phi_threshold*118/520.0) / (phi_threshold * (0.5 - 118/520.0))
                
            if phi > 0.5 * phi_threshold and phi < phi_threshold:
                eta_el = eta_max * (2/3.0 + 0.25)  +  1/12.0 * eta_max * (phi - phi_threshold * 0.5) / (phi_threshold * (1-0.5))
    
        eta_therm_max = 0.45 # constant, after energy.gov
        
        if phi < phi_threshold:
            eta_therm = 0.5 * eta_therm_max * (phi / phi_threshold)
    
        else:
            eta_therm = 0.5 * eta_therm_max * (1 + eta_therm_max * ((phi - phi_threshold) / (1 - phi_threshold)))
    
    
    """ SECOND APPROACH  after http://etheses.bham.ac.uk/641/"""
    if approach_call == "B":
            
        if Q_design > 0:
            phi = float(Q_load) / float(Q_design)
    
        else:
            phi = 0
            
        eta_el_max = 0.39  # after http://etheses.bham.ac.uk/641/   
        eta_therm_max = 0.58   # http://etheses.bham.ac.uk/641/     * 1.11 as this source gives eff. of HHV
        eta_el_score = -0.220 + 5.277 * phi - 9.127 * phi**2 + 7.172* phi ** 3 - 2.103* phi**4
        eta_therm_score = 0.9 - 0.07 * phi + 0.17 * phi**2
        
        eta_el = eta_el_max * eta_el_score
        eta_therm = eta_therm_max * eta_therm_score
        
        if phi < 0.2:
            eta_el = 0
            
    
    return eta_el, eta_therm

""" 
    #    USED FOR PLOTS:
    
"""
"""
Q_load = np.linspace(0,100, 100)
 
eta_result_el = np.zeros(len(Q_load)) 
eta_result_th = np.zeros(len(Q_load))
eta_result_tot = np.zeros(len(Q_load))
Q_max = max(Q_load) 


for k in range(len(Q_load)):
    phi = Q_load[k] / float(Q_max) 

    eta_el_max = 0.39  # after http://etheses.bham.ac.uk/641/   * 1.11 as this source gives eff. of HHV
    eta_therm_max = 0.58   # http://etheses.bham.ac.uk/641/     * 1.11 as this source gives eff. of HHV
    eta_el_score = -0.220 + 5.277 * phi - 9.127 * phi**2 + 7.172* phi ** 3 - 2.103* phi**4
    eta_therm_score = 0.9 - 0.07 * phi + 0.17 * phi**2
    
    eta_el = eta_el_score * eta_therm_max
    eta_therm = eta_therm_score * eta_el_max
    eta_tot = eta_therm + eta_el
    eta_result_el[k] = eta_el
    eta_result_th[k] = eta_therm
    eta_result_tot[k] = eta_tot
    
eta_el, = plt.plot(eta_result_el*100, 'b-', label="eta_el")
eta_th, = plt.plot(eta_result_th*100 , 'r-', label="eta_th")
eta_tot, = plt.plot(eta_result_tot*100, 'g-', label="eta_tot")
plt.legend([eta_el,eta_th, eta_tot],["Electric Efficiency","Thermal Efficiency","Total Fuel Efficiency"], loc=4)

plt.ylabel('Fuel Cell Efficiency [%]')
plt.xlabel('Percent of Part Load')
plt.xlim([0,100])
plt.ylim([0,100])
plt.show()
"""