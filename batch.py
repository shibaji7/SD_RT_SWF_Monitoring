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
from datetime import date, timedelta, datetime
import datetime as dt
import glob

if __name__ == "__main__":
    files = glob.glob("assets/data/figures/xrap/*.png")
    files.sort()
    start, end = (
        dt.datetime.strptime(
            files[-1].split("/")[-1].replace(".png", ""),
            "%Y%m%d"
        ), datetime.combine(date.today(), datetime.min.time()) - timedelta(1)
    )
    sdate, edate = (
        start,
        start + timedelta(1)
    )
    while edate <= end:
        print(sdate, edate)
        commands = [
            f"python simulate.py -m FL",
            f"python simulate.py -m VAL -sd {sdate.strftime('%Y-%m-%d')} -ed {edate.strftime('%Y-%m-%d')}",
            f"python simulate.py -m JS",
            f"python simulate.py -m EA -sd {sdate.strftime('%Y-%m-%d')} -ed {edate.strftime('%Y-%m-%d')}",
        ]
        for command in commands:
            os.chdir("/home/shibaji/CodeBase/SD_RT_SWF_Monitoring/")
            os.system(command)
        sdate, edate = (
            sdate + timedelta(1),
            edate + timedelta(1),
        )
    commands = [
        f"git add --all",
        f"git commit -m \"Updated on {edate.strftime('%Y-%m-%d')}\"",
        f"git push"
    ]
    for command in commands:
        os.chdir("/home/shibaji/CodeBase/SD_RT_SWF_Monitoring/")
        os.system(command)