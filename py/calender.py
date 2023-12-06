#!/usr/bin/env python

"""
    calender.py: module to create calender-flare informations
"""

__author__ = "Chakraborty, S."
__copyright__ = ""
__credits__ = []
__license__ = "MIT"
__version__ = "1.0."
__maintainer__ = "Chakraborty, S."
__email__ = "shibaji7@vt.edu"
__status__ = "Research"


import sys

sys.path.extend(["py/", "py/geo/"])
import datetime as dt

import pandas as pd
from goes import FlareInfo

if __name__ == "__main__":
    year = 2021
    start_date = dt.datetime(year, 1, 1)
    end_date = dt.datetime.now()
    date = start_date
    events = pd.DataFrame()
    while date <= end_date:
        dates = [date, date + dt.timedelta(1)]
        g = FlareInfo(dates)
        if len(g.flare) > 0:
            events = pd.concat([events, g.flare])
        date = date + dt.timedelta(1)
    events.to_csv("repo/events.csv", index=False, header=True)
    events["clx"] = events.fl_goescls.apply(lambda x: x[0])
    events["date"] = events.event_peaktime.apply(
        lambda x: x.to_pydatetime().strftime("%Y-%m-%d")
    )
    date, color = list(), list()
    brc = """
    {
    'date': new Date('fx_date'),
    'color': 'fx_color',
    },"""
    txt = "const EVENTS = ["
    for d in events.date.unique():
        if d not in date:
            e = events[events.date == d]
            if len(e) > 0:
                du = pd.Timestamp(d).to_pydatetime().strftime("%m/%d/%Y")
                date.append(pd.Timestamp(d).to_pydatetime().strftime("%Y-%m-%d"))
                col = "green"
                if "M" in e.clx.tolist():
                    col = "yellow"
                if "X" in e.clx.tolist():
                    col = "red"
                color.append(col)
                txt += brc.replace("fx_color", col).replace("fx_date", du)
    txt += "\n]"
    with open("repo/constant.js", "w") as f:
        f.write(txt)
    _obj = pd.DataFrame()
    _obj["date"], _obj["color"] = date, color
    _obj.to_csv("repo/eventlist.csv", index=False, header=True)
