#!/usr/bin/env python3
# -*- coding: utf-8 -*-*-

from pathlib import Path
from octopix.data.funcs import flatten,is_unique

def get_pdirs(working_dir=Path.cwd()):
    
    return [p.name for p in Path(working_dir/"postProcessing").glob('*')]


def get_tdirs(pdir):
    
    return list(Path(Path.cwd()/"postProcessing"/pdir).glob('[0-9]*'))


def get_ddirs(tdirs):
    
    t = flatten([list(p.glob('*.dat')) for p in tdirs])
    return [p.name for p in t]
   

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
    
    if 'rigidBodyState' in get_pdirs(working_dir):
        
        ppObjects['rigidBodyState'] = get_ddirs(get_tdirs('rigidBodyState')) 
    
    #ppObjects = {k:sorted(v,reverse=True) for (k,v) in ppObjects.items()}
    ppObjects = {k:sorted(v,key=lambda x: x.replace('_','{')) for (k,v) in ppObjects.items()}
        
    return ppObjects

class OFppScanner(object):
    
    def __init__(self,supported_types,working_dir=Path.cwd()):
        
        self.supported_types = supported_types
        self.working_dir = working_dir
        
        self.scan()
    
    def scan(self):
        
        self.ppObjects = findAllOFppObjects(self.supported_types, self.working_dir)
        self.post_types = list(self.ppObjects.keys())



def main():
    
    supported_post_types = ['residuals','forces','rigidBodyState','time','fieldMinMax']
    ppObjects = findAllOFppObjects(supported_post_types)
    print(ppObjects)

if __name__ == '__main__':
    main()