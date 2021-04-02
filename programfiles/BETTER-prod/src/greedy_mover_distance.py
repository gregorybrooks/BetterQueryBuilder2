import numpy as np
from sklearn import metrics

def pairwise_euclidean_dists(x, y):  
    return metrics.pairwise_distances(x, y, metric='euclidean')

def pairwise_cosine_dists(x, y):  
    return metrics.pairwise_distances(x, y, metric='cosine')


def greedy_mover_distance(doc_s,doc_t,weight_s,weight_t):
    doc_s = np.array(doc_s)
    doc_t = np.array(doc_t)

    A = pairwise_euclidean_dists(doc_s,doc_t)

    dict_pairs = dict(np.ndenumerate(A))
    pairs = {h: v for h, v in sorted(dict_pairs.items(), key=lambda item: item[1])}

    distance = 0.0
    for pair in pairs:
        sent_s = pair[0]
        sent_t = pair[1]
        flow = min(weight_s[sent_s],weight_t[sent_t])
        weight_s[sent_s] = weight_s[sent_s]-flow
        weight_t[sent_t] = weight_t[sent_t]-flow
        distance = distance + flow * pairs[pair]
    return distance

