"""
simulate.py: Take user inputs and create all the nessesory files/cnfigurations files
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
import argparse
import datetime as dt
import pandas as pd

import sys
sys.path.extend(["py/", "py/geo/"])
from calender import create_flare_list_for_calender
from goes import FlareTS
from fetchUtils import SDAnalysis
from drap import DRAP

def run_one_event(args):
    print(f"\n\t Date->{args.date}")
    file = f"assets/data/figures/goes/{args.date.strftime('%Y%m%d')}.png"
    if not os.path.exists(file):
        rads = args.rads.split("-")
        color_codes = pd.read_csv(f"assets/data/FL.{args.date.year}_color.csv", parse_dates=["date"])
        event = pd.read_csv(
            f"assets/data/FL.{args.date.year}.csv", 
            parse_dates=["date", "event_starttime", "event_peaktime", "event_endtime"]
        )
        color_codes = color_codes[color_codes.date==args.date]
        if len(color_codes) > 0:
            clas = "C"
            if color_codes.color.iloc[0] == "red": clas = "X"
            if color_codes.color.iloc[0] == "yellow": clas = "M"
            event = event[
                (event.date==args.date)
                & (event.clx==clas)
            ]
            start_time, peak_time, end_time = (
                event.event_starttime.iloc[0],
                event.event_peaktime.iloc[0],
                event.event_endtime.iloc[0],
            )
            print(f"\t Dates->{start_time},{peak_time},{end_time}")
            start_time = start_time.replace(minute=0) - dt.timedelta(hours=1)
            end_time = end_time.replace(minute=0) + dt.timedelta(hours=1)
            
            g = FlareTS([start_time, end_time])
            g.plot_TS()
            g.save()
            g.close()
            sd = SDAnalysis(dates=[start_time, end_time], rads=rads)
            timings = sd.plot_summary_TS()
            sd.save()
            sd.close()
    return

def run_event(args):
    """
    Create simulate .md files
    """
    if args.whole_month:
        date, month = (
            args.date.replace(day=1),
            args.date.month
        )
        while (date.month==month):
            args.date = date
            run_one_event(args)
            date += dt.timedelta(days=1)
    else:
        run_one_event(args)
    return

def run_DRAP_event(args):
    event = pd.read_csv(
        f"assets/data/FL.{args.date.year}.csv", 
        parse_dates=["date", "event_starttime", "event_peaktime", "event_endtime"]
    )
    #d = DRAP()
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-y", "--year", default=2021, type=int, help="Start year for flare list creation."
    )
    parser.add_argument(
        "-m", "--method", default="EA", type=str, help="FL: Flare list; EA: Event analysis; DRAP: Model"
    )
    parser.add_argument(
        "-d", "--date", default="2023-12-31", type=dt.datetime.fromisoformat, help="ISOformat - YYYY-MM-DD:HH:mm:ss"
    )
    parser.add_argument(
        "-wm", "--whole_month", action="store_true", help="Run whole month analysis"
    )
    parser.add_argument(
        "-r", "--rads", default="fhe-fhw-bks", type=str, help="Radars / Sep: '-', fhe-fhw-..."
    )
    args = parser.parse_args()
    for k in vars(args).keys():
        print("     ", k, "->", str(vars(args)[k]))
    if args.method == "EA":
        run_event(args)
    elif args.method == "DRAP":
        run_DRAP_event(args)
    elif args.method == "FL":
        create_flare_list_for_calender(args.year)
    else:
        print(f"Invalid method / not implemented {args.method}")