#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def getAllListItems(qlist):
    return [str(qlist.item(x).text()) for x in range(qlist.count())]


def getSelectedListItems(qlist):
    return [ x.text() for x in qlist.selectedItems() ]