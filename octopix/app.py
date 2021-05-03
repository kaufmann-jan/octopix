#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd

from octopix.show.console import Console
from octopix.show.canvas import CanvasLayout
from octopix.data.scanner import OFppScanner
from octopix.data.reader import makeRuntimeSelectableReader,prepare_data
from octopix.data.funcs import getAllListItems,getSelectedListItems,are_equal
from octopix.common.config import supported_post_types,default_field_selection
from octopix.common.config import OctopixConfigurator

from PyQt5.QtCore import pyqtSlot,QTimer,Qt
from PyQt5.QtGui import QDoubleValidator,QIcon
from PyQt5.QtWidgets import QMainWindow,QWidget,QApplication,QCheckBox,QComboBox,\
    QLabel,QLineEdit,QPushButton,QListWidget,QVBoxLayout,QHBoxLayout,QFormLayout,\
    QGridLayout,QAction,qApp,QAbstractItemView,QSpacerItem,QSizePolicy

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
        
        self.config = OctopixConfigurator()
        
        self.OFscanner = OFppScanner(supported_types=supported_post_types, working_dir=Path.cwd())
        
        self.data_type = None
        self.data_subset = []
        self.eval_time_start = 0.0
        
        self.current_field_selection = {k:[] for k in supported_post_types}
        
        settings_layout = QVBoxLayout()
        
        self.tmin_textfield = QLineEdit()
        self.tmin_textfield.setMaximumWidth(100)
        self.tmin_textfield.setValidator(QDoubleValidator())
        self.tmin_textfield.textEdited.connect(self.on_read_eval_start_time)

        self.datatype_comboBox = QComboBox()
        self.datatype_comboBox.setMaximumWidth(100)
        self.datatype_comboBox.currentIndexChanged.connect(self.on_datatype_selection_changed)

        flo = QFormLayout()
        
        flo.addRow(QLabel("Tmin:"), self.tmin_textfield)
        flo.addRow(QLabel("Data type:"),self.datatype_comboBox)

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
        self.fieldlist.itemSelectionChanged.connect(self.on_fieldlist_selection_changed)              
        
        settings_layout.addWidget(QLabel('Files:'))
        settings_layout.addWidget(self.filelist)
        settings_layout.addWidget(QLabel('Fields:'))
        settings_layout.addWidget(self.fieldlist)
        settings_layout.addStretch(1)

        # the tabs        
        self.console = Console()
        
        self.auto_update_checkBox = QCheckBox("Autoupdate",self)
        self.auto_update_checkBox.setChecked(self.config.getboolean('autoupdate','active_on_start'))
        self.auto_update_checkBox.stateChanged.connect(self.on_auto_update_clicked)
        
        reload_button = QPushButton('Reload', self)
        reload_button.setToolTip('Reload the data')
        reload_button.clicked.connect(self.on_reload_data)
        
        hbox = QHBoxLayout()
        hbox.addWidget(self.auto_update_checkBox)
        hbox.addStretch(1)
        hbox.addWidget(reload_button)
        
        settings_layout.addLayout(hbox)   
         
        self.canvas_layout = CanvasLayout(self.config['canvas'])

        outer_layout = QGridLayout()
        outer_layout.addLayout(settings_layout,0,0,3,1)
        outer_layout.addLayout(self.canvas_layout,0,2)
        outer_layout.addWidget(self.console,2,2)
        outer_layout.setColumnStretch(0,0)
        outer_layout.setColumnStretch(2,2)
        outer_layout.setRowStretch(0,2)
        outer_layout.setRowStretch(2,1)

        widget = QWidget()
        widget.setLayout(outer_layout)
        
        self.setCentralWidget(widget)

        self.update()
        
        if self.config.getboolean('appearance','dark_mode'):
            self.setStyleSheet("background-color:rgb(130, 138, 140);")
            self.console.output_text_field.setStyleSheet("background-color:rgb(139, 146, 148);")
            self.console.statistics_text_field.setStyleSheet("background-color:rgb(139, 146, 148);")
            self.filelist.setStyleSheet("background-color:rgb(139, 146, 148);")
            self.fieldlist.setStyleSheet("background-color:rgb(139, 146, 148);")
        
        if show_gui:
            self.show()
        else:
            self.canvas_layout.mplCanvas.savePlot()
            sys.exit(0)
            
        
        # Timer to trigger the reloading and redrawing by calling te update function.
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update)
        self.on_auto_update_clicked(self.auto_update_checkBox.isChecked())


    def update(self):
                
        self.OFscanner.scan()
        
        currentFoundItems = self.OFscanner.post_types
        
        currentLoadedItems = [self.datatype_comboBox.itemText(i) for i in range(self.datatype_comboBox.count())]
        
        if not are_equal(currentFoundItems,currentLoadedItems):
            self.canvas_layout.mplCanvas.clear()
            self.datatype_comboBox.clear()
            self.datatype_comboBox.addItems(self.OFscanner.post_types)
        
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
        
        self.console.statistics_text_field.setPlainText(str(des))


    def on_auto_update_clicked(self, state):
        """Auto update checkbox
        
        Parameter
        ---------
        
        state : Qt.CheckState or bool
            Qt.Checked,Qt.Unchecked
        """
        if state == Qt.Checked or state:
            self.console.sendToOutput('Autoupdate on')
            self.timer.start()
        elif state == Qt.Unchecked or not state:
            self.console.sendToOutput('Autoupdate off')
            self.timer.stop()
        else:
            raise TypeError
    

    @pyqtSlot()
    def on_reload_data(self):
        """Reload data push button
        """
        self.console.sendToOutput('Reloading data')
        self.update()

    def on_read_eval_start_time(self,text):
        try:
            self.eval_time_start = float(text)
        except:
            self.console.sendToOutput('ups')
        
        self.update()
            
    def on_datatype_selection_changed(self,i):
        
        try:
            self.data_type = self.OFscanner.post_types[i]
           
            self.filelist.clear()
            self.filelist.addItems(self.OFscanner.ppObjects[self.data_type])
            self.filelist.setCurrentRow(0)
            
            self.data_subset = []
                            
            self.update()
            
        except IndexError:
            self.canvas_layout.mplCanvas.clear()
            
            
    def on_fieldlist_selection_changed(self):
        
        self.data_subset = getSelectedListItems(self.fieldlist)
        self.current_field_selection[self.data_type] = getSelectedListItems(self.fieldlist)
        self.update()
        
        

def run():
    
    app = QApplication(sys.argv)
    octopix = Octopix(show_gui=True)
    app.exec_()


if __name__ == '__main__':
    run()



