#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from io import StringIO
#import os
from pathlib import Path
import sys
from datetime import datetime, timezone



def makeRuntimeSelectableReader(reader_name,file_name,case_dir):
    
    reader_name = "OpenFOAM{0:}".format(reader_name)
    
    #try:
    reader = getattr(sys.modules[__name__],reader_name)(base_dir=file_name,case_dir=case_dir)
#     except AttributeError as e:
#         if str(e).find("octopix.data.fileIO"):
#             if not str(e).find('None'):
#                 print('unknown reader',reader_name)    
#         else:
#             print(e)
#             
#         reader = OpenFOAMpostProcessing(base_dir=None, file_name=None, case_dir=None, names=None, usecols=None)        
    
    return reader


def prepare_data(df,time_start=0.0,data_subset=[]):
            
    if time_start > 0.0:
        df = df.loc[df.time >= time_start]
            
    df.set_index('time',drop=True,inplace=True)

    if len(data_subset) > 0:
        df = df[df.columns.intersection(data_subset)]
            
    return df


def parse_of(file_name,names,usecols=None):
    """Opens a text file, replaces all brackets with 
    whitespaces and returns a file stream.  
    """
    trantab = str.maketrans('()','  ')

    path = Path(file_name)

    with path.open('r') as f:
        fstream = StringIO(f.read().translate(trantab))
    
    df = pd.read_csv(fstream,delim_whitespace=True,header=None,names=names,comment='#',usecols=usecols)

    return df


def combine_oftime_files(base_dir,file_name,names,time_dirs=None,usecols=None):
    
    if time_dirs is None:
        time_dirs = list_time_dirs(base_dir)

    # As preparation for checking if loading of the data is necessary,
    # we can determine the latest modification time of all files located
    # under the base dir
    if False:
        mtime = np.amax([Path(base_dir,td,file_name).stat().st_mtime for td in time_dirs])
        print(base_dir,datetime.fromtimestamp(mtime, tz=timezone.utc))

    data = []

    for td in time_dirs:
        p = Path(base_dir,td,file_name) # os.path.join(base_dir,td,file_name)
        df = parse_of(p,names,usecols)
        data.append(df.set_index('time'))

    d = data[-1]
       
    if len(data) > 1:
        for i in reversed(data[:-1]):
            if i.index.array[-1] > d.index.array[-1]: 
                i = i[i.index < d.index.array[-1]]
            d = d.combine_first(i)
    
    return d

def list_time_dirs(path_to_time_dirs):
    
    return sorted([str(x.name) for x in Path(path_to_time_dirs).glob('[0-9]*')],key=float,reverse=False)

class OpenFOAMpostProcessing(object):

    def sort_fields(self):  
        try: 
            self.data = self.data.reindex(sorted(self.data.columns,key=lambda val: self.SORT_ORDER[val]),axis=1)
        except KeyError as e:
            print(e)

    def fields(self):
        f = list(self.data.columns)
        f.remove('time')
        return f
    
    def __str__(self):
        return str(self.data.head())
    
    def __init__(self,base_dir,file_name,names,usecols,case_dir=None,time_dirs=None,tmin=None,tmax=None):
        
        # create and empty reader
        if base_dir is None and file_name is None:
            self.data = pd.DataFrame(columns={'time':[]})
            return

        self.base_dir = base_dir

        self.file_name = file_name
       
        self.case_dir = case_dir
       
        if case_dir is None:
            self.case_dir = Path.cwd()
        
        self.tmin,self.tmax = tmin,tmax
        
        self.names = names
        
        self.usecols = usecols

        try:
            self.base_dir = Path(self.case_dir,'postProcessing',base_dir)
        except TypeError as e:
            print(e)
            self.data = pd.DataFrame(columns=names)
        
        self.base_dir = Path(self.case_dir,'postProcessing',base_dir)
        
        if time_dirs is None:
            self.time_dirs = list_time_dirs(self.base_dir)
        else:
            self.time_dirs = time_dirs
            
        self.load_data()

    def load_data(self):
        
        try:
            self.data = combine_oftime_files(self.base_dir, self.file_name, self.names, self.time_dirs,self.usecols)
        except IndexError:
            self.data = pd.DataFrame(columns=self.names)

        self.data.reset_index(inplace=True)
    
        self.customize()
    
    
    def customize(self):
        pass
        

    def time_range(self):

        if self.tmin is not None:
            self.data = self.data[self.data['time'] > self.tmin]
        
        if self.tmax is not None:
            self.data = self.data[self.data['time'] < self.tmax]


