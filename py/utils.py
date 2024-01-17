#!/usr/bin/env python

"""
    utils.py: module for all utilities
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
import calendar
from loguru import logger

def read_events(date):
    events = pd.read_csv(
        f"assets/data/FL.{date.year}.csv", 
        parse_dates=["date", "event_starttime", "event_peaktime", "event_endtime"]
    )
    color_codes = pd.read_csv(
        f"assets/data/FL.{date.year}_color.csv", 
        parse_dates=["date"]
    )
    return events, color_codes

def select_event_by_color_code_date(events, color_codes, date):
    event, color_code = (
        events[events.date==date],
        color_codes[color_codes.date==date]
    )
    if len(color_code) > 0:
        clas = "C"
        if color_code.color.iloc[0] == "red": clas = "X"
        if color_code.color.iloc[0] == "yellow": clas = "M"
        event = event[
            (event.date==date)
            & (event.clx==clas)
        ]
        start_time, end_time = (
            event.event_starttime.iloc[0],
            event.event_endtime.iloc[0],
        )
        logger.info(f"DT Range->{start_time},{end_time}")
        start_time = start_time.replace(minute=0) - dt.timedelta(hours=1)
        end_time = end_time.replace(minute=0) + dt.timedelta(hours=2)
        event = event.iloc[0].to_dict()
        event["start_time"], event["end_time"] = (
            start_time, end_time
        )
        event["coord"] = "geo"
        event["has_event"] = True
    else:
        event = dict(has_event=False)
    return event

def create_date_list(date, whole_month):
    if whole_month:
        _, nod = calendar.monthrange(date.year, date.month)
    else:
        nod = 1
    dates = [date] if nod == 1 else [
        date.replace(day=1) + dt.timedelta(d) for d in range(nod)
    ]
    return dates