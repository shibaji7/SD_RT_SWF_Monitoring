#!/usr/bin/env python

"""
    batch.py: module to create calender-flare informations and summay plots
"""

__author__ = "Chakraborty, S."
__copyright__ = ""
__credits__ = []
__license__ = "MIT"
__version__ = "1.0."
__maintainer__ = "Chakraborty, S."
__email__ = "shibaji7@vt.edu"
__status__ = "Research"

import os
from datetime import date, timedelta

if __name__ == "__main__":
    date = date.today() - timedelta(1)
    commands = [
        f"python simulate.py -m FL -d {date.strftime('%Y-%m-%d')} >/dev/null 2>&1",
        f"python simulate.py -m EA -d {date.strftime('%Y-%m-%d')} >/dev/null 2>&1",
        f"git add --all",
        f"git commit -m \"Updated on {date.strftime('%Y-%m-%d')}\"",
        f"git push"
    ]
    for command in commands:
        os.chdir("/home/shibaji/CodeBase/SD_RT_SWF_Monitoring/")
        os.system(command)