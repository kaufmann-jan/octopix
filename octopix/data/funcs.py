#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Some handy list operation functions"""

def flatten(l):
    """Flatten a list of lists into a single list."""
    return [item for sublist in l for item in sublist]

def is_unique(l):
    """Check if all elements in the list are the same."""
    return l.count(l[0]) == len(l)

def listDiff(l1,l2):
    """Return elements in l2 that are not in l1."""
    return [x for x in set(l2) if x not in set(l1)]

def are_equal(l1,l2):
    """Check if two lists contain the same elements, regardless of order."""
    return (set(l1) == set(l2))

def getAllListItems(qlist):
    """Get all items from a QListWidget as a list of strings."""
    return [str(qlist.item(x).text()) for x in range(qlist.count())]

def getSelectedListItems(qlist):
    """Get selected items from a QListWidget as a list of strings."""
    return [ x.text() for x in qlist.selectedItems() ]

