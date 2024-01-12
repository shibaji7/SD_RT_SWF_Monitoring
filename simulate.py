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

import argparse
import sys
sys.path.extend(["py/", "py/geo/"])
from calender import create_flare_list_for_calender


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-y", "--year", default=2021, type=int, help="Start year for flare list creation."
    )
    parser.add_argument(
        "-m", "--method", default="FL", type=str, help="FL: Flare list; EA: Event analysis; DRAP: Model"
    )
    args = parser.parse_args()
    for k in vars(args).keys():
        print("     ", k, "->", str(vars(args)[k]))
    if args.method == "EA":
        run_event(args.index, args.cfg_file)
    elif args.method == "FL":
        create_flare_list_for_calender(args.year)
    else:
        print(f"Invalid method / not implemented {args.method}")