#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg,NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import numpy as np
import pandas as pd

from fileIO import OpenFOAMresiduals,OpenFOAMForces,OpenFOAMtime
from PyQt5.QtWidgets import QVBoxLayout


class canvasLayout(QVBoxLayout):

    def __init__(self, *args, **kwargs):
        super(canvasLayout,self).__init__(*args, **kwargs)
        
        self.mplCanvas = MplCanvas()
        self.toolbar = NavigationToolbar(self.mplCanvas,None)
        
        self.addWidget(self.toolbar)
        self.addWidget(self.mplCanvas)


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)
       
        self.data = pd.DataFrame()
        self._plot_refs = None
        self.current_data_type = None
        self.current_data_file = None
        self.current_data_subset = None
       
    def load_data(self,data_type,data_file,time_start=0.0):
        """Reads the OpenFOAM postprocessing time-series data
        from disk and converts it to an pandas data frame.
        """
        try:
            if data_type == 'residuals':
                ofpp = OpenFOAMresiduals(base_dir=data_file)
            elif data_type == 'forces':
                ofpp = OpenFOAMForces(base_dir=data_file)
            elif data_type == 'time':
                ofpp = OpenFOAMtime(base_dir=data_file)
            else:
                ofpp = None
                
            if ofpp is None:
                self.df = pd.DataFrame(data={'time':[]})
            else:
                self.df = ofpp.data
                
            self.fields = list(self.df.columns)
            self.fields.remove('time')
            
            if time_start > 0.0:
                self.df = self.df.loc[self.df.time >= time_start]
            
            self.df.set_index('time',drop=True,inplace=True)
            
        except:
            self.df = pd.DataFrame()
        

                
    def _setPlotStyle(self,style='dark'):
        
        if style is None:
            self.axes.grid(True,linestyle='-',color='black')
            fig_facecolor = 'white'
            axes_facecolor = 'white'
            text_color = 'black'

            self.fig.set_facecolor(fig_facecolor)
            self.axes.set_facecolor(axes_facecolor)
            self.axes.xaxis.label.set_color(text_color)
            self.axes.yaxis.label.set_color(text_color)
            self.axes.tick_params(colors=text_color)

            for spine in ['left','right','top','bottom']:
                self.axes.spines[spine].set_visible(True) 
                           
        else:
            if style == 'bright':
                fig_facecolor = np.array([204.,213,230])/255.
                axes_facecolor = np.array([173.,182,199])/255.
                text_color = 'black'
                grid_color = 'white'
            elif style == 'dark':
                fig_facecolor = np.array([129, 140, 143])/255.
                axes_facecolor = np.array([141, 154, 158])/255.
                #fig_facecolor = np.array([72,77,73])/255.
                #axes_facecolor = np.array([83,89,85])/255.
                grid_color = 'lightgray'
                text_color = 'white'

            self.fig.set_facecolor(fig_facecolor)
            self.axes.grid(True,linestyle=':',color=grid_color)
            self.axes.set_facecolor(axes_facecolor)
            self.axes.xaxis.label.set_color(text_color)
            self.axes.yaxis.label.set_color(text_color)
            self.axes.tick_params(colors=text_color)
            self.axes.tick_params(colors=text_color, which='both')

            for spine in ['left','right','top','bottom']:
                self.axes.spines[spine].set_visible(False)
    
 
    def clear(self):
        
        self.axes.cla()
        textstr = 'No Data\navailable'
        props = dict(boxstyle='round', facecolor=np.array([163, 130, 38])/255., alpha=0.5)
        self.axes.text(0.45, 0.55, textstr, transform=self.axes.transAxes, fontsize=10,verticalalignment='top', bbox=props)
        self._plot_refs = None
 
 
    def update_plot(self,data_type,data_file,time_start=0.0,data_subset=[]):
        """(Re)Loads the data with self.load_data() and 
        draws the plot. If called for the first time, the 
        axis is created, otherwise the reference to the axis
        is updated.
        """
        self.load_data(data_type,data_file,time_start)
        
        if self.df.empty:
            self.clear()
        else:
            
            if len(data_subset) > 0:
                self.df =  self.df[self.df.columns.intersection(data_subset)]
                if self.df.empty:
                    return
    
            if self._plot_refs is None or self.current_data_type != data_type or self.current_data_subset != data_subset:
                
                self.current_data_type = data_type
                self.current_data_file = data_file
                self.axes.cla()
                                
                plot_refs = [ self.axes.plot(self.df.index,self.df[col],label=col)[0] for col in list(self.df)]
                
                if data_type == 'residuals':
                    self.axes.set_ylabel('Residuals [-]')    
                    self.axes.set_yscale('log')

                elif data_type == 'forces':
                    self.axes.set_ylabel('Forces')
                
                self.axes.set_xlabel('Time')   

                legend = self.axes.legend(framealpha=0.2)
                legend.set_draggable(True)
    
                self._plot_refs = plot_refs
                
            else:
               
                for i,col in enumerate(list(self.df)):
                    self._plot_refs[i].set_data(self.df.index,self.df[col])
    
                self.axes.relim()
                self.axes.autoscale_view()

        self._setPlotStyle()
        self.draw()
        
        try:
            self.des = self.df.describe().T.loc[:,['mean','min','max','std']]
        except:
            self.des = pd.DataFrame()
            
    def savePlot(self):
        
        fig_name = "{0:}.png".format(self.current_data_file)
        
        self.print_figure(fig_name,dpi=200)
