#!/usr/bin/env python3
# -*- coding: utf-8 -*-*-

import time
from pathlib import Path

from octopix.common.config import supported_post_types
from octopix.data.scanner import findAllOFppObjects
from octopix.data.reader import makeRuntimeSelectableReader


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
        
        ppo = self.ppo_to_cont(findAllOFppObjects(supported_types=supported_post_types, working_dir=self.location))

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
        
        self.location = Path(location)

        self.name = name

        self.container = {}

        self.scan()
            

    def load_data(self,data_dict,verbose=False):
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
                reader = makeRuntimeSelectableReader(reader_name=data_type, file_name=data_file, case_dir=self.location)
        
                self.container[data_type][data_file] = reader.data

    def get_data(self,data_type,data_files=None):
        """
        Parameter
        ---------
        
        data_type : str
            name of the data type, e.g 'forces'
        data_files : str of list(str)
            name(s) of the data files. If not given, i.e. None return all data files
            for given data type
        """
        
        if isinstance(data_files, str):
            return self.container[data_type][data_files]
        elif isinstance(data_files, list):
            return [self.container[data_type][data_file] for data_file in data_files]
        elif not data_files:
            print('returning all data_files for data_type',data_type)
            return list(self.container[data_type].values())
        else:
            raise TypeError
        
    def data_types(self):
        return list(self.container.keys())
    
    def data_files(self,data_type):  
        return list(self.container[data_type].keys())

def main():
    
    s = Simulation()

    count = 0
    while False:
        print(count)
        if count == 1:
            s.load_data({'forces':'forces'})
            print(s.get_data('forces', 'forces'))
        elif count == 2:
            s.load_data({'residuals':['residuals']})
        elif count == 3:
            s.load_data({'forces':['forces','f_DTC']})
            print(s.get_data('forces',['forces','f_DTC']))
        elif count == 4:
            break
        
        count += 1
        time.sleep(0.1)

    #s.load_data({'forces':'forces'})
    
    if True:
        
        s.load_data({'residuals':'residuals'})    
        df = s.get_data('residuals','residuals')
        print(df)
        
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots()
        plt.plot(df.time,df.loc[:, df.columns != 'time'])
        plt.semilogy()
        plt.grid()
        plt.show()
    
    
    

if __name__ == '__main__':
    main()