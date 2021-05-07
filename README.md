# octopix
octopix is a small, lightweight GUI for showing / plotting (mainly) OpenFOAM time series data, generated by OF's function objects.

## Installation

tbd. Maybe sometimes in the future we can do something like

```bash
pip install octopix
```

## Usage

`pyrcc5 -o resources.py resources.qrc`

In order to run with
 
```bash
python -m octopix
```

we need to add octopix to the PYTHONPATH. One possibility is to add to the site-packages of the virtualenv.
For this we need to create a .pth file within the virtualenv's lib dir: 

`path/to/virtualenv/lib/python3.8/site-packages/`

e.g.

`/home/jan/virtualenvs/gui/lib/python3.8/site-packages/octopix.pth`

with the absolute path to the octopix package

`/path/to/octopix`

e.g.

`/home/jan/workspace/octopix`



## Contribution

Contributions are welcome! This is a private project, therefore time is the most limiting resource... :children_crossing:

## License

[GNU General Public License v3.0](https://github.com/kaufmann-jan/octopix/blob/main/LICENSE)


