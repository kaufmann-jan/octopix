#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import QWidget,QTabWidget,QPlainTextEdit,QVBoxLayout,QHBoxLayout,QPushButton,QFileDialog
from PyQt5.QtGui import QIcon

import pandas as pd

class StatisticsTextField(QPlainTextEdit):
    
    def __init___(self,*args,**kwargs):
        
        super(StatisticsTextField,self).__init__(*args,**kwargs)
        
        self.setReadOnly(True)
        self.setStyleSheet("background-color:lightgray")
        
        self.df = pd.DataFrame()

    def setPlainText(self, df):
        
        self.df = df

        try:
            self.df = df.describe().T.loc[:,['count','mean','min','max','std']]
        except:
            self.df = pd.DataFrame()

        QPlainTextEdit.setPlainText(self,str(self.df))



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
        
        textClearButton = QPushButton('Clear')
        textClearButton.clicked.connect(self.on_click_clearTextButton)
        
        textExportButton = QPushButton('Export')
        textExportButton.clicked.connect(self.on_click_exportTextButton)
        
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(textClearButton)
        hbox.addWidget(textExportButton)
        
        self.output_tab.layout.addLayout(hbox)
        
        self.output_tab.setLayout(self.output_tab.layout)
        
        self.statistics_text_field = StatisticsTextField()
          
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
    
                
    def on_click_exportButton(self):
        
        self.sendToOutput('exporting stats data')
        
        fileName, fileType = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","CSV Files (*.csv);;Text Files (*.txt);;All Files (*)"
                                                 ,options=QFileDialog.DontUseNativeDialog)
        if fileName:
            if "(*.csv)" in fileType:
                if Path(fileName).suffix != '.csv':
                    fileName += '.csv'
                self.statistics_text_field.df.to_csv(fileName,index=True)
            else:
                with open(fileName,'w') as f:
                    f.write(self.statistics_text_field.toPlainText())
    
    def sendToOutput(self,text):
        
        now = datetime.now().strftime("%H:%M:%S")
        txt = "{0:}: {1:}".format(now,text)
        
        self.output_text_field.appendPlainText(txt)
        
    def on_click_exportTextButton(self):
        
        self.sendToOutput('exporting text data')
        
        fileName, _ = QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","All Files (*);;Text Files (*.txt)"
                                                 ,options=QFileDialog.DontUseNativeDialog)
        if fileName:
            with open(fileName,'w') as f:
                f.write(self.output_text_field.toPlainText())        
    
    def on_click_clearTextButton(self):
        
        self.output_text_field.clear()
        
        