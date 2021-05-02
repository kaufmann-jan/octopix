#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd

from octopix.show.canvas import canvasLayout
from octopix.data.fileOps import OFppScanner,are_equal
from octopix.data.fileIO import makeRuntimeSelectableReader,prepare_data
from octopix.data.funcs import getAllListItems,getSelectedListItems

import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5.QtCore import pyqtSlot,QTimer,Qt
from PyQt5.QtGui import QDoubleValidator,QIcon
from PyQt5.QtWidgets import QMainWindow,QWidget,QApplication,QCheckBox,QComboBox,\
    QLabel,QLineEdit,QPushButton,QPlainTextEdit,QTabWidget,QListWidget,QVBoxLayout,\
    QHBoxLayout,QFormLayout,QGridLayout,QAction,qApp,QAbstractItemView,QSpacerItem,\
    QSizePolicy

from octopix.common.config import supported_post_types,default_field_selection


class Octopix(QMainWindow):

    def printMoep(self):
        print('mööööp')

    def initMenubar(self):
        
        exitAct = QAction(QIcon('exit.png'), '&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(qApp.quit)
                
        menubar = self.menuBar()
        
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAct)
        
        setStyle = QAction('möp', self)
        setStyle.setShortcut('Ctrl+M')
        setStyle.setStatusTip('print möööp to the console')
        #setStyle.triggered.connect(self.printMoep)
        setStyle.triggered.connect(lambda: print('mööööööööööp'))
        
        appearanceMenu = menubar.addMenu('&Appearance')
        appearanceMenu.addAction(setStyle)
        
        

    def __init__(self, show_gui, *args, **kwargs):
        super(Octopix, self).__init__(*args, **kwargs)

        self.setWindowTitle("Octopix - Visualize your Simulation Progress")
        
        self.initMenubar()

        self.statusBar()
        
        self.setGeometry(140, 140, 1150, 900)
        
        # --------------
        # user input and defaults
        # data type should be selectable by the GUI
        # by drop down or similar
        # time start should be optional input from GUI
        # slider??, or value box
        # defaults to 0.0
        
        self.OFscanner = OFppScanner(supported_types=supported_post_types, working_dir=Path.cwd())
        
        self.data_type = None
        self.data_subset = []
        self.eval_time_start = 0.0
        dark_mode = False
        self.current_field_selection = {k:[] for k in supported_post_types}
        #---------------------------
        
        settings_layout = QVBoxLayout()
        
        e1 = QLineEdit()
        e1.setMaximumWidth(100)
        #e1.setText(str(0.0))
        e1.setValidator(QDoubleValidator())
        e1.textEdited.connect(self.onChanged)

        self.cb = QComboBox()
        self.cb.setMaximumWidth(100)
        self.cb.currentIndexChanged.connect(self.selectionChanged)
        

        flo = QFormLayout()
        
        flo.addRow(QLabel("Tmin:"), e1)
        flo.addRow(QLabel("Data type:"),self.cb)

        verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        settings_layout.addItem(verticalSpacer)        
        settings_layout.addLayout(flo)
        
        self.filelist = QListWidget()
        self.filelist.setAlternatingRowColors(True)
        self.filelist.setStyleSheet("alternate-background-color:rgb(192,192,192);background-color:rgb(211,211,211);")
        self.filelist.setMaximumSize(150, 100) # (width, height)
        
        self.fieldlist = QListWidget()
        self.fieldlist.setAlternatingRowColors(True)
        self.fieldlist.setStyleSheet("alternate-background-color:rgb(192,192,192);background-color:rgb(211,211,211);")
        self.fieldlist.setMaximumSize(150,120)
        self.fieldlist.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.fieldlist.itemSelectionChanged.connect(self.fieldsSelectionChanged)              
        
        settings_layout.addWidget(QLabel('Files:'))
        settings_layout.addWidget(self.filelist)
        settings_layout.addWidget(QLabel('Fields:'))
        settings_layout.addWidget(self.fieldlist)
        settings_layout.addStretch(1)
         
        # Initialize tab screen
        self.tabs = QTabWidget(self)
        self.output_tab = QWidget()
        self.statistics_tab = QWidget()
        # Add tabs
        self.tabs.addTab(self.output_tab,"Output")
        self.tabs.addTab(self.statistics_tab,"Statistics") 
         
        self.output_text_field = QPlainTextEdit()
        self.output_text_field.setReadOnly(True)
        self.output_text_field.setStyleSheet("background-color:lightgray")

        self.output_tab.layout = QVBoxLayout()
        self.output_tab.layout.addWidget(self.output_text_field)
        self.output_tab.setLayout(self.output_tab.layout)

        self.statistics_text_field = QPlainTextEdit()
        self.statistics_text_field.setReadOnly(True)
        self.statistics_text_field.setStyleSheet("background-color:lightgray")
          
        self.statistics_tab.layout = QVBoxLayout()
        self.statistics_tab.layout.addWidget(self.statistics_text_field)
        exportButton = QPushButton('Export')
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(exportButton)
        self.statistics_tab.layout.addLayout(hbox)
        self.statistics_tab.setLayout(self.statistics_tab.layout)
        
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
                   
        self.canvas_layout = canvasLayout()

        outer_layout = QGridLayout()
        outer_layout.addLayout(settings_layout,0,0,3,1)
        outer_layout.addLayout(self.canvas_layout,0,2)
        outer_layout.addWidget(self.tabs,2,2)
        outer_layout.setColumnStretch(0,0)
        outer_layout.setColumnStretch(2,2)
        outer_layout.setRowStretch(0,2)
        outer_layout.setRowStretch(2,1)

        widget = QWidget()
        widget.setLayout(outer_layout)
        
        self.setCentralWidget(widget)

        self.update_plot()
        
        if dark_mode:
            self.setStyleSheet("background-color:rgb(130, 138, 140);")
            self.output_text_field.setStyleSheet("background-color:rgb(139, 146, 148);")
            self.statistics_text_field.setStyleSheet("background-color:rgb(139, 146, 148);")
            self.filelist.setStyleSheet("background-color:rgb(139, 146, 148);")
        
        if show_gui:
            self.show()
        else:
            self.canvas_layout.mplCanvas.savePlot()
            sys.exit(0)
            
        
        # Setup a timer to trigger the redraw by calling update_plot.
        self.timer = QTimer()
        self.timer.setInterval(1000)
        #self.timer.timeout.connect(lambda: self.sc.update_plot(self.data_type,self.eval_time_start))
        self.timer.timeout.connect(self.update_plot)
        if True:
            # start the timer on start-up        
            self.clickBox(Qt.Checked)

        self.statusBar().showMessage('Ready')


    def update_plot(self):
                
        self.OFscanner.scan()
        
        currentFoundItems = self.OFscanner.post_types
        
        currentLoadedItems = [self.cb.itemText(i) for i in range(self.cb.count())]
        
        if not are_equal(currentFoundItems,currentLoadedItems):
            self.canvas_layout.mplCanvas.clear()
            self.cb.clear()
            self.cb.addItems(self.OFscanner.post_types)
        
        if len(self.OFscanner.post_types) == 0:
            self.filelist.clear()
        
        try:
            data_name = self.filelist.currentItem().text()
        except:
            data_name = None

        # load the data and provide the dataframe to canvas 
        # data_type defines the reader
        reader = makeRuntimeSelectableReader(reader_name=self.data_type,file_name=data_name)
        fields = reader.fields()
        df = prepare_data(reader.data,self.eval_time_start,self.data_subset)

        self.canvas_layout.mplCanvas.update_plot(df,self.data_type,data_name)
        
        # if data type has changed, we need to update the list of fields
        if not are_equal(getAllListItems(self.fieldlist), fields):

            # either apply the previous selection or the default if prev is empty
            if self.current_field_selection[self.data_type]:
                fields_to_select = self.current_field_selection[self.data_type]
            else:
                fields_to_select = default_field_selection.get(self.data_type,fields)
                
            self.fieldlist.clear() 
            self.fieldlist.addItems(fields)
                
            for i in range(self.fieldlist.count()):
                list_item = self.fieldlist.item(i) 
                if list_item.text() in fields_to_select:
                    list_item.setSelected(True)
        
        self.data_subset = getSelectedListItems(self.fieldlist)
        
        try:
            des = df.describe().T.loc[:,['mean','min','max','std']]
        except:
            des = pd.DataFrame()
        
        self.statistics_text_field.setPlainText(str(des))
        


    def _output(self,text):
        
        now = datetime.now().strftime("%H:%M:%S")
        txt = "{0:}: {1:}".format(now,text)
        
        self.output_text_field.appendPlainText(txt)

    def clickBox(self, state):
        """Auto update checkbox
        """
        if state == Qt.Checked:
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
            self._output('ups')
        
        self.update_plot()
            
    def selectionChanged(self,i):
        
        try:
            self.data_type = self.OFscanner.post_types[i]
           
            self.filelist.clear()
            self.filelist.addItems(self.OFscanner.ppObjects[self.data_type])
            self.filelist.setCurrentRow(0)
            
            self.data_subset = []
                            
            self.update_plot()
            
        except IndexError:
            self.canvas_layout.mplCanvas.clear()
            
            
    def fieldsSelectionChanged(self):
        
        self.data_subset = getSelectedListItems(self.fieldlist)
        self.current_field_selection[self.data_type] = getSelectedListItems(self.fieldlist)
        self.update_plot()
        
        

def run():
    
    app = QApplication(sys.argv)
    octopix = Octopix(show_gui=True)
    app.exec_()


if __name__ == '__main__':
    run()



