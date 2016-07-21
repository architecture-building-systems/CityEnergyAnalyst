






def calc_simple_temp_control(tsd, prop_comfort, limit_inf_season, limit_sup_season, weekday):
    def get_hsetpoint(a, b, Thset, Thsetback, weekday):
        if (b < limit_inf_season or b >= limit_sup_season):
            if a > 0:
                if weekday >= 5:  # system is off on the weekend
                    return -30  # huge so the system will be off
                else:
                    return Thset
            else:
                return Thsetback
        else:
            return -30  # huge so the system will be off

    def get_csetpoint(a, b, Tcset, Tcsetback, weekday):
        if limit_inf_season <= b < limit_sup_season:
            if a > 0:
                if weekday >= 5:  # system is off on the weekend
                    return 50  # huge so the system will be off
                else:
                    return Tcset
            else:
                return Tcsetback
        else:
            return 50  # huge so the system will be off

    tsd['ve'] = tsd['people'] * prop_comfort['Ve_lps'] * 3.6  # in m3/h
    tsd['ta_hs_set'] = np.vectorize(get_hsetpoint)(tsd['people'], range(8760), prop_comfort['Ths_set_C'],
                                                   prop_comfort['Ths_setb_C'], weekday)
    tsd['ta_cs_set'] = np.vectorize(get_csetpoint)(tsd['people'], range(8760), prop_comfort['Tcs_set_C'],
                                                   prop_comfort['Tcs_setb_C'], weekday)

    return tsd


