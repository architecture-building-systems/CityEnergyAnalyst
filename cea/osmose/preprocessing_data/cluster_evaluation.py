import numpy as np
import pandas as pd
import os
import cea.osmose.settings as settings
from scipy.spatial.distance import euclidean, cdist, pdist, squareform
from cea.osmose.extract_demand_outputs import path_to_typical_days_files
import matplotlib.pyplot as plt
import seaborn as sns


def main():
    for case in settings.cases:
        # get results from all k
        paths_to_k_folders = path_to_typical_days_folders(case)
        dbi_all, T_ELDC_all, w_ELDC_all, GI_ELDC_all, ppl_ELDC_all  = {}, {}, {}, {}, {}
        # evaluation for each k
        for path in paths_to_k_folders:
            print path
            # original data
            X = pd.read_csv(path_to_typical_days_files(path, 'X'), header=None)
            # cluster labels
            y = pd.read_csv(path_to_typical_days_files(path, 'label'), header=None)
            day_count = pd.read_csv(path_to_typical_days_files(path, 'day_count'))

            # DBI
            dbi, k = db_index(X.values, y.values, day_count)
            dbi_all[k] = dbi

            # ELDC (Errors in Load Duration Curves)
            T_LDC_X, w_LDC_X, GI_LDC_X, ppl_LDC_X = get_LDC_from_X(X)
            T_LDC_K, w_LDC_K, GI_LDC_K, ppl_LDC_K = get_LDC_from_K(X, day_count)
            T_ELDC_all[k] = calculate_ELDC(T_LDC_K, T_LDC_X)
            w_ELDC_all[k] = calculate_ELDC(w_LDC_K, w_LDC_X)
            GI_ELDC_all[k] = calculate_ELDC(GI_LDC_K, GI_LDC_X)
            ppl_ELDC_all[k] = calculate_ELDC(GI_LDC_K, GI_LDC_X)

            # Calendar view
            plot_clusters_in_calendar_view(path, y, k)

        # plot DBI
        plot_evaluation_for_all_k(dbi_all, 'dbi', path)
        ELDC_dict = {'T': T_ELDC_all, 'w': w_ELDC_all, 'GI': GI_ELDC_all, 'occ': ppl_ELDC_all}
        plot_ELDC_for_all_k(ELDC_dict, path)


def plot_evaluation_for_all_k(dbi_all, name, path):
    fig, ax = plt.subplots()
    ax.plot(dbi_all.keys(), dbi_all.values())
    ax.set_title(name, fontsize=16)
    ax.set_xlabel('number of clusters', fontsize=16)
    folder = os.path.dirname(path)
    fig.savefig(os.path.join(folder, '%s.png' %name), bbox_inches="tight")
    return


def plot_ELDC_for_all_k(ELDC_dict, path):
    fig, ax = plt.subplots()
    x = ELDC_dict['T'].keys()
    line1, = ax.plot(x, ELDC_dict['T'].values(), label='T')
    line2, = ax.plot(x, ELDC_dict['w'].values(), label='w')
    line3, = ax.plot(x, ELDC_dict['GI'].values(), label='GI')
    line4, = ax.plot(x, ELDC_dict['occ'].values(), label='occ')
    ax.set_title('ELDC', fontsize=16)
    ax.set_xlabel('number of clusters', fontsize=16)
    ax.set_ylabel('error', fontsize=16)
    ax.xaxis.label.set_size(16)
    ax.yaxis.label.set_size(16)
    folder = os.path.dirname(path)
    ax.legend()
    fig.savefig(os.path.join(folder, 'ELDC.png'), bbox_inches="tight")
    return


def calculate_ELDC(K_list, X_list):
    nom = (abs(np.asarray(X_list) - np.asarray(K_list)).sum())
    denom = sum(X_list)
    error = nom/denom
    return error


def get_LDC_from_X(X):
    T_X = X.iloc[:, 0:24]
    T_LDC_X_array = df_to_sorted_array(T_X)
    w_X = X.iloc[:, 24:48]
    w_LDC_X_array = df_to_sorted_array(w_X)
    GI_X = X.iloc[:, 48:72]
    GI_LDC_X_array = df_to_sorted_array(GI_X)
    ppl_X = X.iloc[:, 72:96]
    ppl_LDC_X_array = df_to_sorted_array(ppl_X)
    return T_LDC_X_array, w_LDC_X_array, GI_LDC_X_array, ppl_LDC_X_array


