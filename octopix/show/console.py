#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import QWidget,QTabWidget,QPlainTextEdit,QVBoxLayout,QHBoxLayout,QPushButton,QFileDialog,\
    QTableView
from PyQt5.QtCore import QAbstractTableModel, Qt


import pandas as pd

class OctopixTableView(QTableView):
    
    def stats(self,data):
        try:
            df = data.describe().T.loc[:,['count','mean','min','max','std']]
        except:
            df = pd.DataFrame()
        
        return df
    
    def __init__(self,data=pd.DataFrame(),*args,**kwargs):
        
        super(OctopixTableView,self).__init__(*args,**kwargs)
        
        self.setModel(PandasModel(self.stats(data)))
        #[self.setColumnWidth(col,100) for col in range(len(data.columns))]
        
        
    def update(self,data, *args, **kwargs):
        
        self.setModel(PandasModel(self.stats(data)))

        return QTableView.update(self, *args, **kwargs)



class PandasModel(QAbstractTableModel):

    def __init__(self, data=pd.DataFrame()):
        QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parnet=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return "{0:.4g}".format(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return self._data.index[col]
        return None



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
        self.table_tab = QWidget()
        
        # Add tabs
        self.addTab(self.statistics_tab,"Statistics") 
        self.addTab(self.output_tab,"Output")
        #self.addTab(self.table_tab, "PANDAS")
         
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
        
        dummy = pd.DataFrame(data={'foo':[],'bar':[],'baz':[]})
        
        self.view = OctopixTableView(dummy)
        self.addTab(self.view,"PANDAS")
        
        
    
    def update(self,data):
        self.view.update(data)
    
                
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
        
        