# FIXME: what is this for? can we remove it?

def main():
    import pandas as pd

    data = pd.read_excel(r'C:\Users\JimenoF\Desktop/Admin data Sep.xlsx', sheet_name='Admin Sep Raw data')
    index = pd.date_range('9/1/2016', periods=1392, freq='30min')

    series = pd.Series(data['KWH'].values, index=index)
    resample = series.resample('1H').mean()
    print resample.sum()

if __name__ == '__main__':
    main()