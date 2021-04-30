#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
from pathlib import Path
from datetime import datetime

from canvas import canvasLayout
from fileOps import OFppScanner,are_equal

import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5.QtGui import QPalette, QColor,QDoubleValidator,QIcon
from PyQt5.QtWidgets import QVBoxLayout,QHBoxLayout,QFormLayout,QGridLayout,QAction,qApp
from PyQt5.QtWidgets import QMainWindow,QWidget,QApplication,QCheckBox,QComboBox,\
    QLabel,QLineEdit,QPushButton,QPlainTextEdit,QTabWidget,QListWidget
from PyQt5.QtCore import pyqtSlot,QTimer,Qt


supported_post_types = ['residuals','forces','rigidBodyState','time','fieldMinMax']

class Color(QWidget):

    def __init__(self, color, *args, **kwargs):
        super(Color, self).__init__(*args, **kwargs)
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)


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
        
        

    def __init__(self, *args, **kwargs):
        super(Octopix, self).__init__(*args, **kwargs)

        self.setWindowTitle("Octopix - Visualize your Simulation Progress")
        
        self.initMenubar()

        self.statusBar()
        
        self.setGeometry(300, 300, 1100, 900)
        
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
        #---------------------------
        
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

        self.show()
        
        # Setup a timer to trigger the redraw by calling update_plot.
        self.timer = QTimer()
        self.timer.setInterval(1000)
        #self.timer.timeout.connect(lambda: self.sc.update_plot(self.data_type,self.eval_time_start))
        self.timer.timeout.connect(self.update_plot)
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
            self.listwidget.clear()
             
        stats = self.canvas_layout.mplCanvas.update_plot(self.data_type,self.eval_time_start,self.data_subset)
        self.statistics_text_field.setPlainText(str(stats))

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
            self.output_text_field.appendPlainText('ups')
        
        self.update_plot()
            
    def selectionChanged(self,i):
        
        try:
            self.data_type = self.OFscanner.post_types[i]
            
            if self.data_type == 'forces':
                self.data_subset = ['fx','fxv']
            else:
                self.data_subset = []
            
            self.listwidget.clear()
            self.listwidget.addItems(self.OFscanner.ppObjects[self.data_type])
            
            self.update_plot()
            
        except IndexError:
            self.canvas_layout.mplCanvas.clear()

def main():
    
    app = QApplication(sys.argv)
    w = Octopix()
    app.exec_()


if __name__ == '__main__':
    main()



