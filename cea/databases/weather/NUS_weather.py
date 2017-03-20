import pandas as pd
import numpy as np
import datetime as DT
import xlrd

# the different commented parts correspond to weather files of different years, not looping them as the
# number of files involved, the date corresponding are changing with each year and there are discrepancies
# in the information available

# for 2003
# today = DT.datetime(2004, 1, 4)
#
# all_data = pd.DataFrame()
#
# for i in range(19):
#     week_ago = today - DT.timedelta(days=7)
#     today = week_ago
#
#     print 'C:/Users/Bhargava/Desktop/Weather Data/' + 'W5m_' + week_ago.strftime('%Y%m%d') + '.xls'
#     df = pd.read_excel('C:/Users/Bhargava/Desktop/Weather-Data/2003/' + 'W_' + week_ago.strftime('%Y%m%d') + '.xlsx')
#     all_data = all_data.append(df, ignore_index=True)
#
# print all_data
# all_data.to_csv("C:/Users/Bhargava/Desktop/Weather-Data/2003/2003.csv", encoding="utf-8")

# for 2017
year = str(2005)
method = 0  # 0 for hourly, 1 for 5 min data
time_interval = ['hourly', '5min']
file_name = ['W_', 'W5m_']

today = DT.datetime(2005, 1, 2)

all_data = pd.DataFrame()

for i in range(52):
    week_later = today

    print 'C:/Users/Bhargava/Desktop/Weather Data/' + file_name[method] + week_later.strftime('%Y%m%d') + '.xls'
    df = pd.read_excel('C:/Users/Bhargava/Desktop/Weather-Data/' + year + '/' + file_name[method] + week_later.strftime('%Y%m%d') + '.xlsx')
    all_data = all_data.append(df, ignore_index=True)
    week_later = today + DT.timedelta(days=7)
    today = week_later

print all_data
all_data.to_csv("C:/Users/Bhargava/Desktop/Weather-Data/" + year + "/" + year + '_' + time_interval[method] + ".csv", encoding="utf-8")

# for 2012
# year = str(2012)
# method = 1  # 0 for hourly, 1 for 5 min data
# time_interval = ['hourly', '5min']
# file_name = ['W_', 'W5m_']
#
# today = DT.datetime(2012, 1, 1)
#
# all_data = pd.DataFrame()
#
# for i in range(52):
#     week_later = today
#
#     if week_later not in [DT.datetime(2012, 7, 1), DT.datetime(2012, 7, 8), DT.datetime(2012, 7, 15)]:
#         # print week_later
#         print 'C:/Users/Bhargava/Desktop/Weather Data/' + file_name[method] + week_later.strftime('%Y%m%d') + '.xls'
#         df = pd.read_excel('C:/Users/Bhargava/Desktop/Weather-Data/' + year + '/' + file_name[method] + week_later.strftime('%Y%m%d') + '.xlsx')
#         all_data = all_data.append(df, ignore_index=True)
#     week_later = today + DT.timedelta(days=7)
#     today = week_later
#
# print all_data
# all_data.to_csv("C:/Users/Bhargava/Desktop/Weather-Data/" + year + "/" + year + '_' + time_interval[method] + ".csv", encoding="utf-8")

# for 2010
# year = str(2010)
# method = 0  # 0 for hourly, 1 for 5 min data
# time_interval = ['hourly', '5min']
# file_name = ['W_', 'W5m_']
#
# today = DT.datetime(2010, 1, 3)
#
# all_data = pd.DataFrame()
#
# for i in range(52):
#     week_later = today
#
#     if week_later not in [DT.datetime(2010, 6, 6), DT.datetime(2010, 6, 13), DT.datetime(2010, 6, 20), DT.datetime(2010, 6, 27)]:
#         # print week_later
#         print 'C:/Users/Bhargava/Desktop/Weather Data/' + file_name[method] + week_later.strftime('%Y%m%d') + '.xls'
#         df = pd.read_excel('C:/Users/Bhargava/Desktop/Weather-Data/' + year + '/' + file_name[method] + week_later.strftime('%Y%m%d') + '.xlsx')
#         all_data = all_data.append(df, ignore_index=True)
#     week_later = today + DT.timedelta(days=7)
#     today = week_later
#
# print all_data
# all_data.to_csv("C:/Users/Bhargava/Desktop/Weather-Data/" + year + "/" + year + '_' + time_interval[method] + ".csv", encoding="utf-8")

# for 2009
# year = str(2009)
# method = 1  # 0 for hourly, 1 for 5 min data
# time_interval = ['hourly', '5min']
# file_name = ['W_', 'W5m_']
#
# today = DT.datetime(2009, 1, 4)
#
# all_data = pd.DataFrame()
#
# for i in range(52):
#     week_later = today
#
#     if week_later not in [ DT.datetime(2009, 11, 1)]:
#         # print week_later
#         print 'C:/Users/Bhargava/Desktop/Weather Data/' + file_name[method] + week_later.strftime('%Y%m%d') + '.xls'
#         df = pd.read_excel('C:/Users/Bhargava/Desktop/Weather-Data/' + year + '/' + file_name[method] + week_later.strftime('%Y%m%d') + '.xlsx')
#         all_data = all_data.append(df, ignore_index=True)
#     week_later = today + DT.timedelta(days=7)
#     today = week_later
#
# print all_data
# all_data.to_csv("C:/Users/Bhargava/Desktop/Weather-Data/" + year + "/" + year + '_' + time_interval[method] + ".csv", encoding="utf-8")

# for 2005
# year = str(2005)
# method = 0  # 0 for hourly, 1 for 5 min data
# time_interval = ['hourly', '5min']
# file_name = ['W_', 'W5m_']
#
# today = DT.datetime(2005, 1, 2)
#
# all_data = pd.DataFrame()
#
# for i in range(52):
#     week_later = today
#
#     if week_later not in [ DT.datetime(2005, 1, 23)]:
#         # print week_later
#         print 'C:/Users/Bhargava/Desktop/Weather Data/' + file_name[method] + week_later.strftime('%Y%m%d') + '.xls'
#         df = pd.read_excel('C:/Users/Bhargava/Desktop/Weather-Data/' + year + '/' + file_name[method] + week_later.strftime('%Y%m%d') + '.xlsx')
#         all_data = all_data.append(df, ignore_index=True)
#     week_later = today + DT.timedelta(days=7)
#     today = week_later
#
# print all_data
# all_data.to_csv("C:/Users/Bhargava/Desktop/Weather-Data/" + year + "/" + year + '_' + time_interval[method] + ".csv", encoding="utf-8")

# year = str(2004)
# method = 1  # 0 for hourly, 1 for 5 min data
# time_interval = ['hourly', '5min']
# file_name = ['W_', 'W5m_']
#
# today = DT.datetime(2004, 4, 18)
#
# all_data = pd.DataFrame()
#
# for i in range(37):
#     week_later = today
#
#     if week_later not in [ DT.datetime(2005, 1, 23)]:
#         # print week_later
#         print 'C:/Users/Bhargava/Desktop/Weather Data/' + file_name[method] + week_later.strftime('%Y%m%d') + '.xls'
#         df = pd.read_excel('C:/Users/Bhargava/Desktop/Weather-Data/' + year + '/' + file_name[method] + week_later.strftime('%Y%m%d') + '.xlsx')
#         all_data = all_data.append(df, ignore_index=True)
#     week_later = today + DT.timedelta(days=7)
#     today = week_later
#
# print all_data
# all_data.to_csv("C:/Users/Bhargava/Desktop/Weather-Data/" + year + "/" + year + '_' + time_interval[method] + ".csv", encoding="utf-8")