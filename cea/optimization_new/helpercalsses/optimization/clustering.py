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


from sklearn.cluster import HDBSCAN

class Clustering(object):

    def __init__(self, building_centroids:list, min_samples:int=5, grid_size:float=300, subdivision_threshold:int=10):
        """
        :param building_centroids: list of building centroids
        :type building_centroids: list of shapely.geometry.point.Point objects
        :param min_samples: min_samples value for DBSCAN
        :type min_samples: int
        :param grid_size: size of the grid in meters
        :type grid_size: float
        :param subdivision_threshold: threshold for the number of points in a cluster before subdivision
        :type subdivision_threshold: int
        """
        self.points = [(point.x, point.y) for point in building_centroids]
        self.min_samples = min_samples
        self.grid_size = grid_size
        self.subdivision_threshold = subdivision_threshold
        self.cluster_indexes:list = []
        self.grid_cell_indexes:list = []

    def cluster(self):
        """
        Performs the clustering of the building centroids using the HDBSCAN algorithm.
        :return: list of cluster indexes
        """
        clustering_algorithm = HDBSCAN(min_samples=self.min_samples)
        clusters = clustering_algorithm.fit(self.points)
        self.cluster_indexes = list(clusters.labels_)
        self.subdivide_with_grid()
        return self.cluster_indexes

    def subdivide_with_grid(self):
        """
        Subdivides clusters if they are too large.
        :return: list of cluster indexes
        """
        if max(self.cluster_indexes) < 0 or self.area_small or self.number_of_small:
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

    def number_of_small(self):
        """ Check if the number of clusters is too small to do subdivision. """

        return len(self.points) < 10 * self.subdivision_threshold

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

        # split up clusters around their most populous grid cell if the latter surpasses the chosen threshold
        for cluster_index, points_per_grid_cell in points_per_subdivision.items():
            most_dense_cell = max(points_per_grid_cell.keys(), key=(lambda key: points_per_subdivision[-1][key]))

            # if the most dense cell does not surpass the threshold, do not subdivide
            if points_per_grid_cell[most_dense_cell] < self.subdivision_threshold:
                continue
            else:
                new_cluster_index = self.split_off_new_cluster(cluster_index, most_dense_cell, points_per_subdivision)
                self.recount_points_after_division(cluster_index, new_cluster_index, )

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
                self.cluster_indexes[self.grid_cell_indexes == cell_index] = new_cluster_index

        return new_cluster_index

    def recount_points_after_division(self, old_cluster:int, new_cluster:int, points_per_subdivion:dict):
        """
        Recounts the points per subdivision after a cluster has been split.
        """
        points_per_subdivion[new_cluster] = {}
        relevant_grid_cells = list(points_per_subdivion[old_cluster].keys())

        for grid_cell_index in relevant_grid_cells:
            points_in_new_cluster = self.grid_cell_indexes[self.cluster_indexes == new_cluster].count(grid_cell_index)
            if points_in_new_cluster > 0:
                points_per_subdivion[new_cluster][grid_cell_index] = points_in_new_cluster
                del points_per_subdivion[old_cluster][grid_cell_index]

        return points_per_subdivion

