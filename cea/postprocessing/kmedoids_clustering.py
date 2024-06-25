
### KMedoids clustering ###

# Standard imports
import matplotlib.pyplot as plt
import os
import pandas as pd
import numpy as np

# Import sklearn features
from sklearn_extra.cluster import KMedoids
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, silhouette_samples, pairwise_distances
from sklearn import metrics

from directories_files_handler import calculate_percentage_change

def data_preprocessing(x):

    # Remove non-numeric columns
    percentage_change = calculate_percentage_change(x)
    x = x.select_dtypes(include=[np.number])
    x = x.drop(index='current_DES')
    percentage_change = percentage_change.drop(index='current_DES')

    # Scale the data before applying the KMedoids algorithm
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(x)
    objective_labels = x.columns
    system_names = x.index

    return X_scaled, scaler, objective_labels, system_names, percentage_change
def kmedoids_clustering(X_scaled, n_medoids, system_names):

    # Apply k-medoids algorithm
    kmedoids = KMedoids(n_clusters=n_medoids)
    kmedoids.fit(X_scaled)

    # Retrieve the labels and medoids
    labels = kmedoids.labels_
    medoids = kmedoids.cluster_centers_
    medoids_indices = kmedoids.medoid_indices_
    selected_systems = system_names[medoids_indices]

    return labels, medoids, selected_systems

def calculate_silhouette_score(X_scaled, labels, n_medoids):
    # Calculate the silhouette score
    silhouette_avg = silhouette_score(X_scaled, labels) # Total score for all the clusters
    silhouette_values = silhouette_samples(X_scaled, labels) # Individual score for each cluster
    silhouette_values_per_cluster = []

    for i in range(n_medoids):
        ith_cluster_silhouette_values = silhouette_values[labels == i]
        silhouette_values_per_cluster.append(np.mean(ith_cluster_silhouette_values))

    return silhouette_avg, silhouette_values

def test_different_cluster_numbers(X_scaled, path):
    # Use the silhoutte score to determine the optimal number of clusters
    silhouette_scores = []
    nr_clusters = []
    for i in range(2, len(X_scaled)):
        try:
            kmedoids = KMedoids(n_clusters=i)
            kmedoids.fit(X_scaled)
            labels_test = kmedoids.labels_
            silhouette_avg = silhouette_score(X_scaled, labels_test)
            silhouette_scores.append(silhouette_avg)
            nr_clusters.append(i)
        except:
            print(f'Error occurred in {path}')

    # Select the optimal number of clusters based on the silhouette score
    if not silhouette_scores:
        n_clusters = 1
    else:
        silhouette_scores_df = pd.DataFrame(data=silhouette_scores, index=nr_clusters)
        n_clusters = silhouette_scores_df.idxmax()[0]

        # Plot the silhouette scores
        plt.figure(figsize=(10, 6))
        plt.plot(nr_clusters, silhouette_scores, marker='o')
        plt.title('Silhouette Score vs Number of Clusters')
        plt.xlabel('Number of Clusters')
        plt.ylabel('Silhouette Score')
        plt.savefig(os.path.join(path, 'silhouette_score.png'))
        plt.close('all')

    return n_clusters

# Function to calculate the within-cluster sum of squares for different number of clusters
def evaluate_elbow(X):
    wcss = []
    for n_clusters in range(1, len(X)):
        kmedoids = KMedoids(n_clusters=n_clusters, random_state=42)
        kmedoids.fit(X)
        wcss.append(np.sum(np.min(pairwise_distances(X, kmedoids.cluster_centers_), axis=1)))
        print(f"WCSS for {n_clusters} clusters: {wcss[-1]:.3f}")

    # Plotting the WCSS
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(X)), wcss, marker='o')
    plt.xlabel('Number of clusters')
    plt.ylabel('WCSS')
    plt.title('Elbow Method')
    plt.show()

# Calculate the purity score
def purity_score(y_true, y_pred):
    # compute contingency matrix (also called confusion matrix)
    contingency_matrix = metrics.cluster.contingency_matrix(y_true, y_pred)
    # return purity
    return np.sum(np.amax(contingency_matrix, axis=0)) / np.sum(contingency_matrix)

def convert_medoids_to_original_scale(medoids, scaler, objective_labels, selected_systems_names):

    # Get the medoid points in the original scale
    medoid_points_original_scale = scaler.inverse_transform(medoids)
    selected_systems = pd.DataFrame(medoid_points_original_scale, columns=objective_labels, index=selected_systems_names)

    return selected_systems

