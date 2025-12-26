#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

import pandas as pd

from octopix.show.console import Console
from octopix.show.canvas import CanvasLayout
from octopix.data.scanner import OFppScanner
from octopix.data.funcs import getAllListItems,getSelectedListItems,are_equal
from octopix.common.config import supported_post_types,default_field_selection
from octopix.common.config import OctopixConfigurator

from octopost.reader import makeRuntimeSelectableReader
from octopost.parsing import filter_time_and_columns

from PyQt5.QtCore import pyqtSlot,QTimer,Qt
from PyQt5.QtGui import QDoubleValidator,QIcon,QPixmap
from PyQt5.QtWidgets import QMainWindow,QWidget,QApplication,QCheckBox,QComboBox,\
    QLabel,QLineEdit,QPushButton,QListWidget,QVBoxLayout,QHBoxLayout,QFormLayout,\
    QGridLayout,QAction,qApp,QAbstractItemView,QSpacerItem,QSizePolicy,QGroupBox,QFileDialog

from octopix.resources import resources

class Octopix(QMainWindow):


    def initMenubar(self):
        
        menubar = self.menuBar()
        
        exitAct = QAction(QIcon('exit.png'), '&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(qApp.quit)
                
        openAct = QAction(QIcon('open.png'), '&Open', self)
        openAct.setShortcut('Ctrl+O')
        openAct.setStatusTip('Open postProcessing')
        openAct.triggered.connect(self.on_clicked_openPP)
        
        exportAct = QAction(QIcon('export.png'), '&Export', self)
        exportAct.setShortcut('Ctrl+E')
        exportAct.setStatusTip('export statistics data')
        exportAct.triggered.connect(self.console.on_click_exportButton)
        
        saveAct = QAction(QIcon('save.png'), '&Save', self)
        saveAct.setShortcut('Ctrl+S')
        saveAct.setStatusTip('Save data')
        saveAct.triggered.connect(self.console.on_click_saveButton)
        
        
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAct)
        fileMenu.addAction(openAct)
        fileMenu.addAction(exportAct)
        fileMenu.addAction(saveAct)
        
        appearanceMenu = menubar.addMenu('&Appearance')
        plotStyleMenu = appearanceMenu.addMenu('Plot Stlye')
        
        selectDarkStyleAct = QAction('dark',self)
        selectDarkStyleAct.triggered.connect(lambda: self.setPlotStyle('dark'))
        selectBrightStyleAct = QAction('bright',self)
        selectBrightStyleAct.triggered.connect(lambda: self.setPlotStyle('bright'))
        selectClassicStyleAct = QAction('classic',self)
        selectClassicStyleAct.triggered.connect(lambda: self.setPlotStyle('classic'))        

        plotStyleMenu.addAction(selectDarkStyleAct)
        plotStyleMenu.addAction(selectBrightStyleAct)
        plotStyleMenu.addAction(selectClassicStyleAct)
        
        
    def setPlotStyle(self,style):
        
        self.canvas_layout.mplCanvas.style = style 
        self.update()
    

    def __init__(self, show_gui, *args, **kwargs):
        super(Octopix, self).__init__(*args, **kwargs)

        self.setWindowTitle("Octopix - Visualize your Simulation Progress")

        self.statusBar()
        
        self.setGeometry(140, 140, 1250, 1000)
        
        self.config = OctopixConfigurator()
        
        self.wDir = Path.cwd()
        self.data_type = None
        self.data_subset = []
        self.show_all = False
        
        self.OFscanner = OFppScanner(supported_types=supported_post_types, working_dir=self.wDir)
        
        self.current_field_selection = {k:[] for k in supported_post_types}
        self.tmin = {k:0.0 for k in supported_post_types}
        self.tmax = {k:None for k in supported_post_types}
        
        self.tmin_textfield = QLineEdit()
        self.tmin_textfield.setMaximumWidth(100)
        self.tmin_textfield.setValidator(QDoubleValidator())
        self.tmin_textfield.textEdited.connect(self.on_read_eval_start_time)

        self.tmax_textfield = QLineEdit()
        self.tmax_textfield.setMaximumWidth(100)
        self.tmax_textfield.setValidator(QDoubleValidator())
        self.tmax_textfield.textEdited.connect(self.on_read_eval_end_time)

        self.datatype_comboBox = QComboBox()
        self.datatype_comboBox.setMaximumWidth(120)
        self.datatype_comboBox.currentIndexChanged.connect(self.on_datatype_selection_changed)
        
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

        openButton = QPushButton('Open', self)
        openButton.clicked.connect(self.on_clicked_openPP)
        

        dataBox = QGroupBox("Data")
        dataBox.setCheckable(False)
        dataBox.layout = QVBoxLayout() 
        dataBox.layout.addWidget(openButton)
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Data type:"))
        hbox.addWidget(self.datatype_comboBox)
        dataBox.layout.addLayout(hbox)
        #dataBox.layout.addWidget(QLabel("Data type:"))
        #dataBox.layout.addWidget(self.datatype_comboBox)
        dataBox.layout.addWidget(QLabel('Files:'))
        dataBox.layout.addWidget(self.filelist)
        dataBox.layout.addWidget(QLabel('Fields:'))
        dataBox.layout.addWidget(self.fieldlist)
        tbox = QHBoxLayout()
        tbox.addWidget(QLabel("Tmin:"))
        tbox.addWidget(self.tmin_textfield)
        tbox.addWidget(QLabel("Tmax:"))
        tbox.addWidget(self.tmax_textfield)
        dataBox.layout.addLayout(tbox)
        dataBox.setLayout(dataBox.layout)        

        # the tabs        
        self.console = Console()
        
        # the canvas 
        self.canvas_layout = CanvasLayout(self.config['canvas'])
        
        # the control  
        auto_update_checkBox = QCheckBox("Autoupdate",self)
        auto_update_checkBox.setChecked(self.config.getboolean('autoupdate','active_on_start'))
        auto_update_checkBox.stateChanged.connect(self.on_auto_update_clicked)

        show_all_checkBox = QCheckBox("Show All", self)
        show_all_checkBox.setChecked(False)
        show_all_checkBox.stateChanged.connect(self.on_show_all_clicked)
        
        autoupdate_interval = QLineEdit()
        autoupdate_interval.setMaximumWidth(100)
        autoupdate_interval.setValidator(QDoubleValidator(0.1,1000.,2))
        autoupdate_interval.setText("1.0")  
        autoupdate_interval.textEdited.connect(self.on_read_autoupdate_interval)
                
        reload_button = QPushButton('Reload', self)
        reload_button.setToolTip('Reload the data')
        reload_button.setMaximumWidth(100)
        reload_button.clicked.connect(self.on_reload_data)

        gb = QGroupBox("Control")
        gb.setCheckable(False)
        gb.layout = QVBoxLayout()
        gb.layout.addWidget(auto_update_checkBox)
        gb.layout.addWidget(show_all_checkBox)
        gb.layout.addWidget(QLabel("Interval:"))
        gb.layout.addWidget(autoupdate_interval)
        gb.layout.addWidget(reload_button)
        gb.setLayout(gb.layout)

        controls_layout = QVBoxLayout()
        controls_layout.addWidget(dataBox)
        controls_layout.addWidget(gb)
        controls_layout.addStretch(1)

        octoLabel = QLabel(self)
        octoLabel.setPixmap(QPixmap(':/images/octo_croped.png').scaled(120,120,Qt.KeepAspectRatio))
        controls_layout.addWidget(octoLabel)
         
        outer_layout = QGridLayout()
        outer_layout.addLayout(controls_layout,0,0,3,1,Qt.AlignTop)
        outer_layout.addLayout(self.canvas_layout,0,1,2,1)
        outer_layout.addWidget(self.console,2,1)
        
        outer_layout.setColumnMinimumWidth(0,220)
        outer_layout.setColumnStretch(0,0)
        outer_layout.setColumnStretch(1,1)
        outer_layout.setRowStretch(0,1)
        outer_layout.setRowStretch(1,1)

        widget = QWidget()
        widget.setLayout(outer_layout)
        
        self.setCentralWidget(widget)

        self.update()
        
        if self.config.getboolean('appearance','dark_mode'):
            self.setStyleSheet(
                "background-color:rgb(40, 40, 40); color:#F0F0F0;"
                "QLabel { color:#D8D8D8; }"
                "QGroupBox { border:1px solid rgb(70,70,70); margin-top:10px; color:#F0F0F0; }"
                "QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding:0 4px; background:rgb(30,30,30); }"
                "QLineEdit { selection-background-color:#A8E10C; selection-color:#333333; }"
                "QListWidget { selection-background-color:#A8E10C; selection-color:#333333; }"
                "QTableView { selection-background-color:#A8E10C; selection-color:#333333; }"
                "QHeaderView::section { background-color:rgb(30,30,30); color:#F0F0F0; }"
                "QMenuBar { background-color:rgb(40,40,40); color:#F0F0F0; }"
                "QMenuBar::item:selected { background-color:#A8E10C; color:#333333; }"
                "QMenu { background-color:rgb(40,40,40); color:#F0F0F0; }"
                "QMenu::item:selected { background-color:#A8E10C; color:#333333; }"
            )
            self.console.output_text_field.setStyleSheet("background-color:rgb(55, 55, 55); color:#F0F0F0;")
            self.console.set_dark_mode()
            self.filelist.setStyleSheet("background-color:rgb(55, 55, 55); color:#F0F0F0;")
            self.fieldlist.setStyleSheet("background-color:rgb(55, 55, 55); color:#F0F0F0;")
            self.tmin_textfield.setStyleSheet("background-color:rgb(55, 55, 55); color:#F0F0F0;")
            self.tmax_textfield.setStyleSheet("background-color:rgb(55, 55, 55); color:#F0F0F0;")
        
        self.initMenubar()
        
        if show_gui:
            self.show()
        else:
            self.canvas_layout.mplCanvas.savePlot()
            sys.exit(0)
        
        # Timer to trigger the reloading and redrawing by calling te update function.
        self.timer = QTimer()
        #self.timer.setInterval(1000)
        self.on_read_autoupdate_interval(autoupdate_interval.text())
        self.timer.timeout.connect(self.update)
        self.on_auto_update_clicked(auto_update_checkBox.isChecked())


    def update(self):
                
        self.OFscanner.scan(working_dir=self.wDir)
        
        currentFoundItems = self.OFscanner.post_types

        currentLoadedItems = [self.datatype_comboBox.itemText(i) for i in range(self.datatype_comboBox.count())]
        
        if not are_equal(currentFoundItems,currentLoadedItems):
            self.canvas_layout.mplCanvas.clear()
            self.datatype_comboBox.clear()
            self.datatype_comboBox.addItems(self.OFscanner.post_types)
        
        if len(self.OFscanner.post_types) == 0:
            self.filelist.clear()
        else:
        
            try:
                data_name = self.filelist.currentItem().text()
            except:
                data_name = None
    
            # load the data and provide the dataframe to canvas 
            # data_type defines the reader
            reader = makeRuntimeSelectableReader(reader_name=self.data_type, base_dir=data_name, case_dir=self.wDir)
            fields = reader.fields()
            
            if self.OFscanner.ppObjects:
                df = filter_time_and_columns(
                    df=reader.data,
                    time_start=self.tmin[self.data_type],
                    time_end=self.tmax[self.data_type],
                    data_subset=self.data_subset
                    )
                if self.show_all and (self.tmin[self.data_type] is not None or self.tmax[self.data_type] is not None):
                    df_full = filter_time_and_columns(
                        df=reader.data,
                        time_start=None,
                        time_end=None,
                        data_subset=self.data_subset
                    )
                else:
                    df_full = None
            else:
                df = pd.DataFrame()
                df_full = None
    
            self.canvas_layout.mplCanvas.update_plot(df, self.data_type, data_name, full_data=df_full)
            
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
            
            self.console.update(df)
        

    def on_clicked_openPP(self):
        
        folderpath = QFileDialog.getExistingDirectory(self, 'Select postProcessing Folder',options=QFileDialog.DontUseNativeDialog)
        
        self.console.sendToOutput('Loading data from: {0:}'.format(folderpath))

        self.wDir = Path(folderpath).parent
        


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

    def on_show_all_clicked(self, state):
        if state == Qt.Checked or state:
            self.show_all = True
        elif state == Qt.Unchecked or not state:
            self.show_all = False
        else:
            raise TypeError
        self.update()
    

    @pyqtSlot()
    def on_reload_data(self):
        """Reload data push button
        """
        self.console.sendToOutput('Reloading data')
        self.update()

    def on_read_eval_start_time(self,text):
        try:
            self.tmin[self.data_type] = float(text)
        except:
            self.console.sendToOutput('ups')
        
        self.update()

    def on_read_eval_end_time(self,text):
        if text == "":
            self.tmax[self.data_type] = None
        else:
            try:
                self.tmax[self.data_type] = float(text)
            except:
                self.console.sendToOutput('ups')
                return
        
        self.update()
    
    def on_read_autoupdate_interval(self,text):
        try:
            self.timer.setInterval(int(float(text)*1000))
        except:
            self.console.sendToOutput('ups')        
    
    def on_datatype_selection_changed(self,i):
        
        try:
            self.data_type = self.OFscanner.post_types[i]
           
            self.filelist.clear()
            self.filelist.addItems(self.OFscanner.ppObjects[self.data_type])
            self.filelist.setCurrentRow(0)
            
            self.tmin_textfield.setText("{:g}".format(self.tmin[self.data_type]))
            if self.tmax[self.data_type] is None:
                self.tmax_textfield.setText("")
            else:
                self.tmax_textfield.setText("{:g}".format(self.tmax[self.data_type]))
                   
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
