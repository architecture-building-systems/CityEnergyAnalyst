import pandas as pd



def get_schedules(x):
    schedules = []
    for use in list_uses():
        # read lists of every daily profile
        occ_schedules, el_schedules, dhw_schedules, pro_schedules, month = read_schedules(use, x)

        # get yearly vectors
        schedule = get_yearly_vectors(date, occ_schedules, el_schedules, dhw_schedules, pro_schedules, month)

        schedules.append(schedule)

    return schedules

def read_schedules(use, x):

    occ = [x['Weekday_1'].values,x['Saturday_1'].values,x['Sunday_1'].values]
    el = [x['Weekday_2'].values, x['Saturday_2'].values, x['Sunday_2'].values]
    dhw = [x['Weekday_3'].values, x['Saturday_3'].values, x['Sunday_3'].values]
    month = x['month'].values

    if use is "INDUSTRIAL":
        pro = [x['Weekday_4'].values, x['Saturday_4'].values, x['Sunday_4'].values]
    else:
        pro = [[]*24, []*24,[]*24]

    return occ, el, dhw, pro, month

def get_yearly_vectors(date, occ_schedules, el_schedules, dhw_schedules, pro_schedules, month)
    occ = []
    el = []
    dhw = []
    pro = []
    for hour in range(8760):
        month_year = date[hour].month-1
        hour_day = date[hour].hour
        if date[hour].dayofweek is 0 or 1 or 2 or 3 or 4: #weekday
            occ.append(occ_schedules[0][hour_day]*month[month_year])
            el.append(el_schedules[0][hour_day]*month[month_year])
            dhw.append(dhw_schedules[0][hour_day]*month[month_year])
            pro.append(pro_schedules[0][hour_day] * month[month_year])
        elif date[hour].dayofweek is 5: #saturday
            occ.append(occ_schedules[1][hour_day] * month[month_year])
            el.append(el_schedules[1][hour_day] * month[month_year])
            dhw.append(dhw_schedules[1][hour_day] * month[month_year])
            pro.append(pro_schedules[1][hour_day] * month[month_year])
        else: # sunday
            occ.append(occ_schedules[2][hour_day] * month[month_year])
            el.append(el_schedules[2]l[hour_day] * month[month_year])
            dhw.append(dhw_schedules[2][hour_day] * month[month_year])
            pro.append(pro_schedules[2][hour_day] * month[month_year])

    schedule = pd.DataFrame('DATE': date)

    return schedule

x = pd.read_excel(r'C:\Users\JF\Desktop\book_1.xlsx', 'OFFICE').T
x.to_csv(r'C:\Users\JF\Desktop\book_1.csv')
schedules = get_schedules(x)
print occ
