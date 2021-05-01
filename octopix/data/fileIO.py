#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from io import StringIO
import os
from pathlib import Path
import sys


def makeRuntimeSelectableReader(reader_name,file_name):
    
    reader_name = "OpenFOAM{0:}".format(reader_name)
    try:
        reader = getattr(sys.modules[__name__],reader_name)(base_dir=file_name)
    except AttributeError as e:
        if str(e).find("octopix.data.fileIO"):
            if not str(e).find('None'):
                print('unknown reader',reader_name)    
        else:
            print(e)
            
        reader = OpenFOAMpostProcessing(base_dir=None, file_name=None, names=None, usecols=None)        
    
    return reader


def prepare_data(df,time_start=0.0,data_subset=[]):
            
    if time_start > 0.0:
        df = df.loc[df.time >= time_start]
            
    df.set_index('time',drop=True,inplace=True)

    if len(data_subset) > 0:
        df = df[df.columns.intersection(data_subset)]
            
    return df


def readOF(file_name):
    """Opens a text file, replaces all brackets with 
    whitespaces and return a file stream.  
    """
    trantab = str.maketrans('()','  ')

    with open(file_name,'r') as f:
        data = StringIO(f.read().translate(trantab))
    
    return data
    
def parseOF(file_name,names,usecols=None):
    """
    """
    return pd.read_csv(readOF(file_name),delim_whitespace=True,header=None,names=names,comment='#',usecols=usecols)    


def combineOFtimeFiles(base_dir,file_name,names,time_dirs=None,usecols=None):
    
    if time_dirs is None:
        time_dirs = listTimeDirs(base_dir)

    data = []
    
    for td in time_dirs:
        data.append(parseOF(os.path.join(base_dir,td,file_name),names,usecols).set_index('time'))

    d = data[-1]
       
    if len(data) > 1:
        for i in reversed(data[:-1]):
            if i.index.array[-1] > d.index.array[-1]: 
                i = i[i.index < d.index.array[-1]]
            d = d.combine_first(i)
    
    return d

def listTimeDirs(path_to_time_dirs):
    ## TODO: check the pattern. the list seems unnecessary, [0-9]' should cover all
    pattern = ['[0-9]*', '0.[0-9]*']  
    l = []
    for p in pattern:
        l.extend([str(x.name) for x in Path(path_to_time_dirs).glob(p)])
    
    return sorted(l,key=float,reverse=False)

class OpenFOAMpostProcessing(object):

    def fields(self):
        fields = list(self.data.columns)
        fields.remove('time')
        return fields
    
    def __str__(self):
        return str(self.data.head())
    
    def __init__(self,base_dir,file_name,names,usecols,case_dir=None,time_dirs=None,scale=None,tmin=None,tmax=None):
        
        # create and empty reader
        if base_dir is None and file_name is None:
            self.data = pd.DataFrame(columns={'time':[]})
            return
       
        if case_dir is None:
            self.case_dir = os.getcwd()
        else:
            self.case_dir = case_dir

        try:
            self.base_dir = os.path.join(self.case_dir,'postProcessing',base_dir)
        except TypeError:
            self.data = pd.DataFrame(columns=names)
        
        if time_dirs is None:
            self.time_dirs = listTimeDirs(self.base_dir)
        else:
            self.time_dirs = time_dirs
        
        try:
            self.data = combineOFtimeFiles(self.base_dir, file_name, names, self.time_dirs,usecols)
        except IndexError:
            self.data = pd.DataFrame(columns=names)
        
        self.tmin,self.tmax = tmin,tmax
        
        if scale is not None:
            self.data = scale * self.data

        self.data.reset_index(inplace=True)


    def timeRange(self):

        if self.tmin is not None:
            self.data = self.data[self.data['time'] > self.tmin]
        
        if self.tmax is not None:
            self.data = self.data[self.data['time'] < self.tmax]


class OpenFOAMvp(OpenFOAMpostProcessing):
    
    def __init__(self,base_dir='vp',file_name='volFieldValue.dat',case_dir=None):
        
        names = ['time','vpx','vpy','vpz']
        usecols = ['time','vpx']
        
        super().__init__(base_dir=base_dir, file_name=file_name, names=names, usecols=usecols, case_dir=case_dir)


