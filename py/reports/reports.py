#!/usr/bin/env python

"""analysis.py: module is dedicated for data analysis, phase and anomaly detection."""

__author__ = "Chakraborty, S."
__copyright__ = "Copyright 2022, SuperDARN@VT"
__credits__ = []
__license__ = "MIT"
__version__ = "1.0."
__maintainer__ = "Chakraborty, S."
__email__ = "shibaji7@vt.edu"
__status__ = "Research"

import os
import datetime as dt

if __name__ == "__main__":
    rads = ["'bks'", "'fhe'", "'fhw'"]
    edate = dt.datetime(2015, 3, 11, 16, 20)
    stime, etime = dt.datetime(2015, 3, 11, 16), dt.datetime(2015, 3, 11, 17)
    folder = "repo/{}/".format(etime.strftime("%d-%b-%Y"))
    if not os.path.exists(folder): os.makedirs(folder)
    
    with open("repo/bulletin.md", "r") as f: text = "".join(f.readlines())
    text = text.replace("{year}", str(edate.year))
    text = text.replace("{day}", str(edate.day))
    text = text.replace("{month}", str(edate.month))
    text = text.replace("{hour}", str(edate.hour))
    text = text.replace("{minute}", str(edate.minute)) 
    text = text.replace("{shour}", str(stime.hour)) 
    text = text.replace("{ehour}", str(etime.hour)) 
    text = text.replace("{Month}", edate.strftime("%b"))
    text = text.replace("{rads}", ",".join(rads))
    
    with open(folder+"bulletin.md", "w") as f: f.write(text)
    os.system(f"stitch {folder}bulletin.md -o {folder}bulletin.html")
    os.remove(f"{folder}bulletin.md")