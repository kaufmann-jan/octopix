#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton,QVBoxLayout,\
    QHBoxLayout,QGroupBox,QTreeWidget,QTreeWidgetItem,QMenu,QFileDialog,QInputDialog

from octopix.data.simulation import Simulation


class Simulations(list):
    
    def __init__(self):
        super(Simulations,self).__init__()
    
    def locations(self):
        return [sim.location for sim in self]

    def names(self):
        return [sim.name for sim in self]
    
    def load(self,working_dir):
        
        sim_name = working_dir.stem

        # if there is a simulation in the given working dir and this simulation is not yet 
        # loaded, append
        
        if working_dir not in self.locations(): 
            s = Simulation(location=working_dir,name=sim_name)
        else:
            print(f'already loaded sim data from {working_dir}')
            return False
        
        if s.container:
            self.append(s)
            return True
        else:
            print(f'no sim data found in {working_dir}')
            return False
        

class SimulationsBox(QGroupBox):

    def initTree(self):
        
        self.tree = QTreeWidget()
        #self.tree.setFocusPolicy(Qt.NoFocus)
        self.tree.setAllColumnsShowFocus(True)
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(['Name','Path'])
    
        self.tree.itemChanged[QTreeWidgetItem, int].connect(self.get_item)
        
        # rename with right click
        #self.tree.setContextMenuPolicy(Qt.CustomContextMenu) # ActionsContexdMenu ????       
        #self.tree.customContextMenuRequested.connect(self.simTreeCustomContextMenuRequested)
        
    def initButtons(self):

        self.load_button = QPushButton("Load")
        self.load_button.clicked.connect(self.on_load)
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.on_delete)
        self.rename_button = QPushButton("Rename")
        self.rename_button.clicked.connect(self.on_rename)
        self.moveup_button = QPushButton("Up")
        self.moveup_button.clicked.connect(self.on_moveup)
        self.down_button = QPushButton("Down")
        self.down_button.clicked.connect(self.on_movedown)
    
    def __init__(self,*args,**kwargs):

        super(SimulationsBox,self).__init__('Simulations',*args,**kwargs)

        self.setCheckable(False)
        
        self.initTree()
        self.initButtons()
        
        button_vbox = QVBoxLayout()
        button_vbox.addWidget(self.load_button)
        button_vbox.addWidget(self.rename_button)
        button_vbox.addWidget(self.remove_button)
        button_vbox.addWidget(self.moveup_button)
        button_vbox.addWidget(self.down_button)
        button_vbox.addStretch(1)
        
        hbox = QHBoxLayout()
        hbox.addWidget(self.tree)
        hbox.addLayout(button_vbox)

        self.setLayout(hbox)
        
        self.simulations = Simulations()
        
        # try to load a new simulation in the current working dir on start
        self.load(Path.cwd())


    def on_moveup(self):
                
        item = self.tree.currentItem()
        index = self.tree.indexOfTopLevelItem(item)
    
        if index > 0:
            
            self.simulations[index - 1],self.simulations[index] = self.simulations[index],self.simulations[index - 1]
            
            self.tree.takeTopLevelItem(index)
            self.tree.insertTopLevelItem(index - 1,item)
            self.tree.setCurrentItem(item)
            
    
    def on_movedown(self):

        item = self.tree.currentItem()
        index = self.tree.indexOfTopLevelItem(item)
         
        if index < self.tree.topLevelItemCount() - 1:
            
            self.simulations[index + 1],self.simulations[index] = self.simulations[index],self.simulations[index + 1]
            
            self.tree.takeTopLevelItem(index)
            self.tree.insertTopLevelItem(index + 1,item)
            self.tree.setCurrentItem(item)
            

    def on_rename(self):
        
        new_name, ok = QInputDialog.getText(self, 'Rename Simulation', 'New Name:')
        
        if ok:
            item = self.tree.currentItem()
            index = self.tree.indexOfTopLevelItem(item)
        
            item.setText(0,new_name)
            self.simulations[index].name = new_name

    def on_delete(self):
        
        item = self.tree.currentItem()        
        index = self.tree.indexOfTopLevelItem(item)
        
        if (len(self.simulations)) > 0:
            self.simulations.pop(index) 
        
        self.tree.takeTopLevelItem(index)

            
    def on_load(self):

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        options |= QFileDialog.ShowDirsOnly
        options |= QFileDialog.ReadOnly

        working_dir = Path(QFileDialog.getExistingDirectory(self, 'Select postProcessing Folder',options=options)).parent.absolute()

        print(f'Loading data from: {working_dir}')
        
        self.load(working_dir)
        
        
    def load(self,working_dir):
        
        name = working_dir.stem

        s = self.simulations.load(working_dir)
        
        if s:
            item = QTreeWidgetItem()
            item.setFlags(item.flags()| Qt.ItemIsUserCheckable)
            item.setCheckState(0,Qt.Checked)
            item.setText(0,name)
            item.setText(1,str(working_dir))
            
            self.tree.addTopLevelItem(item)
            self.tree.setCurrentItem(item)
        
        

    def get_item(self, item, column):
        if item.checkState(column) == Qt.Checked:
            print(f'{item.text(column)} was checked')
        else:
            print(f'{item.text(column)} was unchecked')
            
        
        
    def simTreeCustomContextMenuRequested(self):
        """For mouse right click. tbd"""
        menu = QMenu(self)
        #menu.addAction()
        item = self.tree.currentItem()
        index = self.tree.indexOfTopLevelItem(item)
        print('fooooo',index)



class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow,self).__init__()

        self.setWindowTitle("Simbox testing....")
        
        self.simulationsBox = SimulationsBox()
        
        self.setCentralWidget(self.simulationsBox)




app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()