import random
import sys
from constants import *


# p=[]
# for i in range(1,100,1):
#     p.append(i/100.)

# for T01 in p:
#     T10=T01
#     T00=1-T01
#     T11=1-T10
#     mu=(T01+T10)/(T00+T11)
#     m=(mu-1)/(mu+1)
#     s="%.2f\t%.2f\t%.2f" % (T01,mu,m)
#     print(s)

# sys.exit()




# probabilities for different hours of the day based on SIA norm. In
# the original set the first hour is 1h and last is 24h.
pweek_norm=  [1,1,1,1,1,1,0.8,0.6,0.4,0.4,0.4,0.6,0.8,0.6,0.4,0.4,0.6,0.6,0.8,0.8,0.8,0.8,0.8,0.8]
#pweekend_day=[1,1,1,1,1,0.8,0.8,0.6,0.4,0.4,0.6,0.8,0.6,0.4,0.4,0.4,0.4,0.8,0.8,0.8,1,1,1,1]
pweekend_day=pweek_norm
#pweek_day=   [1,1,1,1,1,0.8,0.4,0.2,0.2,0.2,0.3,0.4,0.3,0.2,0.2,0.3,0.6,0.8,0.8,0.8,1,1,1,1]
pweek_day= pweek_norm
# monthly occupancy after SIA norm
pmonth =     [0.8,0.6,1.0,0.8,0.6,1.0,0.6,0.6,1.0,0.8,1.0,0.6]



def day_presence_prob(localt):
    """
    Return a 24-value vector with the probabilities corresponding to the current calendar day
    """
    month=localt.tm_mon
    wday=localt.tm_wday # 0-6  Monday = 0

    p=[]
    if wday < 5: # if a weekday
        for h in pweek_day:
            p.append(pmonth[month-1]*h)
    else:
        for h in pweekend_day:
            p.append(pmonth[month-1]*h)

    return p


def year_presence_prob(Npersons,scenario_DHW,btype):
    """
    Return the vector of probability, that is shared by all occupants,   for a whole year under analysis.
    Additionally, this function returns the required energy for producing DHW, based on the  maximum number of people per day.
    This functionality is added here in order to reduce the computational time and avoid additional loops.
    The Npersons parameter is used only for the DHW schedule and not for the probability function.
    scenario_DHW and btype are also exclusive for the DHW calculation.

    Btype is either office or residential,

    scenario_DHW is a value in {0,1,2}
    """
    pyear=[]
    dhw=[]

    # see constants.py for a definition of the constant values
    oneday=NMINUTES*60*24 # number of seconds in 1-day


    ## DWH volume per person per day [min,typ,max] in litters from SIA 2024
    DHW_volume={'room':[40,30,50],'kitchen':[30,10,50],'office':[10,5,15]}

    # required for the DHW calculation
    if btype == 'office':
        #dhw_volume = DHW_volume['office'][scenario_DHW]
        dhw_volume=0.0
    elif btype=='residential': # if the building is a residential one
        dhw_volume=DHW_volume['room'][scenario_DHW]+DHW_volume['kitchen'][scenario_DHW]



    for period in range(NDAYS):
        seconds=START_DATE+period*oneday
        localt=time.localtime(seconds)
        pday=day_presence_prob(localt)
        pyear=pyear+pday # concatenate the new day probabilities

        # DHW energy calculation
        totalVolume=Npersons*dhw_volume*max(pday)

        #Required thermal energy
        #It is assumed a deltaT = 35 [kJ]/3600 -> kWh
        thermalEnergy=totalVolume*Cp_water_kWh*DeltaTemp_DHW
        dhw.append(thermalEnergy) # one value per day



    return pyear,dhw



def T01_T11(mu,p0,p1):
    """
    Calculate the probability T01, it is the probability of arriving,
    0 -> 1 transition, and the probability T11, it is the probability
    of staying; given the parameter of mobility mu, the probability of
    the present state p0, and the probability of the next state t+1,
    p1.

    For some instances of mu the probabilities are bigger than 1,
    that's why the min function is used in the return statement.
    """
    m=(mu-1)/(mu+1)

    t01=(m)*p0+p1
    t11=((p0-1)/p0)*(m*p0+p1)+p1/p0

    return min(1,t01),min(1,t11)


def rand_presence(p):
    """
    Given a scalar probability P(1)=p,  return a random value, 0 or 1.
    """

    p1=int(p*100) # probability of 1
    p0=100-p1 # probability of 0
    weighted_choices = [(1,p1),(0,p0)]
    population = [val for val, cnt in weighted_choices for i in range(cnt)]

    return random.choice(population)




def individual(mu,prob,summa,Npersons):
    """
    Return the occupancy pattern for an individual.  mu is the
    parameter of mobility, and prob is the  vector defining the
    probability of presence for all individuals under analysis.


    The vectors summa and Npersons are intended to dynamically calculate the
    average of all profiles.
    """

    state=1 # initial state is considered to be present
    pattern=[]
    pattern.append(state) # first element is assumed to be 1 -> present

    if len(summa)==0:
        initialize=True
        summa.append(state)
    else:
        initialize=False

    for i in range(len(prob[:-1])):
        p0=prob[i]
        p1=prob[i+1]
        t01,t11=T01_T11(mu,p0,p1)
        # find the complementary probabilities
        #t00=1-t01
        #t10=1-t11

        if state==1:
            next=rand_presence(t11)
        else:
            next=rand_presence(t01)

        pattern.append(next)

        if initialize:
            summa.append(next/Npersons)
        else:
            summa[i+1]=summa[i+1] + next/Npersons # first position is known (equal to present -1-)
        state=next

    return pattern,summa



def normalized_occupancy_profile(Npersons,year_prob):
    """
    Calculate Npersons profiles of random occupancy.
    Each profile is calculated individually with different mu (mobility)  parameter.
    At the end all profiles are averaged.
    """


    # vector of mobility parameters
    mu_v=[0.18,0.33,0.54,0.67,0.82,1.22,1.50,3.0,5.67] #    [-0.7,-0.5,-0.3,-0.2,-0.1,0.1,0.2,1.86,0.5,0.7]

    len_mu_v=len(mu_v)

    summa=[]
    #all=[]
    for i in range(Npersons):
        mu=mu_v[int(len_mu_v*random.random())]
        #print("#",mu)
        profile_n,summa=individual(mu,year_prob,summa,Npersons)
        #all.append(profile_n)

    #return summa,all
    return summa



def occupancy_profile(type,Npersons,scenario_DHW,btype):
    """
    The variable type indicates whether the occupancy profile is
    deterministic (type=deterministic) and equal to the SIA norm
    profiles. Otherwise, if    type=random,  the markov generated occupancy
    profile is returned.

    scenario_DHW is a value in {0,1,2}, corresponding to the profiles
    standard, low and high from the SIA 2024 norm.

    btype is currently only implemented for btype=residential
    """

    # calculate the yearly probability of occupancy and the daily DHW schedule.
    year_prob,dhw_daily=year_presence_prob(Npersons,scenario_DHW,btype)

    if type=="deterministic":
        return year_prob,dhw_daily
    else:
        return normalized_occupancy_profile(Npersons,year_prob),dhw_daily