def get_LDC_from_K(X, day_count):
    T_LDC_K, w_LDC_K, GI_LDC_K, ppl_LDC_K = [], [], [], []
    for ix, day in enumerate(day_count['day']):
        count = day_count['count'][ix]
        [T_LDC_K.extend(X.iloc[day - 1, 0:24]) for i in range(count)]
        [w_LDC_K.extend(X.iloc[day - 1, 24:48]) for i in range(count)]
        [GI_LDC_K.extend(X.iloc[day - 1, 48:72]) for i in range(count)]
        [ppl_LDC_K.extend(X.iloc[day - 1, 72:96]) for i in range(count)]
    T_LDC_K.sort(reverse=True)
    w_LDC_K.sort(reverse=True)
    GI_LDC_K.sort(reverse=True)
    ppl_LDC_K.sort(reverse=True)
    return T_LDC_K, w_LDC_K, GI_LDC_K, ppl_LDC_K


def df_to_sorted_array(df):
    array = []
    [array.extend(df.ix[row, :]) for row in df.index.values]
    array.sort(reverse=True)
    return array


def plot_clusters_in_calendar_view(path, y, k):
    calendar_views = []
    weeks = y.values.size / 7
    for week in range(weeks):
        calendar_views.append(y[week * 7:(week + 1) * 7][0].values)
    calendar_df = pd.DataFrame(calendar_views)
    plt.figure(figsize=(10.5, 26))
    # sns.set_context("paper", rc={"font.size": 18, "axes.titlesize": 18, "axes.labelsize": 18})
    sns.set_context("paper", font_scale=3)
    # cmap = sns.diverging_palette(220, 20, n=20, as_cmap=True)
    cmap = sns.color_palette("Spectral", k)
    ax = sns.heatmap(calendar_df, annot=True, annot_kws={"size": 18}, linewidth=0.5, cmap=cmap)
    # sns.palplot(sns.diverging_palette(128, 240, n=20))
    # ax = sns.heatmap(calendar_df, annot=True, linewidth=0.5,
    #             cmap=sns.diverging_palette(128, 240, as_cmap=True))
    # im = ax.collections[0]
    # rgba_values = im.cmap(im.norm(im.get_array()))
    # print('start',len(rgba_values))
    # for row in range(len(rgba_values)):
    #     print list(rgba_values[row])
    figure = ax.get_figure()
    figure.savefig(os.path.join(path, 'calendar.png'))


def db_index(X, y, day_count):
    """
    Davies-Bouldin index is an internal evaluation method for
    clustering algorithms. Lower values indicate tighter clusters that
    are better separated.
    """
    # get unique labels
    # if y.ndim == 2:
    #     y = np.argmax(axis=1)
    uniqlbls = np.unique(y)
    n = len(uniqlbls)  # number of clusters
    # n = day_count.shape[0]
    # pre-calculate centroid and sigma
    centroid_arr = np.empty((n, X.shape[1]))
    sigma_arr = np.empty((n, 1))
    dbi_arr = np.empty((n, n))
    mask_arr = np.invert(np.eye(n, dtype='bool'))
    for i, k in enumerate(uniqlbls):
        Xk = X[np.where(y == k)[0], ...]
        # Ak = np.mean(Xk, axis=0) # change to the medoid
        day_ix = day_count.loc[day_count['k'] == k]['day'].values[0]
        print(k, day_ix, Xk.shape[0])
        Ak = X[day_ix - 1, ...]
        centroid_arr[i, ...] = Ak
        sigma_arr[i, ...] = np.mean(cdist(Xk, Ak.reshape(1, -1)))
    # compute pairwise centroid distances, make diagonal elements non-zero
    centroid_pdist_arr = squareform(pdist(centroid_arr)) + np.eye(n)
    # compute pairwise sigma sums
    sigma_psum_arr = squareform(pdist(sigma_arr, lambda u, v: u + v))
    # divide
    dbi_arr = np.divide(sigma_psum_arr, centroid_pdist_arr)
    # get mean of max of off-diagonal elements
    dbi_arr = np.where(mask_arr, dbi_arr, 0)
    dbi = np.mean(np.max(dbi_arr, axis=1))
    return dbi, n


def path_to_typical_days_folders(case):
    """
    find files with _el.csv and return a list of paths
    :param building:
    :return:
    """
    # path_to_folder = PATH_TO_FOLDER + building
    path_to_typical_day_folder = os.path.join(settings.typical_days_path, case)
    all_files_in_path = os.listdir(path_to_typical_day_folder)
    path_to_folders = []
    for file in all_files_in_path:
        if 'k_' in file:
            path_to_folder = os.path.join(path_to_typical_day_folder, file)
            path_to_folders.append(path_to_folder)
    return path_to_folders


def path_to_typical_days_files(path, file_name):
    path_to_file = os.path.join(path, '%s.csv' % (file_name))
    return path_to_file


if __name__ == '__main__':
    main()
