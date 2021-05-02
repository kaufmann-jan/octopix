#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime

from PyQt5.QtWidgets import QWidget,QTabWidget,QPlainTextEdit,QVBoxLayout,QHBoxLayout,QPushButton,QFileDialog
from PyQt5.QtGui import QIcon


class Console(QTabWidget):
    
    def __init__(self,*args,**kwargs):
        
        super(Console,self).__init__(*args,**kwargs)
        
        #self.tabs = QTabWidget(self)
        self.output_tab = QWidget()
        self.statistics_tab = QWidget()
        
        # Add tabs
        self.addTab(self.statistics_tab,"Statistics") 
        self.addTab(self.output_tab,"Output")
         
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
        exportButton.setToolTip('Reload the data')
        exportButton.clicked.connect(self.on_click_exportButton)
        
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(exportButton)
        
        self.statistics_tab.layout.addLayout(hbox)
        
        self.statistics_tab.setLayout(self.statistics_tab.layout)
    
    
    def export_stats(self):
        
        # from:
        # https://pythonspot.com/pyqt5-file-dialog/
        
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","All Files (*);;Text Files (*.txt)", options=options)
        if fileName:
            with open(fileName,'w') as f:
                f.write(self.statistics_text_field.toPlainText())
        
        
    def on_click_exportButton(self):
        self.sendToOutput('exporting stats data')
        self.export_stats()
    
    def sendToOutput(self,text):
        
        now = datetime.now().strftime("%H:%M:%S")
        txt = "{0:}: {1:}".format(now,text)
        
        self.output_text_field.appendPlainText(txt)
        
        
        
        