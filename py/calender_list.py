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
import json
import os

import numpy as np
import pandas as pd
from goes import FlareInfo, FlareTS


def fetch_flare_details(date):
    events, color_codes = pd.DataFrame(), pd.DataFrame()
    g = FlareInfo([date, date + dt.timedelta(1)])
    if len(g.flare) > 0:
        events = pd.concat([events, g.flare])
        events["date"], events["flare_class"] = (
            events.event_peaktime.apply(
                lambda x: x.to_pydatetime().strftime("%Y-%m-%d")
            ),
            events.fl_goescls.apply(lambda x: x[0]),
        )
        if "M" in events.flare_class.tolist():
            col = "yellow"
        elif "X" in events.flare_class.tolist():
            col = "red"
        else:
            col = "green"
        color_codes["color"], color_codes["date"] = [col], [date]
    return events, color_codes


def create_flare_list_for_calender(year_start):
    events, color_codes = pd.DataFrame(), pd.DataFrame()
    start_date, end_date = (
        dt.datetime(year_start, 1, 1),
        dt.datetime.now() - dt.timedelta(days=1),
    )
    flare_data_file, flare_color_code_file = (
        "assets/data/FL.csv",
        "assets/data/Colors.csv",
    )
    days = (end_date - start_date).days + 1
    dates = [start_date + dt.timedelta(d) for d in range(days)]
    if os.path.exists(flare_data_file):
        events = pd.read_csv(
            flare_data_file,
            parse_dates=["event_starttime", "event_peaktime", "event_endtime", "date"],
        )
    if os.path.exists(flare_color_code_file):
        color_codes = pd.read_csv(flare_color_code_file, parse_dates=["date"])
    first_date, last_date = (
        start_date,
        color_codes.date.iloc[-1] if len(color_codes) > 0 else None,
    )
    for d in dates:
        isrun = False
        if (last_date == None) and (d not in color_codes.date.tolist()):
            print(f"Date: {d}")
            isrun = True
        elif (last_date is not None) and ((d > last_date) or (d < start_date)):
            print(f"Out range Date: {d}")
            isrun = True
        if isrun:
            e, col = fetch_flare_details(d)
            events, color_codes = (
                pd.concat([events, e]),
                pd.concat([color_codes, col]),
            )
            print(e)
    events.to_csv(flare_data_file, index=False, header=True)
    color_codes.to_csv(flare_color_code_file, index=False, header=True)
    return events, color_codes


def validate_specific_dates_class_list(start_date, end_date):
    flare_data_file, flare_color_code_file = (
        "assets/data/FL.csv",
        "assets/data/Colors.csv",
    )
    color_codes = pd.read_csv(flare_color_code_file, parse_dates=["date"])
    events = pd.read_csv(
        flare_data_file,
        parse_dates=["event_starttime", "event_peaktime", "event_endtime", "date"],
    )
    days = (end_date - start_date).days + 1
    dates = [start_date + dt.timedelta(d) for d in range(days)]
    for d in dates:
        if d in color_codes.date.tolist():
            o = color_codes[color_codes.date == d]
            flareTS = FlareTS([d, d + dt.timedelta(1)])
            goes = flareTS.dfs["goes"].copy()
            if (len(goes) > 0) and (len(o) == 1):
                col = o["color"].iloc[0]
                peak = np.max(goes.xrsb)
                fl_goescls = None
                if (peak * 1e5 >= 1) and (peak * 1e5 < 10) and (col != "yellow"):
                    print(f"Validating Date M: {d}")
                    fl_goescls, flare_class, date, ar_noaanum = (
                        "M%.1f" % np.round(peak * 1e5, 1),
                        "M",
                        d,
                        0,
                    )
                    color_codes.loc[color_codes.date == d, "color"] = "yellow"
                if (peak * 1e4 >= 1) and (col != "red"):
                    print(f"Validating Date X: {d}")
                    fl_goescls, flare_class, date, ar_noaanum = (
                        "X%.1f" % np.round(peak * 1e4, 1),
                        "X",
                        d,
                        0,
                    )
                    color_codes.loc[color_codes.date == d, "color"] = "red"
                if fl_goescls:
                    t_peak = goes.time.iloc[goes.xrsb.argmax()]
                    goes = goes[
                        (goes.time < t_peak + dt.timedelta(minutes=10))
                        & (goes.time > t_peak - dt.timedelta(minutes=20))
                    ]
                    t_start = goes.loc[goes[goes.xrsb.gt(1e-6)].index[0], "time"]
                    t_end = goes.loc[goes[goes.xrsb.gt(1e-6)].index[-1], "time"]
                    e = pd.DataFrame.from_records(
                        [
                            dict(
                                event_starttime=t_start,
                                event_peaktime=t_peak,
                                event_endtime=t_end,
                                fl_goescls=fl_goescls,
                                ar_noaanum=ar_noaanum,
                                date=date,
                                flare_class=flare_class,
                            )
                        ]
                    )
                    events = pd.concat([events, e])
                    events.sort_values(by="event_peaktime", inplace=True)
    color_codes.to_csv(flare_color_code_file, index=False, header=True)
    events.to_csv(flare_data_file, index=False, header=True)
    return


def create_JS(year_start):
    _, color_codes = create_flare_list_for_calender(year_start)
    brc = """
    {
    'date': new Date('fx_date'),
    'color': 'fx_color',
    },"""
    txt = "var EVENTS = ["
    for i, e in color_codes.iterrows():
        txt += brc.replace("fx_color", e.color).replace(
            "fx_date", e.date.strftime("%m/%d/%Y")
        )
    txt += "\n]"
    with open("assets/js/flarelist.js", "w") as f:
        f.write(txt)
    return


def create_event_list(year_start):
    events, color_codes = pd.DataFrame(), pd.DataFrame()
    start_date = dt.datetime(year_start, 1, 1)
    end_date = dt.datetime.now() - dt.timedelta(days=1)
    years = [year_start + i for i in range(int((end_date - start_date).days / 365) + 1)]
    flare_data_files = ["assets/data/FL.{year}.csv".format(year=y) for y in years]
    o = pd.concat(
        [
            pd.read_csv(
                f,
                parse_dates=[
                    "event_starttime",
                    "event_peaktime",
                    "event_endtime",
                    "date",
                ],
            )
            for f in flare_data_files
        ]
    )
    o = o[["fl_goescls", "event_starttime", "event_peaktime", "event_endtime"]]
    o.event_starttime = o.event_starttime.astype(str).apply(lambda x: f"Date('{x}')")
    o.event_peaktime = o.event_peaktime.astype(str).apply(lambda x: f"Date('{x}')")
    o.event_endtime = o.event_endtime.astype(str).apply(lambda x: f"Date('{x}')")
    o = o.to_dict("records")
    y = "var events = " + json.dumps(o, indent=4)
    y = y.replace('"Date(', "Date(").replace("')\"", "')")
    with open("assets/js/eventlist.js", "w") as f:
        f.write(y)
    return
