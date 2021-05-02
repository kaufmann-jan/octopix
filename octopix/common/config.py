#!/usr/bin/env python3
# -*- coding: utf-8 -*-


supported_post_types = ['residuals','forces','rigidBodyState','time','fieldMinMax']

default_field_selection = {'forces':['fx'],'rigidBodyState':['z','pitch'],'time':['cpu/step','clock/step']}

import configparser

from pathlib import Path
import os

path = Path(Path.home()/".config/ocotpix")
os.makedirs(path, exist_ok=True)

cfg_data = {
    'appearance': 
    {
        'backgroundcolor': 'lightblue',
        'gridcolor': 'white',
    },
    'settings':
    {
    }
}

config = configparser.ConfigParser()
config.read_dict(cfg_data)

with open(Path(path/'octopix.ini'), 'w') as configfile:
    config.write(configfile)
