"""
drap.py: Run new DRAP model
"""

__author__ = "Chakraborty, S."
__copyright__ = ""
__credits__ = []
__license__ = "MIT"
__version__ = "1.0."
__maintainer__ = "Chakraborty, S."
__email__ = "shibaji7@vt.edu"
__status__ = "Research"

import numpy as np
from goes import FlareTS

class DRAP(object):

    def __init__(self, event, date=None):
        self.event = event
        for k in self.event.keys():
            setattr(self, k, self.event[k])
        self.date = date if date else self.event_peaktime
        self.flareTS = FlareTS([self.event_starttime, self.event_endtime])
        self.run_event_analysis()
        return

    def run_event_analysis(self, date=None):
        date = date if date else self.date
        goes = self.flareTS.dfs["goes"].copy()
        goes = goes[goes.time==date]
        print(goes)
        return
