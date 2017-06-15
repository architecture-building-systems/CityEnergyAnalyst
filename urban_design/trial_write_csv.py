import csv

with open('persons.csv', 'wb') as csvfile:
    filewriter = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    filewriter.writerow(['NAMLE','BUILT','ROOF','WINDOWS','PARTITION','BASEMENT','HVAC','ENVELOPE'])
    filewriter.writerow(['B01','2016','0','0','0','0','0','0'])
    filewriter.writerow(['Steve', 'Software Developer'])
    filewriter.writerow(['Paul', 'Manager'])

import dbf

some_table = dbf.from_csv(csvfile='/persons.csv', to_disk=True)