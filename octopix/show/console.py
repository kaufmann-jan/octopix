#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from pathlib import Path
import io
import csv

from PyQt5.QtWidgets import QWidget,QTabWidget,QPlainTextEdit,QVBoxLayout,QHBoxLayout,QPushButton,QFileDialog,\
    QTableView,qApp,QTextEdit
from PyQt5.QtCore import QAbstractTableModel, Qt,QEvent
from PyQt5.QtGui import QKeySequence

import pandas as pd

class OctopixTableView(QTableView):
    
    def stats(self):
        try:
            des = self.df.describe().T.loc[:,['count','mean','min','max','std']]
        except:
            des = pd.DataFrame()
        
        return des
    
    def __init__(self,data=pd.DataFrame(),*args,**kwargs):
        
        super(OctopixTableView,self).__init__(*args,**kwargs)
        
        self.setData(data)
        
        self.installEventFilter(self)
        
        
    def update(self,data, *args, **kwargs):
        
        self.setData(data)

        return QTableView.update(self, *args, **kwargs)

    def setData(self,data):
        
        self.df = data
        
        self.setModel(PandasModel(self.stats()))
        
    def eventFilter(self, source, event):
        if (event.type() == QEvent.KeyPress and
            event.matches(QKeySequence.Copy)):
            self.copySelection()
            return True
        return super().eventFilter(source, event)

    def copySelection(self):
        """header and index are not copied. 
        how to extend to allow for right click on selection?
        """
        selection = self.selectedIndexes()
        
        if selection:
            rows = sorted(index.row() for index in selection)
            columns = sorted(index.column() for index in selection)
            rowcount = rows[-1] - rows[0] + 1
            colcount = columns[-1] - columns[0] + 1
            table = [[''] * colcount for _ in range(rowcount)]
            
            for index in selection:
                row = index.row() - rows[0]
                column = index.column() - columns[0]
                table[row][column] = index.data()
                
            stream = io.StringIO()
            csv.writer(stream).writerows(table)
            qApp.clipboard().setText(stream.getvalue())
              

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
                return "{0:g}".format(self._data.iloc[index.row(), index.column()])
            
        return None

    def headerData(self, col, orientation, role):
        
        try:
            if orientation == Qt.Horizontal and role == Qt.DisplayRole:
                return self._data.columns[col]
            if orientation == Qt.Vertical and role == Qt.DisplayRole:
                return self._data.index[col]
            return None
        
        except IndexError as e:
            pass


class TimeSeriesData(object):
    
    def __init__(self,df=pd.DataFrame(data={'time':[]})):
        
        ## this should become some kind of container for the data (frame)
        ## which implemnts some kind of statitics, maybe sub-setting
        ## ...etc
        
        self.df = df

    def stats(self):
        try:
            des = self.df.describe().T.loc[:,['count','mean','min','max','std']]
        except:
            des = pd.DataFrame()
        
        return des


class OutputTextField(QPlainTextEdit):
    
    def __init__(self,*args,**kwargs):
        
        super(OutputTextField,self).__init__(*args,**kwargs)

        self.setReadOnly(True)
        self.setStyleSheet("background-color:rgb(211,211,211)")
        


class Console(QTabWidget):
    
    def __init__(self,*args,**kwargs):
        
        super(Console,self).__init__(*args,**kwargs)
        
        self.output_tab = QWidget()
        self.table_tab = QWidget()
        
        # Add tabs
        self.addTab(self.table_tab, "Table")
        self.addTab(self.output_tab,"Output")
        
        self.output_text_field = OutputTextField()
        
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
        
        exportButton = QPushButton('Export')
        exportButton.setToolTip('Export the statistics')
        exportButton.clicked.connect(self.on_click_exportButton)
        
        saveButton = QPushButton('Save')
        saveButton.setToolTip('Save the data')
        saveButton.clicked.connect(self.on_click_saveButton)
        
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(saveButton)
        hbox.addWidget(exportButton)
               
        self.view = OctopixTableView()
        
        self.table_tab.layout = QVBoxLayout()
        self.table_tab.layout.addWidget(self.view)
        self.table_tab.layout.addLayout(hbox)
        self.table_tab.setLayout(self.table_tab.layout)
                
    
    def update(self,data):
        self.view.update(data)


    def on_click_saveButton(self):
        
        fileName, fileType = QFileDialog.getSaveFileName(self,"Saving the data","","CSV Files (*.csv);;Text Files (*.txt);;All Files (*)"
                                                 ,options=QFileDialog.DontUseNativeDialog)
        if fileName:
            if "(*.csv)" in fileType:
                if Path(fileName).suffix != '.csv':
                    fileName += '.csv'
                self.view.df.to_csv(fileName,index=True)
            else:
                with open(fileName,'w') as f:
                    f.write(self.view.df.to_string(index=True))
                    
            self.sendToOutput('saving data')

    
                
    def on_click_exportButton(self):
        
        fileName, fileType = QFileDialog.getSaveFileName(self,"Exporting the statistics data","","CSV Files (*.csv);;Text Files (*.txt);;All Files (*)"
                                                 ,options=QFileDialog.DontUseNativeDialog)
        if fileName:
            if "(*.csv)" in fileType:
                if Path(fileName).suffix != '.csv':
                    fileName += '.csv'
                self.view.stats().to_csv(fileName,index=True)
            else:
                with open(fileName,'w') as f:
                    f.write(self.view.stats().to_string())
                    
            self.sendToOutput('exporting stats data')
    
    def sendToOutput(self,text):
        
        now = datetime.now().strftime("%H:%M:%S")
        
        txt = "{0:}: {1:}".format(now,text)
        
        self.output_text_field.appendPlainText(txt)
        
    def on_click_exportTextButton(self):
        
        self.sendToOutput('exporting text data')
        
        fileName, _ = QFileDialog.getSaveFileName(self,"Exporting the statistics data","","All Files (*);;Text Files (*.txt)"
                                                 ,options=QFileDialog.DontUseNativeDialog)
        if fileName:
            with open(fileName,'w') as f:
                f.write(self.output_text_field.toPlainText())        
    
    def on_click_clearTextButton(self):
        
        self.output_text_field.clear()
        
        