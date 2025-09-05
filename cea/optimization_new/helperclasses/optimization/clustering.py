"""
This script is used to cluster buildings based on their geographical proximity. This clustering is based on the HDBSCAN
algorithm but also includes a subdivision into a gridded structure in case the clusters get too big.

This clustering should only be applied if the mutation and/or recombination operations on vector encoding network
connectivity require it.
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2023, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"

import networkx as nx
from sklearn.cluster import HDBSCAN
from community import community_louvain

class Clustering(object):
    _method = None

    def __init__(self, domain_network_graph:nx.Graph, min_samples:int=5, grid_size:float=300, subdivision_threshold:int=5):
        """
        :param domain_network_graph: graph of the thermal network connecting all buildings in the domain (nodes)
        :type domain_network_graph: nx.Graph
        :param min_samples: min_samples value for DBSCAN
        :type min_samples: int
        :param grid_size: size of the grid in meters
        :type grid_size: float
        :param subdivision_threshold: threshold for the number of points in a cluster before subdivision
        :type subdivision_threshold: int
        """
        self.domain_network_graph = domain_network_graph
        self.points = [point for point, data in dict(domain_network_graph.nodes(data=True)).items()
                       if data['label'] != 'connector']
        self.min_samples = min_samples
        self.grid_size = grid_size
        self.subdivision_threshold = subdivision_threshold
        self.cluster_indexes:list = []
        self.grid_cell_indexes:list = []

    def cluster(self):
        """
        Performs the clustering of the building centroids using the HDBSCAN algorithm or Louvain method for community
        detection.
        :return: list of cluster indexes
        """
        if Clustering._method == 'Louvain':
            communities = community_louvain.best_partition(self.domain_network_graph)
            self.cluster_indexes = self.derive_cluster_indexes(communities)
        elif Clustering._method == 'HDBSCAN':
            clustering_algorithm = HDBSCAN(min_samples=self.min_samples)
            clusters = clustering_algorithm.fit(self.points)
            self.cluster_indexes = list(clusters.labels_)
        else:
            raise ValueError(f"Clustering method {Clustering._method} not supported.")

        self.subdivide_with_grid()

        return self.cluster_indexes

    def derive_cluster_indexes(self, communities:dict):
        """
        Derive cluster indexes from the communities dictionary.
        :param communities: dictionary of communities
        :type communities: dict
        :return: list of cluster indexes
        """
        # Extract community indexes of the building nodes
        building_community_indexes = [communities[node]
                                      for node ,data in dict(self.domain_network_graph.nodes(data=True)).items()
                                      if data['label'] != 'connector']

        # Map community indexes to clusters and mark all buildings that are alone in their communities as outliers
        community_indexes = set(building_community_indexes)
        mapping = {}
        cluster_index = 1

        for i, index in enumerate(community_indexes):
            if building_community_indexes.count(index) > 1:
                mapping[index] = cluster_index
                cluster_index += 1

        cluster_indexes = [mapping[index] if index in mapping else -1 for index in building_community_indexes]

        return cluster_indexes

    def subdivide_with_grid(self):
        """
        Subdivides clusters if they are too large.
        :return: list of cluster indexes
        """
        if max(self.cluster_indexes) < 0 or self.area_small() or self.nbr_points_small():
           return self.cluster_indexes

        # assign points to grid cells
        self.grid_cell_indexes = self.points_to_grid()

        # subdivide clusters
        self.cluster_indexes = self.split_clusters()

        return self.cluster_indexes

    def area_small(self):
        """ Check if the area of the clusters is too small to do subdivision. """
        x_coordinates = [point[0] for point in self.points]
        y_coordinates = [point[1] for point in self.points]

        x_range = max(x_coordinates) - min(x_coordinates)
        y_range = max(y_coordinates) - min(y_coordinates)

        return x_range + y_range < 4 * self.grid_size

    def nbr_points_small(self):
        """ Check if the number of building centroids is too small to do subdivision. """

        return len(self.points) < 4 * self.subdivision_threshold

    def points_to_grid(self):
        """
        Assigns the clustering points to their grid cell indexes.
        """
        # determine min and max values of x and y coordinates
        x_coords = [point[0] for point in self.points]
        y_coords = [point[1] for point in self.points]
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)

        # calculate number of grid cells in x and y direction
        x_cells = int((x_max - x_min) / self.grid_size) + 1
        y_cells = int((y_max - y_min) / self.grid_size) + 1

        # define origin of grid
        x_zero = x_min - (x_max - x_min) / (2 * x_cells)
        y_zero = y_min - (y_max - y_min) / (2 * y_cells)

        # create grid and assign points to grid cells
        grid_cell_indexes = []
        for point in self.points:
            x, y = point
            x_index = int((x - x_zero) / self.grid_size)
            y_index = int((y - y_zero) / self.grid_size)
            grid_cell_indexes.append((x_index, y_index))

        return grid_cell_indexes

    def split_clusters(self):
        """
        Split clusters if the number of points in a given grid cell exceeds the subdivision threshold.
        """
        # count points per subdivision (i.e. points in the same cluster and the same grid cell)
        points_per_subdivision = self.count_points_per_subdivision()

        # split up clusters around their most populous grid cell until none of them can be split up further
        nbr_clusters = len(points_per_subdivision.keys())
        unsplitable_clusters = [-1] if -1 in points_per_subdivision.keys() else []

        while len(unsplitable_clusters) < nbr_clusters:
            # determine which clusters have yet to be checked for splitting and...
            clusters_to_check = [cluster_index for cluster_index in points_per_subdivision.keys()
                                 if cluster_index not in unsplitable_clusters]
            # determine how many points they hold per grid subdivision
            points_per_subdivision = {cluster_index: points_per_grid_cell for cluster_index, points_per_grid_cell in
                                      points_per_subdivision.items() if cluster_index in clusters_to_check}

            # for each cluster, find the most dense grid cell and split the cluster around it
            for cluster_index in clusters_to_check:
                points_per_grid_cell = points_per_subdivision[cluster_index]
                most_dense_cell = max(points_per_grid_cell, key=points_per_grid_cell.get)

                # if the most dense cell does not surpass the threshold, do not subdivide...
                if points_per_grid_cell[most_dense_cell] < self.subdivision_threshold:
                    unsplitable_clusters.append(cluster_index)
                else:
                    # if it does, split the cluster towards the side that holds the most points (N, S, E or W)
                    new_cluster_index = self.split_off_new_cluster(cluster_index, most_dense_cell, points_per_subdivision)
                    # and recount the points per subdivision for the new cluster
                    points_per_subdivision = self.recount_points_after_division(cluster_index, new_cluster_index,
                                                                                points_per_subdivision)
                    # if the new cluster has been added successfully, break off the for loop and start anew
                    if len(points_per_subdivision.keys()) > nbr_clusters:
                        nbr_clusters = len(points_per_subdivision.keys())
                        break
                    else:
                        # in the cases where the cluster could not be split (e.g. none of the sides had enough points)
                        # add the cluster to the list of unsplitable clusters
                        unsplitable_clusters.append(cluster_index)

        return self.cluster_indexes

    def count_points_per_subdivision(self):
        """
        Identify in which grid cells the cluster points are located and how many points from each cluster each
        grid cell contains
        """
        points_per_subdivision = {}
        for i, cluster_index in enumerate(self.cluster_indexes):
            grid_cell_index = self.grid_cell_indexes[i]
            if cluster_index not in points_per_subdivision:
                points_per_subdivision[cluster_index] = {}
            if grid_cell_index not in points_per_subdivision[cluster_index]:
                points_per_subdivision[cluster_index][grid_cell_index] = 0
            points_per_subdivision[cluster_index][grid_cell_index] += 1

        return points_per_subdivision

    def split_off_new_cluster(self, cluster_index:int, on_grid_cell_index:tuple, points_per_subdivision:dict):
        """
        Splits a cluster into two clusters around the grid cell with the most points.
        """
        # count the sum of all points to the north, east, south and west of the most populous grid cell respectively
        # and store the grid cell indexes of these cells
        nbr_points = {'north': 0, 'east': 0, 'south': 0, 'west': 0}
        cell_indexes = {'north': [], 'east': [], 'south': [], 'west': []}

        for grid_cell_index, points in points_per_subdivision[cluster_index].items():
            if grid_cell_index == on_grid_cell_index:
                continue
            if grid_cell_index[1] > on_grid_cell_index[1]:
                nbr_points['north'] += points
                cell_indexes['north'].append(grid_cell_index)
            if grid_cell_index[0] > on_grid_cell_index[0]:
                nbr_points['east'] += points
                cell_indexes['east'].append(grid_cell_index)
            if grid_cell_index[1] < on_grid_cell_index[1]:
                nbr_points['south'] += points
                cell_indexes['south'].append(grid_cell_index)
            if grid_cell_index[0] < on_grid_cell_index[0]:
                nbr_points['west'] += points
                cell_indexes['west'].append(grid_cell_index)

        # split the cluster towards the direction with the most points
        if all([nbr < self.subdivision_threshold for nbr in nbr_points.values()]):
            return None
        else:
            direction = max(nbr_points.keys(), key=(lambda key: nbr_points[key]))
            new_cluster_index = max(self.cluster_indexes) + 1
            for cell_index in cell_indexes[direction]:
                self.cluster_indexes = [new_cluster_index
                                        if self.grid_cell_indexes[i] == cell_index
                                           and self.cluster_indexes[i] == cluster_index
                                        else c_id
                                        for i, c_id in enumerate(self.cluster_indexes)]

        return new_cluster_index

    def recount_points_after_division(self, old_cluster:int, new_cluster:int, points_per_subdivision:dict):
        """
        Recounts the points per subdivision after a cluster has been split.
        """
        if not new_cluster:
            return points_per_subdivision

        points_per_subdivision[new_cluster] = {}
        relevant_grid_cells = list(points_per_subdivision[old_cluster].keys())

        for grid_cell_index in relevant_grid_cells:
            points_in_new_cluster = [cell_index for i, cell_index in enumerate(self.grid_cell_indexes)
                                     if self.cluster_indexes[i] == new_cluster].count(grid_cell_index)
            if points_in_new_cluster > 0:
                points_per_subdivision[new_cluster][grid_cell_index] = points_in_new_cluster
                del points_per_subdivision[old_cluster][grid_cell_index]

        return points_per_subdivision

    @staticmethod
    def initialize_class_variables(domain):
        """
        Initializes the class variables that are used to store the cluster indexes and grid cell indexes.
        """
        Clustering._method = domain.config.optimization_new.building_clustering_method

