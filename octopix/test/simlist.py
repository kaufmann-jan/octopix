#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path


from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton,QVBoxLayout,\
    QHBoxLayout,QGroupBox, QTreeWidget, QTreeWidgetItem, QMenu


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Simlist testing....")
        
        
        load_button = QPushButton("Load")
        load_button.clicked.connect(lambda: self.on_load('foo'))
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(self.on_delete)
        rename_button = QPushButton("Rename")
        rename_button.clicked.connect(self.on_rename)
        up_button = QPushButton("Up")
        up_button.clicked.connect(self.on_move_up)
        down_button = QPushButton("Down")
        down_button.clicked.connect(self.on_move_down)

        button_vbox = QVBoxLayout()
        button_vbox.addWidget(load_button)
        button_vbox.addWidget(rename_button)
        button_vbox.addWidget(remove_button)
        button_vbox.addWidget(up_button)
        button_vbox.addWidget(down_button)
        button_vbox.addStretch(1)

        self.sim_tree = QTreeWidget()
        #self.sim_tree.setFocusPolicy(Qt.NoFocus)
        self.sim_tree.setAllColumnsShowFocus(True)
        self.sim_tree.setColumnCount(2)
        self.sim_tree.setHeaderLabels(['Name','Path'])
    
        self.sim_tree.itemChanged[QTreeWidgetItem, int].connect(self.get_item)
        
        # rename with right click
        self.sim_tree.setContextMenuPolicy(Qt.CustomContextMenu) # ActionsContexdMenu ????       
        self.sim_tree.customContextMenuRequested.connect(self.simTreeCustomContextMenuRequested)

        
        if True:            
            self.on_load('v 20 kn')
            self.on_load('v 21 kn')
        
        hbox = QHBoxLayout()
        hbox.addWidget(self.sim_tree)
        hbox.addLayout(button_vbox)
        
        sim_groupBox = QGroupBox('Simulations')
        sim_groupBox.setCheckable(False)
        
        sim_groupBox.setLayout(hbox)
        
        # Set the central widget of the Window.
        self.setCentralWidget(sim_groupBox)

    def on_move_up(self):
                
        item = self.sim_tree.currentItem()
        index = self.sim_tree.indexOfTopLevelItem(item)
    
        if index > 0:
            self.sim_tree.takeTopLevelItem(index)
            self.sim_tree.insertTopLevelItem(index - 1,item)
            self.sim_tree.setCurrentItem(item)
    
    def on_move_down(self):

        item = self.sim_tree.currentItem()
        index = self.sim_tree.indexOfTopLevelItem(item)
         
        if index < self.sim_tree.topLevelItemCount() -1:
            self.sim_tree.takeTopLevelItem(index)
            self.sim_tree.insertTopLevelItem(index + 1,item)
            self.sim_tree.setCurrentItem(item)


    def on_rename(self):
        
        item = self.sim_tree.currentItem()        
        item.setText(0,'renamed')


    def on_delete(self):
        
        item = self.sim_tree.currentItem()        
        index = self.sim_tree.indexOfTopLevelItem(item)
        self.sim_tree.takeTopLevelItem(index)
        

    def on_load(self,name):

        item = QTreeWidgetItem()
        item.setFlags(item.flags()| Qt.ItemIsUserCheckable)
        item.setCheckState(0,Qt.Checked)
        item.setText(0,name)
        item.setText(1,str(Path(Path.cwd(),name)))
        
        self.sim_tree.addTopLevelItem(item)
        self.sim_tree.setCurrentItem(item)
        
        
    def simTreeCustomContextMenuRequested(self):
        
        menu = QMenu(self)
        #menu.addAction()
        item = self.sim_tree.currentItem()
        index = self.sim_tree.indexOfTopLevelItem(item)
        print('fooooo',index)
    

    def get_item(self, item, column):
        if item.checkState(column) == Qt.Checked:
            #print(f'{item.text(column)} was checked')
            print('{0:} was checked'.format(item.text(column)))
        else:
            #print(f'{item.text(column)} was unchecked')
            print('{0:} was unchecked'.format(item.text(column)))


app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()