import arcpy
from DATools import *


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Data Assistant"
        self.alias = "dla"

        # List of tool classes associated with this toolbox
        self.tools = [Append, Stage, NewFile, Preview, Replace]
