#!/usr/bin/env python3
# -*- coding: utf-8 -*-*-

import time
from pathlib import Path

from octopix.common.config import supported_post_types
from octopix.data.scanner import find_all_OF_ppObjects
from octopost.reader import makeRuntimeSelectableReader


class Simulation(object):
    
    def ppo_to_cont(self,ppo):
        """Convert to the Simulation data structure:
        
        from 
            {data_type1: [list of data_files], 
            ..., 
            data_typeN, [list of data_files]}
        to
            {data_type1: { data_file1 : None, ..., data_fileN: None},
            ...,
            data_typeN: { data_file1 : None, ..., data_fileN: None}
        """
        return {post_type:{post_file:None for post_file in post_files} for post_type,post_files in ppo.items()}
    
    def representationName(self):
        """Return the representation Name.
        If self.name is not defined, it is just the name of 
        the simulation directory.  
        """
        if self.name:
            return self.name
        else:
            return str(self.location.stem)
    
    
    def scan(self,verbose=False):
        
        ppo = self.ppo_to_cont(find_all_OF_ppObjects(supported_types=supported_post_types, working_dir=self.location))

        # if there is some post data found:
        if ppo:
            # if the container is empty, i.e not yet initialized, we can just assign ppo
            if not self.container:
                if verbose: print('init the container')
                self.container = ppo
    
            # if the file structure on the disk has changed, i.e. the ppo keys do not match the container keys, we need to update.
            # we assume, that if there is as difference, that means always new created files, but never deleted files. With one 
            # exception: in case the complete simulation is deleted. But this is accounted for with the check of emptyness of the
            
            elif ([v.keys() for v in ppo.values()] != [v.keys()for v in self.container.values()]):
                if verbose: print('updating')
                ppo.update(self.container)
                self.container = ppo
            else:
                if verbose: print('no action required')
            
        else:
            if verbose: print('no data found')
            self.container = {}
            
    
    def __init__(self,location=Path.cwd(),name=None):
        
        self.location = Path(location).absolute()

        self.name = name

        self.container = {}

        self.scan()
            

    def load_data_readers(self,data_dict,verbose=False):
        """
        
        Parameter
        ---------
        
        data_dict : dict
            dictionary with key = data_type, e.g. forces, residuals, etc.
            and value the data file(s). Can be eiter a str or [str, str] with the name 
            of the data files.
        
        """
        self.scan(verbose)

        for data_type in data_dict.keys():
            if isinstance(data_dict[data_type],str):
                data_dict[data_type] = [data_dict[data_type]]
                
            for data_file in data_dict[data_type]:
                if self.container[data_type][data_file] is None: 
                    reader = makeRuntimeSelectableReader(reader_name=data_type, base_dir=data_file, case_dir=self.location)
                    self.container[data_type][data_file] = reader


    def get_data(self,data_type,data_files=None):
        """
        
        this loads and gets, as reader.get_data() (re)loads and returns the data 
        
        Parameter
        ---------
        
        data_type : str
            name of the data type, e.g 'forces'
        data_files : str of list(str)
            name(s) of the data files. If not given, i.e. None return all data files
            for given data type
        """
        
        if isinstance(data_files, str):
            return self.container[data_type][data_files].get_data()
        elif isinstance(data_files, list):
            return [self.container[data_type][data_file].get_data() for data_file in data_files]
        elif not data_files:
            print('returning all data_files for data_type',data_type)
            
            return [x.get_data() for x in list(self.container[data_type].values()) ]
        else:
            raise TypeError
        
    def data_types(self):
        return list(self.container.keys())
    
    def data_files(self,data_type):  
        return list(self.container[data_type].keys())

def main():
    
    s = Simulation()

    print(s.container)
    print(s.data_types())
    print(s.data_files('forces'))
    
    # instantiate all reader for the simulation
    for data_type in s.data_types():
        s.load_data_readers({data_type:s.data_files(data_type)})
        
    count = 0
    while False:
        print(count)
        if count == 1:
            print(s.get_data('forces', 'forces'))
        elif count == 2:
            s.get_data('residuals')
        
        elif count == 4:
            s.get_data('residuals')    
    
        elif count == 6:
            s.get_data('residuals')
        
        elif count == 10:
            break

        count += 1
        time.sleep(1)

    for data_type in s.data_types():
        print(s.get_data(data_type))

    if True:
        import matplotlib.pyplot as plt
        
        df = s.get_data('residuals')[0]
        fig, ax = plt.subplots()
        plt.plot(df.time,df.loc[:, df.columns != 'time'])
        plt.semilogy()
        plt.grid()
        plt.show()
    
    
    

if __name__ == '__main__':
    main()
