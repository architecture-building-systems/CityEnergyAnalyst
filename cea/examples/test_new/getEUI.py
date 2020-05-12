

import cea.config
import cea.inputlocator
import pandas as pd

def getEUI(locator):
    monthly_measured_data = pd.read_csv(locator.get_monthly_measurements())
    return monthly_measured_data
x=1