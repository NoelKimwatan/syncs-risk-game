"""
A script to compute the odds of the attacker winning a RISK battle, defined as the attacker probability of the
attacker successfully capturing territory, given a set number of attackers and defenders.

30/08/2020
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def compute(M, N, store, P_dict):
    """Recursively computes the probability of the attacker winning, given M attackers and N defenders"""

    # P_dict stores the probabilities involved in the basic rolls
    # store is an M by N array, used to store previous results in dynamic programming style

    # if a given matchup is known, get the result from store
    if store[M, N]:
        return store[M, N]

    # if no attackers or defenders are left, the result is immediately known
    elif M == 0 and N > 0:
        store[M, N] = 0
        return 0

    elif M > 0 and N == 0:
        store[M, N] = 1
        return 1

    # for all other matchups, recursively compute the probability
    # extract the probability a given event occuring from P_dict

    # for a matchup where attackers >= 3 and defenders >= 2...
    elif M >= 3 and N >= 2:
        # get the P of attacker winning after losing both battles after the first roll
        T1 = compute(M - 2, N, store, P_dict)
        # if this result is not known, store it
        if not store[M - 2, N]:
            store[M - 2, N] = T1
        # get the P of attacker winning after both sides lose one battle each
        T2 = compute(M - 1, N - 1, store, P_dict)
        if not store[M - 1, N - 1]:
            store[M - 1, N - 1] = T2
        # get the P of attacker winning after winning both battles after the first roll
        T3 = compute(M, N - 2, store, P_dict)
        if not store[M, N - 2]:
            store[M, N - 2] = T3
        # compute the sum of terms, weighted by the P of each initial event occurring
        return P_dict[(3, 2)][2] * T1 + P_dict[(3, 2)][1] * T2 + P_dict[(3, 2)][0] * T3

    # similarly for all other matchups...

    elif M >= 3 and N == 1:
        T1 = compute(M - 1, 1, store, P_dict)
        if not store[M - 1, 1]:
            store[M - 1, 1] = T1
        if not store[M, 0]:
            store[M, 0] = 1
        return P_dict[(3, 1)][1] * T1 + P_dict[(3, 1)][0]

    elif M == 2 and N == 1:
        T1 = compute(1, 1, store, P_dict)
        if not store[1, 1]:
            store[1, 1] = T1
        if not store[2, 0]:
            store[2, 0] = 1
        return P_dict[(2, 1)][1] * T1 + P_dict[(2, 1)][0]

    elif M == 2 and N >= 2:
        if not store[0, N]:
            store[0, N] = 0
        T1 = compute(1, N - 1, store, P_dict)
        if not store[1, N - 1]:
            store[1, N - 1] = T1
        T2 = compute(2, N - 2, store, P_dict)
        if not store[2, N - 2]:
            store[2, N - 2] = T2
        return P_dict[(2, 2)][0] * T2 + P_dict[(2, 2)][1] * T1

    elif M == 1 and N == 1:
        if not store[0, 1]:
            store[0, 1] = 0
        if not store[1, 0]:
            store[1, 0] = 1
        return P_dict[(1, 1)][0]

    elif M == 1 and N >= 2:
        if not store[0, N]:
            store[0, N] = 0
        T1 = compute(1, N - 1, store, P_dict)
        if not store[1, N - 1]:
            store[1, N - 1] = T1
        return P_dict[(1, 2)][0] * T1


def simulate(max_val, P_dict):
    """Iterate through all possible pairs store the results. Returns a numpy array containing the probabilities"""

    # max_val is the largest number of attackers and defenders considered
    store = np.zeros((max_val + 1, max_val + 1))
    for i in range(0, max_val + 1):
        for j in range(0, max_val + 1):
            result = compute(i, j, store, P_dict)
            store[i, j] = result

    return store


def make_table(store):
    """Creates a probability surface and a nice table to showcase the data"""

    # round the probabilites, and drop the first row and column, which correspond to the trivial case
    store = np.round_(store, 3)
    store = np.delete(store, [0], axis=0)
    store = np.delete(store, [0], axis=1)
    dim = store.shape[0]

    # create mesh grid and then plot a probability surface
    x = range(1, dim + 1)
    y = range(1, dim + 1)
    X, Y = np.meshgrid(x, y)

    fig = plt.figure()
    ax = Axes3D(fig)
    ax.plot_surface(X, Y, store, rstride=1, cstride=1, cmap='hot')
    plt.ylabel('No. of Attackers')
    plt.xlabel('No. of Defenders')
    graph_label = 'RISK probability surface'
    plt.title(graph_label)

    plt.show()

    # create a nice table to showcase the data
    colors = plt.get_cmap('Reds')(np.linspace(0, 0.5, dim + 1))
    table = plt.table(cellText=store, loc=(0, 0), cellLoc='center', rowLabels=x, colLabels=y, rowColours=colors,
                      colColours=colors)

    tab_properties = table.properties()['children']

    for cell in tab_properties:
        cell.set_height(1.0 / (dim + 1))
        cell.set_width(1.0 / (dim + 1))

    plt.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
    plt.tick_params(axis='y', which='both', right=False, left=False, labelleft=False)

    for pos in ['right', 'top', 'bottom', 'left']:
        plt.gca().spines[pos].set_visible(False)

    ax.set_xticks([])
    ax.set_yticks([])
    plt.xlabel('No. of Defenders')
    plt.ylabel('No. of Attackers')

    table_label = 'RISK probability matrix'
    table_label_2 = 'Data represents the probability of the attacker gaining territory'

    plt.suptitle(table_label, fontsize=16)
    plt.title(table_label_2, fontsize=7)
    plt.show()


if __name__ == '__main__':
    # P_dict can be computed using basic_rolls.py
    # the first key (1, 1), has value P of attacker winning i.e. (1, 1) -> (1, 0) being 0.416 and
    # defender winning i.e. (1, 1) -> (0, 1) being 0.584
    # the second key (2, 1) has value P of attacker winning i.e. (2, 1) -> (2, 0) being 0.579 and
    # defender winning i.e. (2, 1) -> (1, 1) being 0.423
    # the final key (3, 2) has value P of attacker winning i.e. (3, 2) -> (3, 0) being 0.371, a value P
    # of a draw i.e. (3, 2) -> (2, 1) being 0.336 and defender winning i.e. (3, 2) -> (1, 2) being 0.293
    P_dict = {(1, 1): [0.416355, 0.583645], (2, 1): [0.578681, 0.421319], (3, 1): [0.65982, 0.34018],
              (1, 2): [0.253999, 0.746001], (2, 2): [0.22794, 0.323617, 0.448443],
              (3, 2): [0.370976, 0.335948, 0.293076]}

    # generate the numpy array containing probabilities
    matrix = simulate(max_val=20, P_dict=P_dict)  # compute for up to max_val vs max_val
    # draw a table
    make_table(matrix)