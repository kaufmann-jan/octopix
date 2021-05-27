#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from io import StringIO
from pathlib import Path
import sys

import pandas as pd
import numpy as np


def makeRuntimeSelectableReader(reader_name,file_name,case_dir):
    
    reader_name = "OpenFOAM{0:}".format(reader_name)

    if reader_name == "OpenFOAMrigidBodyState":
        reader = getattr(sys.modules[__name__],reader_name)(file_name=file_name,case_dir=case_dir)
    else:
        reader = getattr(sys.modules[__name__],reader_name)(base_dir=file_name,case_dir=case_dir)
    
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
    whitespaces, passes a file stream to the pandas csv read method
    and return a pandas DataFrame.  
    """
    trantab = str.maketrans('()','  ')

    path = Path(file_name)

    with path.open('r') as f:
        fstream = StringIO(f.read().translate(trantab))
    
    df = pd.read_csv(fstream,delim_whitespace=True,header=None,names=names,comment='#',usecols=usecols)

    return df


def list_time_dirs(path_to_time_dirs):
    
    l = sorted([str(x.name) for x in Path(path_to_time_dirs).glob('[0-9]*')],key=float,reverse=False)
    l = [Path(path_to_time_dirs,p) for p in l]
    
    return l

class OpenFOAMpostProcessing(object):

    def combine_oftime_files(self,file_name,names,usecols):      

        time_dirs = list_time_dirs(self.base_dir)
            
        if not time_dirs:
            # no time dirs found, empty case!!!
            #self.data = pd.DataFrame(columns={'time':[]})
            self.data = pd.DataFrame(columns=self.names)
            return
        
        current_mtime = np.amax([Path(td,file_name).stat().st_mtime for td in time_dirs])
        
        verbose = True
        if current_mtime == self.mtime: # no need to reload
            if verbose: print('no need to reload, we are up to date')
            self.up_to_date = True
        else:
            self.up_to_date = False
            self.mtime = current_mtime
            
            tmp_data = []
        
            for td in time_dirs:
                p = Path(td,file_name)
                df = parse_of(p,names,usecols)
                try:
                    tmp_data.append(df.set_index('time'))
                except KeyError as e:
                    tmp_data.append(df.set_index(0))
        
            d = tmp_data[-1]
               
            if len(tmp_data) > 1:
                for i in reversed(tmp_data[:-1]):
                    if i.index.array[-1] > d.index.array[-1]: 
                        i = i[i.index < d.index.array[-1]]
                    d = d.combine_first(i)
            
            self.data = d
            self.data.reset_index(inplace=True)


    def sort_fields(self):
          
        try: 
            self.data = self.data.reindex(sorted(self.data.columns,key=lambda val: self.SORT_ORDER[val]),axis=1)
        except KeyError as e:
            pass 
            #print(e)

    def fields(self):
        
        f = list(self.data.columns)
        f.remove('time')
        
        return f
    
    def __str__(self):
        
        return str(self.data.head())
    
    def __init__(self,base_dir,file_name,names=None,usecols=None,case_dir=None,tmin=None,tmax=None):
        
        self.mtime = 0
        self.up_to_date = False
        
        # create and empty reader  # not sure if this makes sense
        if base_dir is None and file_name is None:
            self.data = pd.DataFrame(columns={'time':[]})
            return

        self.base_dir = base_dir

        self.file_name = file_name
       
        self.case_dir = case_dir
       
        if case_dir is None:
            self.case_dir = Path.cwd()
        
        self.tmin,self.tmax = tmin,tmax
                
        if names is None:
            # instead of just passing names=None to pd.read_csv() we create a dummy
            # names list with ['time', 'c1', ... 'c89'], because:
            # 1. we want to explicitly name column 0 to 'time'
            # 2. with header=None, names=None and usecols=None reading of the 
            #    OpenFOAM residual files fails due to the first line 
            #    showing only one entry N/A for Ux Uy Uz, i.e. number of columns
            #    determined by pandas does not match the number of data fields
            self.names =  ['time'] + ['c' + str(x) for x in range(99)]
        else:
            self.names = names
        
        self.usecols = usecols
        
        self.base_dir = Path(self.case_dir,'postProcessing',base_dir)
                   
        self.load_data()
        

    def load_data(self):
        
        self.combine_oftime_files(self.file_name, self.names, self.usecols)

        if not self.up_to_date:
            self.customize()
            
        
    
    def get_data(self):
        
        self.load_data()
        
        return self.data
    
    def customize(self):
        
        pass
        

    def time_range(self):

        if self.tmin is not None:
            self.data = self.data[self.data['time'] > self.tmin]
        
        if self.tmax is not None:
            self.data = self.data[self.data['time'] < self.tmax]


class OpenFOAMforces(OpenFOAMpostProcessing):
    
    def __init__(self,base_dir='forces',file_name='forces.dat',case_dir=None,tmin=None,tmax=None):

        self.SORT_ORDER = {'time':-1, "fx": 0}
        
        super().__init__(base_dir=base_dir,file_name=file_name,case_dir=case_dir,names=None,usecols=None,tmin=tmin,tmax=tmax)
        
    def customize(self):
        OpenFOAMpostProcessing.customize(self)

        if not self.data.empty and self.usecols is None:

            self.data.dropna(how='all',axis=1,inplace=True)            

            if len(self.data.columns == 13):
                self.names = ['time','fxp','fyp','fzp','fxv','fyv','fzv','mxp','myp','mzp','mxv','myv','mzv']        
            else:
                self.names = ['time','fxp','fyp','fzp','fxv','fyv','fzv','fxpor','fypor','fzpor', 'mxp','myp','mzp','mxv','myv','mzv','mxpor','mypor','mzpor']

            self.usecols = ['time','fxp','fyp','fzp','fxv','fyv','fzv','mxp','myp','mzp','mxv','myv','mzv']

            for i in range(1,len(self.usecols)):
                self.SORT_ORDER[self.usecols[i]] = i
            
            mapper = dict(zip(self.data.columns,self.usecols))
            
            self.data.rename(columns=mapper,inplace=True)        
        
        try:
            self.data['fx'] = self.data['fxp'] + self.data['fxv']
        except KeyError:
            pass
        
        self.time_range()
        
        self.sort_fields()
        

class OpenFOAMrigidBodyState(OpenFOAMpostProcessing):
    
    def __init__(self,base_dir='rigidBodyState',file_name='hull.dat',case_dir=None,subtractInitialCoG=True,tmin=None,tmax=None):
        
        self.subtractInitialCoG = subtractInitialCoG

        names = ['time','x','y','z','roll','pitch','yaw','vx','vy','vz','vroll','vpitch','vyaw','xvcorr','yvcorr','zvcorr']
        
        super().__init__(base_dir=base_dir,file_name=file_name,names=names,usecols=None,case_dir=case_dir,tmin=tmin,tmax=tmax)
              
        
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
        
        super().__init__(base_dir=base_dir,file_name=file_name,names=None,usecols=None,case_dir=case_dir,tmin=tmin,tmax=tmax)
        
    
    def customize(self): 
        OpenFOAMpostProcessing.customize(self)

        if not self.data.empty and self.usecols is None:
        
            self.data.dropna(how='all',axis=1,inplace=True)
            
            time_dirs = list_time_dirs(Path(self.base_dir))
                     
            with Path(self.base_dir,time_dirs[0],'residuals.dat').open('r') as f:
                for i,line in enumerate(f):
                    if i == 1:
                        header = line
                        break
    
            header = header.replace('#','').split()[:]
            header[0] = 'time'
    
            self.names = header
            self.usecols = header
            
            mapper = dict(zip(self.data.columns,self.usecols))
            
            self.data.rename(columns=mapper,inplace=True)

        try:
            self.data['U'] = (np.abs(self.data['Ux'].pow(2) + self.data['Uy'].pow(2) + self.data['Uz'].pow(2)))/3.
            self.data.drop(columns=['Ux','Uy','Uz'],inplace=True)    
        except KeyError:
            pass

        self.time_range()
            
        self.sort_fields()
        

class OpenFOAMtime(OpenFOAMpostProcessing):
    
    def __init__(self,base_dir,file_name='time.dat',case_dir=None,tmin=None,tmax=None):
        
        super().__init__(base_dir=base_dir,file_name=file_name,names=None,usecols=None,case_dir=case_dir,tmin=tmin,tmax=tmax)
        
        
    def customize(self):
        OpenFOAMpostProcessing.customize(self)
                
        if not self.data.empty and self.usecols is None:
            self.data.dropna(how='all',axis=1,inplace=True)
            
            time_dirs = list_time_dirs(Path(self.base_dir))

            with Path(self.base_dir,time_dirs[0],'time.dat').open('r') as f:
                for i,line in enumerate(f):
                    if i == 1:
                        header = line
                        break
                    
            header = header.replace('#','').split()[:]
            header[0] = 'time'
    
            self.names = header
            self.usecols = header
            
            mapper = dict(zip(self.data.columns,self.usecols))
            
            self.data.rename(columns=mapper,inplace=True)
        
        
        self.time_range()
        
        
class OpenFOAMfieldMinMax(OpenFOAMpostProcessing):
    
    def __init__(self,base_dir,file_name='fieldMinMax.dat',case_dir=None,tmin=None,tmax=None):
        
        names = ['time','field','min','locationX(min)','locationY(min)','locationZ(min)','processor(min)','max','locationX(max)','locationY(max)','locationZ(max)','processor(max)']
        usecols = ['time','field','min','max']
        
        super().__init__(base_dir=base_dir,file_name=file_name,names=names,usecols=usecols,case_dir=case_dir,tmin=tmin,tmax=tmax)
        
        
    def customize(self):
        OpenFOAMpostProcessing.customize(self)
        
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


def residuals(base_dir='residuals',case_dir=None):
    return OpenFOAMresiduals(base_dir=base_dir,case_dir=case_dir).data

def forces(base_dir='forces',file_name='forces.dat',case_dir=None,tmin=None,tmax=None):
    
    return OpenFOAMforces(base_dir=base_dir,file_name=file_name,case_dir=case_dir,tmin=tmin,tmax=tmax).data
    
def rigidBodyState(file_name='hull.dat',case_dir=None,tmin=None,tmax=None):
    
    return OpenFOAMrigidBodyState(file_name=file_name,case_dir=case_dir,tmin=tmin,tmax=tmax).data

def time(base_dir='timeMonitor'):
    return OpenFOAMtime(base_dir=base_dir).data.drop(columns=['cpu','clock']) 


def main():

    #r = OpenFOAMforces() 
    #r = OpenFOAMresiduals()
    #r = OpenFOAMtime(base_dir='timeMonitor')
    r = OpenFOAMfieldMinMax(base_dir='minMaxMag')
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
