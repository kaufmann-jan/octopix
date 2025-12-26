#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg,NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5.QtWidgets import QVBoxLayout

import numpy as np
import pandas as pd

from octopix.data.funcs import are_equal

class CanvasLayout(QVBoxLayout):

    def __init__(self, canvas_settings={},*args, **kwargs):
        super(CanvasLayout,self).__init__(*args, **kwargs)
        
        self.mplCanvas = MplCanvas(settings=canvas_settings)
        self.toolbar = NavigationToolbar(self.mplCanvas,None)
        
        self.addWidget(self.toolbar)
        self.addWidget(self.mplCanvas)


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100,settings={}):
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)
       
        self.data = pd.DataFrame()
        self._plot_refs = None
        self._plot_refs_full = None
        self._mean_refs = None
        self.current_data_type = None
        self.current_data_file = None
        self.fields = None
        self.show_all = False
        self.show_mean = False
        self.style = settings.get('style','classic')
        self._base_figsize = (width, height)

    def resizeEvent(self, event):
        super(MplCanvas, self).resizeEvent(event)
        self._update_font_sizes()
        self.draw_idle()

    def _font_size(self):
        width, height = self.fig.get_size_inches()
        base_w, base_h = self._base_figsize
        scale = min(width / base_w, height / base_h)
        return max(6, int(8 * scale))

    def _update_font_sizes(self):
        size = self._font_size()
        self.axes.xaxis.label.set_size(size + 1)
        self.axes.yaxis.label.set_size(size + 1)
        self.axes.tick_params(labelsize=size)
        legend = self.axes.get_legend()
        if legend is not None:
            for text in legend.get_texts():
                text.set_fontsize(size)

                
    def setPlotStyle(self):
        
        if self.style == 'classic':
            
            fig_facecolor = 'white'
            axes_facecolor = 'white'
            grid_color = 'black'
            text_color = 'black'
            spines_visible = True
            grid_linestyle = '-'
                           
        elif self.style == 'bright':
            fig_facecolor = np.array([204.,213,230])/255.
            axes_facecolor = np.array([173.,182,199])/255.
            text_color = 'black'
            grid_color = 'white'
            spines_visible = False
            grid_linestyle = ':'
            
        elif self.style == 'dark':
            fig_facecolor = np.array([129, 140, 143])/255.
            axes_facecolor = np.array([141, 154, 158])/255.
            grid_color = 'lightgray'
            text_color = 'white'
            spines_visible = False
            grid_linestyle = ':'
            

        self.fig.set_facecolor(fig_facecolor)
        self.axes.grid(True,linestyle=grid_linestyle,color=grid_color)
        self.axes.set_facecolor(axes_facecolor)
        self.axes.xaxis.label.set_color(text_color)
        self.axes.yaxis.label.set_color(text_color)
        self.axes.tick_params(colors=text_color)
        self.axes.tick_params(colors=text_color, which='both')

        for spine in ['left','right','top','bottom']:
            self.axes.spines[spine].set_visible(spines_visible)
    
 
    def clear(self):
        
        self.axes.cla()
        textstr = 'No Data\navailable'
        props = dict(boxstyle='round', facecolor=np.array([163, 130, 38])/255., alpha=0.5)
        self.axes.text(0.45, 0.55, textstr, transform=self.axes.transAxes, fontsize=10,verticalalignment='top', bbox=props)
        self._plot_refs = None
        self._plot_refs_full = None
        self._mean_refs = None
        self.show_all = False
        self.show_mean = False
 
 
    def update_plot(self, data, data_type, data_file, full_data=None, mean_values=None):
        """(Re)Loads the data with self.load_data() and 
        draws the plot. If called for the first time, the 
        axis is created, otherwise the reference to the axis
        is updated.
        """
        self.df = data
        self.full_df = full_data
        self.mean_values = mean_values
        
        show_all = self.full_df is not None and not self.full_df.empty
        show_mean = self.mean_values is not None and not self.mean_values.empty

        if self.df.empty and not show_all:
            self.clear()
        else:
            if (
                self._plot_refs is None
                or self.current_data_type != data_type
                or not are_equal(self.fields, (self.df.columns if not self.df.empty else self.full_df.columns))
                or self.show_all != show_all
                or self.show_mean != show_mean
            ):
                
                self.current_data_type = data_type
                self.current_data_file = data_file
                self.fields = self.df.columns if not self.df.empty else self.full_df.columns
                self.show_all = show_all
                self.show_mean = show_mean
                
                self.axes.cla()
                                
                if show_all:
                    plot_refs_full = [
                        self.axes.plot(
                            self.full_df.index,
                            self.full_df[col],
                            color="lightgray",
                            linewidth=1.0,
                            label="_full",
                        )[0]
                        for col in list(self.full_df)
                    ]
                else:
                    plot_refs_full = None

                if not self.df.empty:
                    plot_refs = [
                        self.axes.plot(self.df.index, self.df[col], label=col)[0]
                        for col in list(self.df)
                    ]
                else:
                    plot_refs = []

                if show_mean and plot_refs:
                    mean_refs = []
                    for i, col in enumerate(list(self.df)):
                        mean_val = self.mean_values.get(col)
                        if mean_val is None:
                            continue
                        color = plot_refs[i].get_color()
                        mean_line = self.axes.axhline(
                            mean_val,
                            color=color,
                            linestyle="--",
                            linewidth=1.0,
                            label="_mean",
                        )
                        mean_refs.append(mean_line)
                else:
                    mean_refs = None
                
                if data_type == 'residuals':
                    self.axes.set_ylabel('Residuals [-]')    
                    self.axes.set_yscale('log')
                elif data_type == 'forces':
                    self.axes.set_ylabel('Forces [N]')
                elif data_type == 'time':
                    self.axes.set_ylabel('Time [s]')
                else:
                    self.axes.set_ylabel('Data []')
                
                self.axes.set_xlabel('Time')   

                legend = self.axes.legend(framealpha=0.2)
                legend.set_draggable(True)
    
                self._plot_refs = plot_refs
                self._plot_refs_full = plot_refs_full
                self._mean_refs = mean_refs
                
            else:
               
                for i,col in enumerate(list(self.df)):
                    self._plot_refs[i].set_data(self.df.index, self.df[col])

                if self._plot_refs_full is not None:
                    for i,col in enumerate(list(self.full_df)):
                        self._plot_refs_full[i].set_data(self.full_df.index, self.full_df[col])

                if self._mean_refs is not None:
                    for i, col in enumerate(list(self.df)):
                        mean_val = self.mean_values.get(col)
                        if mean_val is None:
                            continue
                        self._mean_refs[i].set_ydata([mean_val, mean_val])
    
                self.axes.relim()
                self.axes.autoscale_view()

        self.setPlotStyle()
        self._update_font_sizes()
        self.draw()

            
    def savePlot(self):
        
        fig_name = "{0:}.png".format(self.current_data_file)
        
        self.print_figure(fig_name,dpi=200)
