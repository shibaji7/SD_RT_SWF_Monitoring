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

import datetime as dt
import os
import pandas as pd
from goes import FlareInfo

def create_flare_list_file(file, start_date, end_date):
    date = start_date
    events = pd.DataFrame()
    while date <= end_date:
        dates = [date, date + dt.timedelta(1)]
        g = FlareInfo(dates)
        if len(g.flare) > 0:
            events = pd.concat([events, g.flare])
        date = date + dt.timedelta(1)
    events["clx"] = events.fl_goescls.apply(lambda x: x[0])
    events["date"] = events.event_peaktime.apply(
        lambda x: x.to_pydatetime().strftime("%Y-%m-%d")
    )
    date, color = list(), list()
    for d in events.date.unique():
        if d not in date:
            e = events[events.date == d]
            if len(e) > 0:
                du = pd.Timestamp(d).to_pydatetime().strftime("%m/%d/%Y")
                date.append(pd.Timestamp(d).to_pydatetime())
                col = "green"
                if "M" in e.clx.tolist():
                    col = "yellow"
                if "X" in e.clx.tolist():
                    col = "red"
                color.append(col)
    color_codes = pd.DataFrame()
    color_codes["color"], color_codes["date"] = color, date
    events.to_csv(file, index=False, header=True)
    color_codes.to_csv(file.replace(".csv", "_color.csv"), index=False, header=True)
    return events, color_codes

def create_flare_list_for_calender(year_start):
    events, color_codes = pd.DataFrame(), pd.DataFrame()
    start_date = dt.datetime(year_start, 1, 1)
    end_date = dt.datetime.now()
    years = [year_start + i for i in range(int((end_date-start_date).days/365)+1)]
    flare_data_files = ["assets/data/FL.{year}.csv".format(year=y) for y in years]
    for file, year in zip(flare_data_files, years):
        print(file, year)
        if year == end_date.year:
            e, code = create_flare_list_file(
                    file, dt.datetime(year, 1, 1), 
                    end_date
                )
            events = pd.concat([events, e])
            color_codes = pd.concat([color_codes, code])
        else:
            if not os.path.exists(file):
                e, code = create_flare_list_file(
                    file, dt.datetime(year, 1, 1), 
                    dt.datetime(year, 12, 31)
                )
                events = pd.concat([events, e])
                color_codes = pd.concat([color_codes, code])
            else:
                events = pd.concat([
                    events, 
                    pd.read_csv(file, parse_dates=["event_starttime","event_peaktime","event_endtime","date"])
                ])
                color_codes = pd.concat([
                    color_codes, 
                    pd.read_csv(file.replace(".csv","_color.csv"), parse_dates=["date"])
                ])
    events.to_csv("assets/data/FL.csv", index=False, header=True)
    color_codes.to_csv("assets/data/FL.color.csv", index=False, header=True)
    brc = """
    {
    'date': new Date('fx_date'),
    'color': 'fx_color',
    },"""
    txt = "var EVENTS = ["
    for i, e in color_codes.iterrows():
        txt += brc.replace("fx_color", e.color).replace("fx_date", 
            e.date.strftime("%m/%d/%Y"))
    txt += "\n]"
    with open("assets/js/flarelist.js", "w") as f:
        f.write(txt)
    return events, color_codes