class OpenFOAMforces(OpenFOAMpostProcessing):
    
    def __init__(self,base_dir='forces',file_name='forces.dat',case_dir=None,tmin=None,tmax=None):
        
        names = ['time','fxp','fyp','fzp','fxv','fyv','fzv','fxpor','fypor','fzpor', 'mxp','myp','mzp','mxv','myv','mzv','mxpor','mypor','mzpor']
        usecols = ['time','fxp','fyp','fzp','fxv','fyv','fzv','mxp','myp','mzp','mxv','myv','mzv']

        self.SORT_ORDER = {'time':-1, "fx": 0}
          
        for i in range(1,len(usecols)):
            self.SORT_ORDER[usecols[i]] = i
        
        try:
            super().__init__(base_dir=base_dir,file_name=file_name,case_dir=case_dir,names=names,usecols=usecols,tmin=tmin,tmax=tmax)
        except Exception as e:
            if str(e) == 'Too many columns specified: expected 19 and found 13':
                #print("seems to be a force file without porosity")
                super().__init__(base_dir=base_dir,file_name=file_name,case_dir=case_dir,names=usecols,usecols=usecols,tmin=tmin,tmax=tmax)
        
        
    def customize(self):
        OpenFOAMpostProcessing.customize(self)
        
        self.data['fx'] = self.data['fxp'] + self.data['fxv']
        self.time_range()
        self.sort_fields()
        

class OpenFOAMrigidBodyState(OpenFOAMpostProcessing):
    
    def __init__(self,file_name='hull.dat',case_dir=None,subtractInitialCoG=True,tmin=None,tmax=None):

        names = ['time','x','y','z','roll','pitch','yaw','vx','vy','vz','vroll','vpitch','vyaw','xvcorr','yvcorr','zvcorr']
        
        super().__init__(base_dir='rigidBodyState',file_name=file_name,names=names,usecols=None,case_dir=case_dir,tmin=tmin,tmax=tmax)
        
        self.subtractInitialCoG = subtractInitialCoG
        
        
    def customize(self):
        OpenFOAMpostProcessing.customize(self)
        if self.data.size != 0:
            if self.subtractInitialCoG:
                for dof in ['x','y','z']:
                    self.data[dof] = self.data[dof] - self.data[dof].iloc[0]
        
        self.time_range()

class OpenFOAMresiduals(OpenFOAMpostProcessing):
    
    def __init__(self,base_dir='residuals',file_name='residuals.dat',case_dir=None,tmin=None,tmax=None):
        
        self.SORT_ORDER = {"U": 0, "Ux": 1, "Uy": 2, "Uz": 3, "p": 4, "p_rgh": 5, "k": 6, "omega":7,'time':-1}
        
        # we do not know in advance how many columns we have (e.g. laminar or turbulent case, etc.) 
        # and also which time dirs are present
        names = ['time'] + ['r' + str(x) for x in range(10)]
        
        super().__init__(base_dir=base_dir,file_name=file_name,names=names,usecols=None,case_dir=case_dir,tmin=tmin,tmax=tmax)
        
        self.data.dropna(how='all',axis=1,inplace=True)
        
        print('hui',(self.base_dir,self.time_dirs[0],'residuals.dat'))
        
        with Path(self.base_dir,self.time_dirs[0],'residuals.dat').open('r') as f:
            for i,line in enumerate(f):
                if i == 1:
                    header = line
                    break
        header = header.replace('#','').split()[:]
        header[0] = 'time'

        try:        
            self.data.columns = header
            self.names = list(header[1:])
        except ValueError as e:
            print('OpenFOAMresiduals::init',e)
        
        try:
            self.data['U'] = np.abs(self.data['Ux'].pow(2) + self.data['Uy'].pow(2) + self.data['Uz'].pow(2))
            self.data.drop(columns=['Ux','Uy','Uz'],inplace=True)
            
        except Exception:
            pass

        self.time_range()
            
        self.sort_fields()
        
        

