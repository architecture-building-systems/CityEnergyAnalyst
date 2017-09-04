from __future__ import print_function
from sklearn.metrics import silhouette_samples, silhouette_score, calinski_harabaz_score
from sklearn.datasets import fetch_20newsgroups
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer
from sklearn import metrics
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.preprocessing import MinMaxScaler
import logging
from optparse import OptionParser
import sys
import cea
from time import time
import numpy as np
import pandas as pd
import cea.globalvar
import cea.inputlocator as inputlocator


# #############################################################################
# Do the actual clustering
word_size = 9
alphabet_size = 7
gv = cea.globalvar.GlobalVariables()
scenario_path = r'C:\reference-case-open\baseline'
locator = inputlocator.InputLocator(scenario_path=scenario_path)
building_name = 'B155066'
ht_cl_el=['Qhsf_kWh', 'Qcsf_kWh', 'Ef_kWh']
measued_dataset = pd.read_csv(locator.get_demand_measured_file(building_name),
                           usecols=ht_cl_el )

inputs_x=np.asarray(measued_dataset)




#################################################################################
from sklearn.preprocessing import MinMaxScaler
from keras.layers import Input, Dense
from keras.models import Model

np.random.seed(7)

inputs_x_rows, inputs_x_cols, = inputs_x.shape
# scaling and normalizing inputs
scalerX = MinMaxScaler(feature_range=(0, 1))
inputs_x = scalerX.fit_transform(inputs_x)
encoding_dim = 1
middle_dim = 3
over_complete_dim = 6
AE_input_dim = int(inputs_x_cols)

#sparsing inputs
input_AEI = Input(shape=(AE_input_dim,))
encoded = Dense(over_complete_dim, activation='softplus')(input_AEI)
encoded = Dense(middle_dim, activation='softplus')(encoded)
encoded = Dense(encoding_dim, activation='softplus')(encoded)

decoded = Dense(middle_dim, activation='softplus')(encoded)
decoded = Dense(over_complete_dim, activation='softplus')(decoded)
decoded = Dense(inputs_x_cols, activation='softplus')(decoded)

autoencoder = Model(input_AEI, decoded)
autoencoder.compile(optimizer='Adamax', loss='mse')
autoencoder.fit(inputs_x,inputs_x,epochs=10000, batch_size= 100000, shuffle=True)
encoder = Model(input_AEI, encoded)
encoded_input=Input(shape=(encoding_dim,))
encoded_x=encoder.predict(inputs_x)



#################################################################################

X=np.reshape(encoded_x,(365,24))

range_n_clusters = np.arange(2,50)
scores_list=np.empty([48, 2])
for n_clusters in range_n_clusters:


    # Initialize the clusterer with n_clusters value and a random generator
    # seed of 10 for reproducibility.
    clusterer = KMeans(n_clusters=n_clusters, random_state=10, n_init=100)
    cluster_labels = clusterer.fit_predict(X)

    # The silhouette_score gives the average value for all the samples.
    # This gives a perspective into the density and separation of the formed
    # clusters
    sil_score = silhouette_score(X, cluster_labels, sample_size=1000)
    ch_score=calinski_harabaz_score(X, cluster_labels)



    #print("For n_clusters =", n_clusters,
    #          "The average silhouette_score is :", sil_score, ch_score)

    scores_array=np.asarray([sil_score,ch_score])
    counter_dummy=n_clusters-2

    scores_list[counter_dummy,:]=scores_array


    print (scores_list)
    # Compute the silhouette scores for each sample
    #sample_silhouette_values = silhouette_samples(X, cluster_labels)


scaler_sil = MinMaxScaler(feature_range=(0, 1))
scaler_ch = MinMaxScaler(feature_range=(0, 1))
sil_score = scaler_sil.fit_transform(scores_list[:,0])
ch_score = scaler_ch.fit_transform(scores_list[:,1])
real_score = np.sqrt([(np.square(sil_score))+(np.square(ch_score))])
best_idx=np.argmax(real_score)
n_clusters=best_idx+2

clusterer = KMeans(n_clusters=n_clusters, init='k-means++', n_init=100, max_iter=3000, tol=0.0001,
                   precompute_distances='auto', verbose=0, random_state=None, copy_x=True, n_jobs=1, algorithm='auto')
cluster_labels = clusterer.fit_predict(X)

print (cluster_labels)