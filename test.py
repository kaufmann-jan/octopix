#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

import configparser

from pathlib import Path

from datetime import datetime

sys.path.insert(0, "/home/jan/workspace/MOFA/python")
#print(str(sys.path))
from dataProcessing.fileIO import forces, residuals
import matplotlib
matplotlib.use('Qt5Agg')

#from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5 import QtCore
from PyQt5.QtGui import QPalette, QColor,QDoubleValidator

from PyQt5.QtWidgets import QVBoxLayout,QHBoxLayout,QFormLayout,QGridLayout

from PyQt5.QtWidgets import QMainWindow,QWidget,QApplication,QCheckBox,QComboBox,\
    QDateEdit,QDateTimeEdit,QDial,QDoubleSpinBox,QLCDNumber,QLabel,QLineEdit,QProgressBar,\
    QPushButton,QRadioButton,QSlider,QSpinBox,QTimeEdit,QPlainTextEdit,QTabWidget,QListWidget
    
from PyQt5.QtCore import pyqtSlot

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg,NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import numpy as np
import pandas as pd

from fileOps import findAllOFPostProcObjects,listDiff,findAllOFppObjects,are_equal

if False:
    pd.set_option('display.float_format', lambda x: '%.3f' % x)

supported_post_types = ['residuals','forces','rigidBodyState','time','fieldMinMax']


class Color(QWidget):

    def __init__(self, color, *args, **kwargs):
        super(Color, self).__init__(*args, **kwargs)
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)
       
        self.data = pd.DataFrame()
        self._plot_refs = None
        self.stylecounter = 0
        self.current_data_type = None
       
    def load_data(self,data_type,time_start=0.0):
        """Reads the OpenFOAM postprocessing time-series data 
        from disk and converts it to an pandas data frame.
        """
        try:
            if data_type == 'residuals':
                self.df = residuals()
            elif data_type == 'forces':
                self.df = forces()
            else:
                self.df = pd.DataFrame(data={'time':[]})
            
            if time_start > 0.0:
                self.df = self.df.loc[self.df.time >= time_start]
            
            self.df.set_index('time',drop=True,inplace=True)
            
        except IndexError as e:
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
                fig_facecolor = np.array([72,77,73])/255.
                axes_facecolor = np.array([83,89,85])/255.
                grid_color = 'lightgray'
                text_color = 'white'

            self.fig.set_facecolor(fig_facecolor)
            self.axes.grid(True,linestyle=':',color=grid_color)
            self.axes.set_facecolor(axes_facecolor)
            self.axes.xaxis.label.set_color(text_color)
            self.axes.yaxis.label.set_color(text_color)
            self.axes.tick_params(colors=text_color)

            for spine in ['left','right','top','bottom']:
                self.axes.spines[spine].set_visible(False)
    
 
    def update_plot(self,data_type,time_start=0.0,data_subset=[]):
        """(Re)Loads the data with self.load_data() and 
        draws the plot. If called for the first time, the 
        axis is created, otherwise the reference to the axis
        is updated (not yet implemented, for now we just clear the
        axis and redraw...
        """
        self.load_data(data_type,time_start)
        
        if self.df.empty:
            self.axes.cla()
            textstr = 'No Data available'
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            self.axes.text(0.35, 0.6, textstr, transform=self.axes.transAxes, fontsize=10,verticalalignment='top', bbox=props)
            self._plot_refs = None
        else:
            
            if len(data_subset) > 0:
                self.df =  self.df[self.df.columns.intersection(data_subset)]
    
            if self._plot_refs is None or self.current_data_type != data_type:
                
                self.current_data_type = data_type
                self.axes.cla()
                                
                plot_refs = [ self.axes.plot(self.df.index,self.df[col],label=col)[0] for col in list(self.df)]
                
                if data_type == 'residuals':
                    self.axes.set_ylabel('Residuals [-]')    
                    self.axes.set_yscale('log')
                elif data_type == 'forces':
                    self.axes.set_ylabel('Forces')
                
                self.axes.set_xlabel('Time')   
    
                legend = self.axes.legend()
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
            des = self.df.describe().T.loc[:,['mean','min','max','std']]
        except:
            des = pd.DataFrame()
        
        return des.T


