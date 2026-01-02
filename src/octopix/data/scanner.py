#!/usr/bin/env python3
# -*- coding: utf-8 -*-*-

from pathlib import Path

from octopix.data.funcs import flatten,is_unique
from octopost.parsing import list_time_dirs
from octopix.common.config import supported_post_types

def get_pdirs(working_dir=Path.cwd()):
    
    return [p.name for p in Path(working_dir/"postProcessing").glob('*')]


def find_dat_files(tdirs):
    
    t = flatten([list(p.glob('*.dat')) for p in tdirs])

    return [p.name for p in t]
   

def find_all_OF_ppObjects(supported_types,working_dir=Path.cwd()):
    """
    Parses the postProcessing directory recursively in the given
    working directory for OpenFOAM's function object generated data files.
    
    Results are stored and returned with a dictionary.
    
    The dict-keys are the function object types, the dict-values the 
    list of corresponding data-files. E.g.
    
    {
        'residuals':['residuals'],
        'forces':['forces', 'force_patch1','force_onanotherPatch', ]
        'fieldMinMax':['minMaxPressure','minMaxSomeOtherField']
    }
     
    the dict-values (the lists with the data-files) are alphabetically sorted,
    with the "_" (underscore) put to the very end of the sort order. 
    
    
    Parameters
    ----------
    
    supported_types : list
        list of strings with the functionObject type names, which should be looked up. 
    working_dir : Path-like
        path to the postProcessing parents directory
    Returns
    -------
    
    dict 
     
    """
    ppObjects = {k:[] for k in supported_types}
    
    for val in get_pdirs(working_dir=working_dir):
        dat_files = find_dat_files(list_time_dirs(Path(working_dir,'postProcessing',val)))
        
        if dat_files and is_unique(dat_files):
            try:
                ppObjects[Path(dat_files[0]).stem].append(val)
            except: #??? not nice
                pass
      
    ppObjects = {k:v for (k,v) in ppObjects.items() if len(v) > 0}

    # special handling of rigidBodyState, as the rigidBodyState function object
    # writes to 
    # postProcessing/rigidBodyState/0/<6DoFObjectName>.dat
    # This is in oposite to the logic of all other (at least to my current knowledge)
    # function objects, which are writing to
    # postProcessing/<userDefinedOutputName>/0/<functionObjectType>.dat
        
    if 'rigidBodyState' in get_pdirs(working_dir):
        dat_files = find_dat_files(list_time_dirs(Path(working_dir,'postProcessing','rigidBodyState')))
        ppObjects['rigidBodyState'] = list(set(dat_files))
    
    #ppObjects = {k:sorted(v,reverse=True) for (k,v) in ppObjects.items()}
    # for sorting we replace the underscore with the bracket, as the bracket is at the end of the sorting order
    # therefore all file names containing an underscore a put to the end
    # Usefull for e.g.
    # forces
    # forces_aft
    # forces_bow
       
    ppObjects = {k:sorted(v,key=lambda x: x.replace('_','{')) for (k,v) in ppObjects.items()}
        
    return ppObjects


class OFppScanner(object):
    
    def __init__(self,supported_types,working_dir=Path.cwd()):
        
        self.supported_types = supported_types
        self.working_dir = working_dir
        
        self.scan()
    
    def scan(self,working_dir=Path.cwd()):
        
        self.working_dir = working_dir
        
        self.ppObjects = find_all_OF_ppObjects(self.supported_types, self.working_dir)
        self.post_types = list(self.ppObjects.keys())


def main():
    
    ppObjects = find_all_OF_ppObjects(supported_post_types)
    print(ppObjects)

if __name__ == '__main__':
    main()
