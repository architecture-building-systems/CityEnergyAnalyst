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
from keras.layers import Input, Dense
from keras.models import Model
import logging
from optparse import OptionParser
import sys
import cea
import  os
from time import time
import numpy as np
import pandas as pd
import cea.globalvar
import cea.inputlocator as inputlocator


__author__ = ""
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = []
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Testing"


def partitioner(building_name):
    metered_path=r'C:\reference-case-open\baseline\inputs\building-metering'
    metered_building=os.path.join(metered_path, '%s.csv' % building_name)
    #ht_cl_el=['Qhsf_kWh', 'Qcsf_kWh', 'Ef_kWh'] # this is in case of multivaribale calibration
    ht_cl_el=['Qhsf'] # disactivate this line if the previous line is active
    measured_data = pd.read_csv(metered_building,
                               usecols=ht_cl_el)

    discritization_lvl=2 # lower discritization equals more generalization
    target_m=np.asarray(measured_data)
    max_measured=np.max(target_m)
    num_inetegers=np.divide(max_measured,discritization_lvl)

    temp1=np.divide(target_m,num_inetegers)
    temp2=np.round(temp1)
    temp3=np.multiply(temp2,num_inetegers)

    target_m=temp3
    # scaling data
    scaler_target_m = MinMaxScaler(feature_range=(0, 1))
    target_m = scaler_target_m.fit_transform(target_m)

    # data sparsing
    # activate this if you are doing multivariable calibration
    # np.random.seed(7)

    # inputs_x_rows, inputs_x_cols, = target_m.shape
    # scaling and normalizing inputs

    # encoding_dim = 1
    # AE_input_dim = int(inputs_x_cols)
    # over_complete_dim = int(inputs_x_cols*2)
    # middle_dim = int((over_complete_dim/2)+1)
    #
    # #sparsing inputs
    # input_AEI = Input(shape=(AE_input_dim,))
    # encoded = Dense(over_complete_dim, activation='softplus')(input_AEI)
    # encoded = Dense(middle_dim, activation='softplus')(encoded)
    # encoded = Dense(encoding_dim, activation='softplus')(encoded)
    #
    # decoded = Dense(middle_dim, activation='softplus')(encoded)
    # decoded = Dense(over_complete_dim, activation='softplus')(decoded)
    # decoded = Dense(inputs_x_cols, activation='softplus')(decoded)
    #
    # autoencoder = Model(input_AEI, decoded)
    # autoencoder.compile(optimizer='Adamax', loss='mse')
    # autoencoder.fit(target_m, target_m, epochs=10000, batch_size= 100000, shuffle=True)
    # encoder = Model(input_AEI, encoded)
    # encoded_input=Input(shape=(encoding_dim,))
    # encoded_x=encoder.predict(target_m)



    #################################################################################
    encoded_x=target_m # disactivate if you are doing multivariable calibration

    X=np.reshape(encoded_x,(365,24))

    min_clust=2     # define the minimum number of cluster (x>1)
    max_clust=10    # define the maximum number of clusters
    num_clust= max_clust-2

    range_n_clusters = np.arange(min_clust,max_clust)
    scores_list=np.empty([num_clust, 2])

    for n_clusters in range_n_clusters:

        clusterer = KMeans(n_clusters=n_clusters, random_state=10, n_init=100)
        cluster_labels = clusterer.fit_predict(X)

        sil_score = silhouette_score(X, cluster_labels, sample_size=1000)
        ch_score=calinski_harabaz_score(X, cluster_labels)

        #print("For n_clusters =", n_clusters,
        #          "The average silhouette_score is :", sil_score, ch_score)

        scores_array=np.asarray([sil_score,ch_score])
        counter_dummy=n_clusters-2

        scores_list[counter_dummy,:]=scores_array


        #print (scores_list)
        # Compute the silhouette scores for each sample
        #sample_silhouette_values = silhouette_samples(X, cluster_labels)


    scaler_scores = MinMaxScaler(feature_range=(0, 1))
    scaler_scores = scaler_scores.fit_transform(scores_list)

    sil_score = scaler_scores[:,0]
    ch_score = scaler_scores[:,1]

    real_score = np.sqrt([(np.square(sil_score))+(np.square(ch_score))])
    best_idx=np.argmax(real_score)
    n_clusters=best_idx+2

    clusterer = KMeans(n_clusters=n_clusters, init='k-means++', n_init=100, max_iter=3000, tol=0.0001,
                       precompute_distances='auto', verbose=0, random_state=None, copy_x=True, n_jobs=1, algorithm='auto')
    cluster_labels = np.array(clusterer.fit_predict(X))

    print (n_clusters)

    target_m_new2=np.asarray(measured_data)
    target_m_new=target_m_new2[:,0]
    all_reshaped=np.reshape(target_m_new,(365,24))

    unique_clusters=np.unique(cluster_labels)
    list_medians=np.empty([n_clusters, 24])
    cluster_index_counter=0



    for cluster_index in unique_clusters:
        first_group=np.where(cluster_labels==cluster_index)[0]
        first_mat=all_reshaped[first_group,:]
        average_first_mat = np.median(first_mat, axis=0)
        list_medians[cluster_index_counter,:]=average_first_mat
        cluster_index_counter=cluster_index_counter+1

    return list_medians , cluster_labels


def run_as_script():

    building_name = 'B155066' # intended building
    list_median , cluster_labels=partitioner(building_name)


if __name__ == '__main__':
    run_as_script()