class Octopix(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(Octopix, self).__init__(*args, **kwargs)

        self.setWindowTitle("Octopix - Visualize your Simulation Progress")
        self.statusBar().showMessage('Ready')
        
        # --------------
        # user input and defaults
        # data type should be selectable by the GUI
        # by drop down or similar
        # time start should be optional input from GUI
        # slider??, or value box
        # defaults to 0.0
        
        self.ppObjects = findAllOFppObjects(supported_types=supported_post_types, working_dir=Path.cwd())
        
        self.data_types = list(self.ppObjects.keys())
        self.data_type = None
        self.data_subset = []
        self.eval_time_start = 0.0
        #---------------------------
        
        self.sc = MplCanvas(self, width=7, height=4, dpi=100)
        toolbar = NavigationToolbar(self.sc, self)
        
        settings_layout = QVBoxLayout()
        
        e1 = QLineEdit()
        #e1.setText(str(0))
        e1.setValidator(QDoubleValidator())
        e1.textEdited.connect(self.onChanged)

        self.cb = QComboBox()
        #cb.addItem('forces')
        #cb.addItem('residuals')
        #cb.addItems(self.data_types)
        self.cb.currentIndexChanged.connect(self.selectionChanged)
        
            

        flo = QFormLayout()
        flo.addRow("Eval start time", e1)
        flo.addRow("Data",self.cb)
        
        settings_layout.addLayout(flo)
        
        self.listname = QLabel('objects')
        self.listwidget = QListWidget()
        
        settings_layout.addWidget(self.listname)
        settings_layout.addWidget(self.listwidget)
        settings_layout.addStretch(1)
         
        # Initialize tab screen
        self.tabs = QTabWidget(self)
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        # Add tabs
        self.tabs.addTab(self.tab1,"Output")
        self.tabs.addTab(self.tab2,"Statistics") 
         
        self.output_text_field = QPlainTextEdit()
        self.output_text_field.setReadOnly(True)
        self.output_text_field.setStyleSheet("background-color:lightgray")

        self.tab1.layout = QVBoxLayout()
        self.tab1.layout.addWidget(self.output_text_field)
        self.tab1.setLayout(self.tab1.layout)

        self.statistics_text_field = QPlainTextEdit()
        self.statistics_text_field.setReadOnly(True)
        self.statistics_text_field.setStyleSheet("background-color:lightgray")
          
        self.tab2.layout = QVBoxLayout()
        self.tab2.layout.addWidget(self.statistics_text_field)
        exportButton = QPushButton('Export')
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(exportButton)
        self.tab2.layout.addLayout(hbox)
        self.tab2.setLayout(self.tab2.layout)
        
        self.auto_update = True
        self.auto_update_checkBox = QCheckBox("Autoupdate",self)
        self.auto_update_checkBox.setChecked(True)
        self.auto_update_checkBox.stateChanged.connect(self.clickBox)
        
        reload_button = QPushButton('Reload', self)
        reload_button.setToolTip('Reload the data')
        reload_button.clicked.connect(self.on_click)
        
        hbox = QHBoxLayout()
        hbox.addWidget(self.auto_update_checkBox)
        hbox.addStretch(1)
        hbox.addWidget(reload_button)
        
        settings_layout.addLayout(hbox)    
                   
        canvas_layout = QVBoxLayout()
        canvas_layout.addWidget(toolbar)
        canvas_layout.addWidget(self.sc)
        #canvas_layout.addWidget(self.tabs)
        
        #outer_layout = QHBoxLayout()
        #outer_layout.addLayout(settings_layout)
        #outer_layout.addLayout(canvas_layout)

        outer_layout = QGridLayout()
        outer_layout.addLayout(settings_layout,0,0,3,1)
        outer_layout.addLayout(canvas_layout,0,2)
        outer_layout.addWidget(self.tabs,2,2)
        outer_layout.setColumnStretch(0,0)
        outer_layout.setColumnStretch(2,2)

        widget = QWidget()
        widget.setLayout(outer_layout)
        
        self.setCentralWidget(widget)

        self.update_plot()

        self.show()
        
        # Setup a timer to trigger the redraw by calling update_plot.
        self.timer = QtCore.QTimer()
        self.timer.setInterval(1000)
        #self.timer.timeout.connect(lambda: self.sc.update_plot(self.data_type,self.eval_time_start))
        self.timer.timeout.connect(self.update_plot)
        # start the timer on start-up        
        self.clickBox(QtCore.Qt.Checked)

        self.statusBar().showMessage('Ready')
    

    def update_plot(self):
        
        self.ppObjects = findAllOFppObjects(supported_types=supported_post_types)
        
        currentFoundItems = list(self.ppObjects.keys())
        currentLoadedItems = [self.cb.itemText(i) for i in range(self.cb.count())]
        
        if not are_equal(currentFoundItems,currentLoadedItems):
            self.cb.clear()
            self.cb.addItems(list(self.ppObjects.keys()))

        # set focus on first element if not yet initialized # check!!!!!
        if self.data_type is None and len(self.data_types) > 0:
            self.data_type = self.data_types[0]

            self.listwidget.clear()
            self.listwidget.addItems(self.ppObjects[self.data_type])       
        
             
        stats = self.sc.update_plot(self.data_type,self.eval_time_start,self.data_subset)
        self.statistics_text_field.setPlainText(str(stats))

    def _output(self,text):
        
        now = datetime.now().strftime("%H:%M:%S")
        txt = "{0:}: {1:}".format(now,text)
        
        self.output_text_field.appendPlainText(txt)

    def clickBox(self, state):
        """Auto update checkbox
        """
        if state == QtCore.Qt.Checked:
            self._output('Autoupdate on')
            self.timer.start()
        else:
            self._output('Autoupdate off')
            self.timer.stop()
    

    @pyqtSlot()
    def on_click(self):
        """Reload data button
        """
        self._output('Reloading data')
        self.update_plot()

    def onChanged(self,text):
        try:
            self.eval_time_start = float(text)
        except:
            self.output_text_field.appendPlainText('ups')
        
        self.update_plot()
            
    def selectionChanged(self,i):
        
        self.ppObjects = findAllOFppObjects(supported_types=supported_post_types)
        
        try:
            self.data_type = list(self.ppObjects.keys())[i]
            
            if self.data_type == 'forces':
                self.data_subset = ['fx','fxv']
            else:
                self.data_subset = []
            
            self.listwidget.clear()
            self.listwidget.addItems(self.ppObjects[self.data_type])
            
            self.update_plot()
            
        except IndexError as e:
            print(e)

def main():
    
    app = QApplication(sys.argv)
    w = Octopix()  
    app.exec_()


if __name__ == '__main__':
    main()