class OpenFOAMforces(OpenFOAMpostProcessing):
    
    def __init__(self,base_dir='forces',file_name='forces.dat',case_dir=None,scale=None,tmin=None,tmax=None):
        
        names = ['time','fxp','fyp','fzp','fxv','fyv','fzv','fxpor','fypor','fzpor', 'mxp','myp','mzp','mxv','myv','mzv','mxpor','mypor','mzpor']
        usecols = ['time','fxp','fyp','fzp','fxv','fyv','fzv','mxp','myp','mzp','mxv','myv','mzv']
        
        try:
            super().__init__(base_dir=base_dir,file_name=file_name,case_dir=case_dir,names=names,usecols=usecols,scale=scale,tmin=tmin,tmax=tmax)
        except Exception as e:
            if str(e) == 'Too many columns specified: expected 19 and found 13':
                #print("seems to be a force file without porosity")
                super().__init__(base_dir=base_dir,file_name=file_name,case_dir=case_dir,names=usecols,usecols=usecols,scale=scale,tmin=tmin,tmax=tmax)
                
        self.data['fx'] = self.data['fxp'] + self.data['fxv']
        
        self.timeRange()

class OpenFOAMRigidBodyState(OpenFOAMpostProcessing):
    
    def __init__(self,file_name='hull.dat',case_dir=None,scale=None,subtractInitialCoG=True,tmin=None,tmax=None):
        
        names = ['time','x','y','z','roll','pitch','yaw','vx','vy','vz','vroll','vpitch','vyaw','xvcorr','yvcorr','zvcorr']
        
        super().__init__(base_dir='rigidBodyState',file_name=file_name,names=names,usecols=None,case_dir=case_dir,scale=scale,tmin=tmin,tmax=tmax)
        
        if self.data.size != 0:
            if subtractInitialCoG:
                for dof in ['x','y','z']:
                    self.data[dof] = self.data[dof] - self.data[dof].iloc[0]
        
        self.timeRange()

class OpenFOAMresiduals(OpenFOAMpostProcessing):
    
    def __init__(self,base_dir='residuals',file_name='residuals.dat',case_dir=None,tmin=None,tmax=None):
        
        # we do not know in advance how many columns we have (e.g. laminar or turbulent case, etc.) 
        # and also which time dirs are present
        names = ['time'] + ['r' + str(x) for x in range(10)]
        
        super().__init__(base_dir=base_dir,file_name=file_name,names=names,usecols=None,case_dir=case_dir,scale=None,tmin=tmin,tmax=tmax)
        
        self.data.dropna(how='all',axis=1,inplace=True)
        
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

        # TODO: we should add the sort functionality to the base class and provide a default sort dict to 
        # all derived classed, where required.         
        SORT_ORDER = {"U": 0, "Ux": 1, "Uy": 2, "Uz": 3, "p": 4, "p_rgh": 5, "k": 6, "omega":7,'time':-1}
        self.data = self.data.reindex(sorted(self.data.columns,key=lambda val: SORT_ORDER[val]),axis=1)
        

class OpenFOAMtime(OpenFOAMpostProcessing):
    
    def __init__(self,base_dir,file_name='time.dat',case_dir=None,tmin=None,tmax=None):
        
        # we do not know in advance how many columns we have (as we can write e.g. with or without per-time-step values)
        # and also which time dirs are present
        names = ['time'] + ['r' + str(x) for x in range(10)]
        
        super().__init__(base_dir=base_dir,file_name=file_name,names=names,usecols=None,case_dir=case_dir,scale=None,tmin=tmin,tmax=tmax)
        
        self.data.dropna(how='all',axis=1,inplace=True)
        
        with Path(self.base_dir,self.time_dirs[0],'time.dat').open('r') as f:
            for i,line in enumerate(f):
                if i == 1:
                    header = line
                    break
        header = header.replace('#','').split()[:]
        header[0] = 'time'
        self.data.columns = header
        

def residuals(base_dir='residuals'):
    return OpenFOAMresiduals(base_dir=base_dir).data

def forces(base_dir='forces',file_name='forces.dat',case_dir=None,scale=None,tmin=None,tmax=None):
    
    return OpenFOAMforces(base_dir=base_dir,file_name=file_name,case_dir=case_dir,scale=scale,tmin=tmin,tmax=tmax).data
    
def rigidBodyState(file_name='hull.dat',case_dir=None,tmin=None,tmax=None):
    
    return OpenFOAMRigidBodyState(file_name=file_name,case_dir=case_dir,tmin=tmin,tmax=tmax).data

def time(base_dir='timeMonitor'):
    return OpenFOAMtime(base_dir=base_dir).data.drop(columns=['cpu','clock']) 


def main():
    
    t = OpenFOAMtime(base_dir='timeMonitor')
    


if __name__ == '__main__':
    main()
