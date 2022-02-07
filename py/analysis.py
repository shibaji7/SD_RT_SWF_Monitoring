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


import sys
sys.path.extend(["py/"])
import os

import json
import datetime as dt
from statsmodels.tsa.ar_model import AutoReg, ar_select_order
import statsmodels.api as sm
import argparse

import pydarn
from suntime import Sun
from loguru import logger

import matplotlib.pyplot as plt
import seaborn as sns

from getfitdata import FetchData
from rad_fov import FoV

class PhaseDetector(object):
    """
    Class is dedicated for phase detction algorithm
    """
    
    def __init__(self, rad, cfg="config/server.json"):
        self.rad = rad
        with open(cfg, "r") as f: o = json.load(f)
        for k in o.keys():
            setattr(self, k, o[k])
        for k in o["train_unit"].keys():
            setattr(self, k, o["train_unit"][k])
        self.hdw = pydarn.read_hdw_file(rad)
        self.rad_fov = FoV(hdw=self.hdw, ngates=70)
        self.model = {}
        return
    
    def fetch_echoes_dataset(self):
        dates = [self.prev_date, self.prev_date + dt.timedelta(1)]
        fd = FetchData(self.rad, dates)
        b, _ = fd.fetch_data()
        dat = fd.convert_to_pandas(b)
        scan_min_time = self.scan_time/60.
        dat["min_of_day"] = dat.time.apply(lambda x: scan_min_time*int((x.hour*60+x.minute)/scan_min_time))
        dat = dat.groupby("min_of_day").size().reset_index()
        dat = dat.rename(columns={0:"size"}).drop(columns=["min_of_day"])
        return dat
    
    def train_AR(self, rt=False):
        self.prev_date = dt.datetime.strptime(self.date, "%Y-%m-%d") - dt.timedelta(1)
        logger.info(f"Train background for {self.rad} on {self.prev_date}")
        ar_max_order = int(self.train_hours*3600. / self.scan_time)
        fname = self.save_train_file + "ar.e%s.d%d.model.pickle"%(self.prev_date.strftime("%d%b%y"),self.train_days)
        if rt: os.system("rm " + fname)
        os.makedirs(self.save_train_file, exist_ok=True)
        if not os.path.exists(fname):
            logger.info(f"Train an auto regressor model ARm({ar_max_order})")
            dat = self.fetch_echoes_dataset()
            ar = AutoReg(dat, ar_max_order, old_names=False)
            self.model["ar.resp"] = ar.fit(cov_type="HC0")
            self.model["ar.resp"].save(fname)
        else: 
            logger.info(f"Load an auto regressor model ARm({ar_max_order}):{fname}")
            self.model["ar.resp"] = sm.load(fname)
        return
    
    def get_central_lat_lon(self):
        lonCenter, latCenter = self.rad_fov.lonFull.mean(), self.rad_fov.latFull.mean()
        return latCenter, lonCenter
    
    def calculate_suntime(self):
        latCenter, lonCenter = self.get_central_lat_lon()
        sun = Sun(latCenter, lonCenter)
        date = self.prev_date + dt.timedelta(1)
        sr, ss = sun.get_sunrise_time(date), sun.get_sunset_time(self.prev_date)
        logger.info(f"Train SunTime {sr} on {ss}")
        return sr, ss

def simulate(args):
    """
    Simulate background model
    """
    opd = PhaseDetector(args.rad)
    opd.train_AR(args.retrain)
    return

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("-r", "--rad", default="bks", help="SuperDARN radar code (default bks)")
    p.add_argument("-t", "--retrain", action="store_true", help="Retrain the model (default False)")
    args = p.parse_args()
    logger.info(f"Simulation run using fitacf_amgeo.__main__")
    simulate(args)
    pass