class OpenFOAMtime(OpenFOAMpostProcessing):
    
    def __init__(self,base_dir,file_name='time.dat',case_dir=None,tmin=None,tmax=None):
        
        # we do not know in advance how many columns we have (as we can write e.g. with or without per-time-step values)
        # and also which time dirs are present
        names = ['time'] + ['r' + str(x) for x in range(10)]
        
        super().__init__(base_dir=base_dir,file_name=file_name,names=names,usecols=None,case_dir=case_dir,tmin=tmin,tmax=tmax)
        
        self.data.dropna(how='all',axis=1,inplace=True)
        
        with Path(self.base_dir,self.time_dirs[0],'time.dat').open('r') as f:
            for i,line in enumerate(f):
                if i == 1:
                    header = line
                    break
        header = header.replace('#','').split()[:]
        header[0] = 'time'
        self.data.columns = header
        
        self.time_range()
        
        
class OpenFOAMfieldMinMax(OpenFOAMpostProcessing):
    
    def __init__(self,base_dir,file_name='fieldMinMax.dat',case_dir=None,tmin=None,tmax=None):
        
        names = ['time','field','min','locationX(min)','locationY(min)','locationZ(min)','processor(min)','max','locationX(max)','locationY(max)','locationZ(max)','processor(max)']
        usecols = ['time','field','min','max']
        
        super().__init__(base_dir=base_dir,file_name=file_name,names=names,usecols=usecols,case_dir=case_dir,tmin=tmin,tmax=tmax)
        
        fields = self.data['field'].unique()
    
        dfs = [self.data.loc[self.data['field'] == field] for field in fields ]
        dfs = [df.drop(columns=['field']) for df in dfs]
        dfs = [df.set_index('time',drop=True) for df in dfs]
        
        for i,df in enumerate(dfs):
            mapper = {k:"{0:}_{1:}".format(k,fields[i]) for k in list(df.columns)}
            df.rename(columns=mapper,inplace=True)
        
        self.data = pd.concat(dfs,axis=1)
        
        self.data['time'] = self.data.index
        
        self.time_range()
    

def residuals(base_dir='residuals'):
    return OpenFOAMresiduals(base_dir=base_dir).data

def forces(base_dir='forces',file_name='forces.dat',case_dir=None,tmin=None,tmax=None):
    
    return OpenFOAMforces(base_dir=base_dir,file_name=file_name,case_dir=case_dir,tmin=tmin,tmax=tmax).data
    
def rigidBodyState(file_name='hull.dat',case_dir=None,tmin=None,tmax=None):
    
    return OpenFOAMrigidBodyState(file_name=file_name,case_dir=case_dir,tmin=tmin,tmax=tmax).data

def time(base_dir='timeMonitor'):
    return OpenFOAMtime(base_dir=base_dir).data.drop(columns=['cpu','clock']) 


def main():

    r = OpenFOAMresiduals()
    print(r.data)
    r.load_data()
    print(r.data)

    if False:    
        t = OpenFOAMtime(base_dir='timeMonitor')
        
        t = OpenFOAMfieldMinMax(base_dir='minMaxMag')
        fields = t.data.field.unique()
        
        dfs = [t.data.loc[t.data['field'] == field] for field in fields ]
        dfs = [df.drop(columns=['field']) for df in dfs]
        dfs = [df.set_index('time',drop=True) for df in dfs]
        for i,df in enumerate(dfs):
            mapper = {k:"{0:}_{1:}".format(k,fields[i]) for k in list(df.columns)}
            df.rename(columns=mapper,inplace=True)
            
        result = pd.concat(dfs,axis=1)
        print(result)
 


if __name__ == '__main__':
    main()
