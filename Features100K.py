import numpy as np
import pandas as pd
import matplotlib as plt
import networkx as nx
import itertools
from collections import Counter
import metrics
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import OneHotEncoder


def convert_categorical(df_X, _X):
    values = np.array(df_X[_X])
    # integer encode
    label_encoder = LabelEncoder()
    integer_encoded = label_encoder.fit_transform(values)
    # binary encode
    onehot_encoder = OneHotEncoder(sparse=False)
    integer_encoded = integer_encoded.reshape(len(integer_encoded), 1)
    onehot_encoded = onehot_encoder.fit_transform(integer_encoded)
    df_X = df_X.drop(columns=_X)
    for j in range(integer_encoded.max() + 1):
        df_X.insert(loc=j + 1,
                    column=str(_X) + str(j + 1),
                    value=onehot_encoded[:, j])
    return df_X


def load_data(dataPath):
    df = pd.read_csv(dataPath + 'ua.base',
                     sep='\\t',
                     engine='python',
                     names=['UID', 'MID', 'rate', 'time'])
    df_user = pd.read_csv(dataPath + 'u.user',
                          sep='\\|',
                          engine='python',
                          names=['UID', 'age', 'gender', 'job', 'zip'])

    df_user = convert_categorical(df_user, 'job')
    df_user = convert_categorical(df_user, 'gender')
    df_user['bin'] = pd.cut(df_user['age'], [0, 10, 20, 30, 40, 50, 100],
                            labels=['1', '2', '3', '4', '5', '6'])
    df_user['age'] = df_user['bin']

    df_user = df_user.drop(columns='bin')
    df_user = convert_categorical(df_user, 'age')
    df_user = df_user.drop(columns='zip')

    return df, df_user


def train_model(df, df_user):
    alpha_coefs = [0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045]

    for alpha_coef in alpha_coefs:
        pairs = []
        grouped = df.groupby(['MID', 'rate'])

        for key, group in grouped:
            pairs.extend(list(itertools.combinations(group['UID'], 2)))

        counter = Counter(pairs)
        alpha = alpha_coef * 1682  # param*i_no
        edge_list = map(
            list,
            Counter(el for el in counter.elements()
                    if counter[el] >= alpha).keys())
        G = nx.Graph()

        for el in edge_list:
            G.add_edge(el[0], el[1], weight=1)
            G.add_edge(el[0], el[0], weight=1)
            G.add_edge(el[1], el[1], weight=1)

        pr = nx.pagerank(G.to_directed())
        df_user['PR'] = df_user['UID'].map(pr)
        df_user['PR'] /= float(df_user['PR'].max())
        dc = nx.degree_centrality(G)
        df_user['CD'] = df_user['UID'].map(dc)
        df_user['CD'] /= float(df_user['CD'].max())
        cc = nx.closeness_centrality(G)
        df_user['CC'] = df_user['UID'].map(cc)
        df_user['CC'] /= float(df_user['CC'].max())
        bc = nx.betweenness_centrality(G)
        df_user['CB'] = df_user['UID'].map(bc)
        df_user['CB'] /= float(df_user['CB'].max())
        lc = nx.load_centrality(G)
        df_user['LC'] = df_user['UID'].map(lc)
        df_user['LC'] /= float(df_user['LC'].max())
        nd = nx.average_neighbor_degree(G, weight='weight')
        df_user['AND'] = df_user['UID'].map(nd)
        df_user['AND'] /= float(df_user['AND'].max())
        X_train = df_user.loc[:, df_user.columns[1:]]
        X_train.fillna(0, inplace=True)

        X_train.to_pickle("data100k/x_train_alpha(" + str(alpha_coef) +
                          ").pkl")


dataPath = 'datasets/ml-100k/'

df, df_user = load_data(dataPath)

train_model(df, df_user)

# Evaluate the recommendations
k = 50
ground_truth = np.argsort(-test_r, axis=0)[:k, :].T.tolist()
recommended = np.argsort(-res, axis=0)[:k, :].T.tolist()
random = np.random.randint(0, n_m, (n_u, k)).T.tolist()

print("Baseline (random):\t", metrics.mapk(ground_truth, random, k=k),
      "\nGlocalK:\t\t", metrics.mapk(ground_truth, recommended, k=k))