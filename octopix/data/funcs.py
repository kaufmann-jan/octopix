#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Some handy list operation functions"""

def flatten(l):
    return [item for sublist in l for item in sublist]

def is_unique(l):
    return l.count(l[0]) == len(l)

def listDiff(l1,l2):
    return [x for x in set(l2) if x not in set(l1)]

def are_equal(l1,l2):
    return (set(l1) == set(l2))

def getAllListItems(qlist):
    return [str(qlist.item(x).text()) for x in range(qlist.count())]

def getSelectedListItems(qlist):
    return [ x.text() for x in qlist.selectedItems() ]


def prepare_data(df, time_start=0.0, data_subset=None):
    if data_subset is None:
        data_subset = []

    if time_start > 0.0:
        df = df.loc[df.time >= time_start]

    df.set_index('time', drop=True, inplace=True)

    if len(data_subset) > 0:
        df = df[df.columns.intersection(data_subset)]

    return df
