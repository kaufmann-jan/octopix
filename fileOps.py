#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

import sys
sys.path.insert(0, "/home/jan/workspace/MOFA/python")
from dataProcessing import fileIO 


def flatten(l):
    
    return [item for sublist in l for item in sublist]


def is_unique(l):
    
    return l.count(l[0]) == len(l)


def get_pdirs(working_dir=Path.cwd()):
    
    return [p.name for p in Path(working_dir/"postProcessing").glob('*')]


def get_tdirs(pdir):
    
    return list(Path(Path.cwd()/"postProcessing"/pdir).glob('[0-9]*'))


def get_ddirs(tdirs):
    
    t = flatten([list(p.glob('*.dat')) for p in tdirs])
    return [p.name for p in t]


def listDiff(l1,l2):
    
    diff = [x for x in set(l2) if x not in set(l1)]
    return diff


def are_equal(l1,l2):
    return (set(l1) == set(l2))

def findAllOFPostProcObjects(working_dir=Path.cwd()):
    
    ppObjects = {}
    for key in get_pdirs(working_dir=working_dir):
        dat_files = get_ddirs(get_tdirs(key))
        if is_unique(dat_files):
            ppObjects[key] = Path(dat_files[0]).stem
        
    return ppObjects    
    

def findAllOFppObjects(supported_types,working_dir=Path.cwd()):
    
    ppObjects = {k:[] for k in supported_types}
    
    for val in get_pdirs(working_dir=working_dir):
        dat_files = get_ddirs(get_tdirs(val))
        if is_unique(dat_files):
            try:
                ppObjects[Path(dat_files[0]).stem].append(val)
            except:
                pass
    
    ppObjects = {k:v for (k,v) in ppObjects.items() if len(v) > 0}
    #ppObjects = {k:sorted(v,reverse=True) for (k,v) in ppObjects.items()}
    ppObjects = {k:sorted(v,key=lambda x: x.replace('_','{')) for (k,v) in ppObjects.items()}
        
    return ppObjects


def main():
    
    supported_post_types = ['residuals','forces','rigidBodyState','time','fieldMinMax']
    ppObjects = findAllOFppObjects(supported_post_types)
    
    #ppObjects = findAllOFPostProcObjects()
    print(list(ppObjects.keys()))
    print(list(ppObjects.values()))
        
    comboItems = []
    currentItems = ['forces','residuals']
    comboItems += listDiff(comboItems,currentItems)
    print(comboItems)
    
    currentItems = ['forces','residuals','foo']
    comboItems += listDiff(comboItems,currentItems)
    print(comboItems)

if __name__ == '__main__':
    main()