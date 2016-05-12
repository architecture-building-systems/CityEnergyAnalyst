import pandas as pd
import numpy as np

    x = pd.read_excel(r'C:\Users\Jimeno\Desktop\BOOK_1.xlsx', 'ADMIN').T




def get_schedules(x)
    weekday_occ = x['Weekday_1'].values
    saturday_occ = x['Saturday_1'].values
    sunday_occ = x['Sunday_1'].values
    weekday_el = x['Weekday_2'].values
    saturday_el = x['Saturday_2'].values
    sunday_el = x['Sunday_2'].values
    weekday_dhw = x['Weekday_3'].values
    saturday_dhw = x['Saturday_3'].values
    sunday_dhw = x['Sunday_3'].values
    month_value = x['Month'].values
    date = pd.date_range('1/1/2016', periods=8760, freq='H')
    dates = len(date)
    occ = []
    el = []
    dhw = []
    for hour in range(dates):
        month_year = date[hour].month-1
        hour_day = date[hour].hour
        if date[hour].dayofweek is 0 or 1 or 2 or 3 or 4: #weekday
            occ.append(weekday_occ[hour_day]*month_value[month_year])
            el.append(weekday_el[hour_day]*month_value[month_year])
            dhw.append(weekday_dhw[hour_day]*month_value[month_year])
        elif date[hour].dayofweek is 5: #saturday
            occ.append(saturday_occ[hour_day] * month_value[month_year])
            el.append(saturday_el[hour_day] * month_value[month_year])
            dhw.append(saturday_dhw[hour_day] * month_value[month_year])
        else: # sunday
            occ.append(sunday_occ[hour_day] * month_value[month_year])
            el.append(sunday_el[hour_day] * month_value[month_year])
            dhw.append(sunday_dhw[hour_day] * month_value[month_year])

    return occ, el, dwh

