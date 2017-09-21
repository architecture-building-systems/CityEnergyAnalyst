# from keras.layers import Input, Dense
# from keras.models import Model
# from keras import optimizers
# import numpy as np
# import scipy.io
# from keras.models import Sequential
# from keras.layers.advanced_activations import LeakyReLU, PReLU
# from keras.callbacks import EarlyStopping
# from keras.layers.normalization import BatchNormalization
# from keras.layers import Activation
# import pandas as pd
# from sklearn.preprocessing import scale
# #from custom_optimizers import ScipyOpt
# from sklearn.preprocessing import MinMaxScaler
#
# # fix random seed for reproducibility
# np.random.seed(6)
#
# input_file_path='D:\Test_input.mat'
# dataset1 = scipy.io.loadmat(input_file_path)
# dataset = dataset1['ALL']
#
#
# X = np.array(dataset[:,0:33],"float32")
# T = np.array(dataset[:,33],"float32")
#
# scalerX = MinMaxScaler(feature_range=(0, 1))
# X=scalerX.fit_transform(X)
# scalerT = MinMaxScaler(feature_range=(0, 1))
# T=scalerT.fit_transform(T)
#
#
#
# # create model
# model = Sequential()
# model.add(Dense(40, input_dim=33, activation='relu'))
# model.add(Dense(20, activation='relu'))
# model.add(Dense(1, activation='linear'))
#
# # compile model
# model.compile(loss='mean_squared_error', optimizer='Adam') # compile the network
#
# # define early stopping to avoid overfitting
# estop = EarlyStopping(monitor='val_loss', min_delta=0, patience=10, verbose=1, mode='auto')
#
# # Fit the model
# model.fit(X, T, validation_split=0.7, epochs=5000, batch_size=8760,callbacks=[estop])
#
#
# # predict ourputs
# Y = model.predict(X)
# real_Y = scalerT.inverse_transform(Y)
#
# # save to csv
# my_y = pd.DataFrame(real_Y)
# output_path='D:\Network-output.csv'
# my_y.to_csv(output_path, index=False, header=False, float_format='%.3f', decimal='.')

import pandas as pd
from cea.utilities.dbfreader import dbf_to_dataframe
from cea.utilities.dbfreader import dataframe_to_dbf



#print(a)

dbf_path=r'C:\Users\Fazel\Desktop\architecture.dbf'
dbf_path2=r'C:\Users\Fazel\Desktop\architecture2.dbf'
table2 = dbf_to_dataframe(dbf_path)
#print(table2)
a=table2.iloc[5]
a['Name']='B17'
a['Hs']=1
#f1=a.iloc[[5]]
#f2=a.iloc[[10]]
#f3=a.iloc[[11]]
#f4=a.iloc[[12]]
#f5=a.iloc[[13]]
#f6=a.iloc[[14]]



#table2.append(f1)
#aa2=table2.append(f2)
#aa3=table2.append(f3)
#aa4=table2.append(f4)
#aa5=table2.append(f5)
#aa6=table2.append(f6)

print(table2)

#dataframe_to_dbf(table2,dbf_path2)
