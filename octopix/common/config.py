#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from configparser import ConfigParser

#import distutils
from distutils import util

from pathlib import Path
import os

supported_post_types = ['residuals','forces','rigidBodyState','time','fieldMinMax','actuatorDisk']

default_field_selection = {'forces':['fx'],'rigidBodyState':['z','pitch'],'time':['cpu/step','clock/step'],'actuatorDisk':['thrust']}

rgb_colors = {}
rgb_colors['lightgrey'] = 'rgb(211,211,211)'
rgb_colors['silver'] = 'rgb(192,192,192)'


cfg_data = {
    
    'appearance':
    {
        'dark_mode':False
    },
    
    'canvas': 
    {
        'style': 'dark'
    },
    'autoupdate':
    {
            'interval': 1.0,
            'active_on_start': True
    }
    
}

def getBool(s):
    return bool(util.strtobool(s))

class OctopixConfigurator(ConfigParser):
    
    def _configPath(self):
        return Path(Path.home() / ".config" / "octopix" / "octopix.ini")

    def _legacyConfigPath(self):
        return Path(Path.home() / ".config" / "ocotpix" / "octopix.ini")

    def _writeConfigFile(self):
        
        path = Path(Path.home() / ".config" / "octopix")  # to cfg_data
        os.makedirs(path, exist_ok=True)
        
        with open(Path(path/'octopix.ini'), 'w') as configfile:
            self.write(configfile)        
    
    def __init__(self,*args, **kwargs):
        
        super(OctopixConfigurator,self).__init__(*args, **kwargs)
        self.read_dict(cfg_data)
        config_path = self._configPath()
        legacy_path = self._legacyConfigPath()
        if config_path.exists():
            self.read(config_path)
        elif legacy_path.exists():
            self.read(legacy_path)


def main():
    
    c = OctopixConfigurator()
    c._writeConfigFile()


    print(c.getfloat('autoupdate','interval'))
    print(c._sections['autoupdate'])
    print(c['autoupdate'])

if __name__ == '__main__':
    main()
