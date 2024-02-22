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
import utils
from calender_list import create_flare_list_for_calender, create_event_list
from drap import DRAP
from summary import Summary

def run_summary_plots_event_analysis(args):
    """
    Create simulate .md files
    """
    args.rads = args.rads.split("-")
    if args.whole_month:
        dates = utils.create_date_list(args.start_date, args.whole_month)
    else:
        days = int((args.end_date - args.start_date).days)
        dates = [args.start_date + dt.timedelta(d) for d in range(days+1)]
    for date in dates:
        events, color_codes =  utils.read_events(date)
        event = utils.select_event_by_color_code_date(events, color_codes, date)
        if event["has_event"]:
            event.update(args.__dict__)
            summary = Summary(event)
            summary.create_overlap_summary_plot()
            drap = DRAP(event, only_xrap=True)
    return

def run_DRAP_event(args):
    if args.whole_month:
        dates = utils.create_date_list(args.start_date, args.whole_month)
    else:
        days = int((args.end_date - args.start_date).days)
        dates = [args.start_date + dt.timedelta(d) for d in range(days+1)]
    for date in dates:
        events, color_codes =  utils.read_events(date)
        event = utils.select_event_by_color_code_date(events, color_codes, date)
        if event["has_event"]:
            event.update(args.__dict__)
            drap = DRAP(event)
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-y", "--year", default=2021, type=int, help="Start year for flare list creation."
    )
    parser.add_argument(
        "-m", "--method", default="EA", type=str, help="FL: Flare list; EA: Event analysis, EL: Event list"
    )
    parser.add_argument(
        "-sd", "--start_date", default="2024-02-21", type=dt.datetime.fromisoformat, help="ISOformat - YYYY-MM-DD:HH:mm:ss"
    )
    parser.add_argument(
        "-ed", "--end_date", default="2024-02-21", type=dt.datetime.fromisoformat, help="ISOformat - YYYY-MM-DD:HH:mm:ss"
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
        run_summary_plots_event_analysis(args)
        run_DRAP_event(args)
    elif args.method == "FL":
        create_flare_list_for_calender(args.year)
    elif args.method == "EL":
        create_event_list(args.year)
    else:
        print(f"Invalid method / not implemented {args.method}")