from keras.layers import Input, Dense
from keras.models import Model
from keras import optimizers
import numpy as np
import scipy.io
from keras.models import Sequential
from keras.layers.advanced_activations import LeakyReLU, PReLU
from keras.callbacks import EarlyStopping
from keras.layers.normalization import BatchNormalization
from keras.layers import Activation
import pandas as pd
from sklearn.preprocessing import scale
#from custom_optimizers import ScipyOpt
from sklearn.preprocessing import MinMaxScaler

# fix random seed for reproducibility
np.random.seed(6)

input_file_path='D:\Test_input.mat'
dataset1 = scipy.io.loadmat(input_file_path)
dataset = dataset1['ALL']


X = np.array(dataset[:,0:33],"float32")
T = np.array(dataset[:,33],"float32")

scalerX = MinMaxScaler(feature_range=(0, 1))
X=scalerX.fit_transform(X)
scalerT = MinMaxScaler(feature_range=(0, 1))
T=scalerT.fit_transform(T)



# create model
model = Sequential()
model.add(Dense(40, input_dim=33, activation='relu'))
model.add(Dense(20, activation='relu'))
model.add(Dense(1, activation='linear'))

# compile model
model.compile(loss='mean_squared_error', optimizer='Adam') # compile the network

# define early stopping to avoid overfitting
estop = EarlyStopping(monitor='val_loss', min_delta=0, patience=10, verbose=1, mode='auto')

# Fit the model
model.fit(X, T, validation_split=0.7, epochs=5000, batch_size=8760,callbacks=[estop])


# predict ourputs
Y = model.predict(X)
real_Y = scalerT.inverse_transform(Y)

# save to csv
my_y = pd.DataFrame(real_Y)
output_path='D:\Network-output.csv'
my_y.to_csv(output_path, index=False, header=False, float_format='%.3f', decimal='.')