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
import copy
import numpy as np
import pandas as pd

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
        last_date = self.prev_date - dt.timedelta(self.train_days-1)
        dates = [last_date, self.prev_date + dt.timedelta(1)]
        fd = FetchData(self.rad, dates)
        b, _ = fd.fetch_data()
        dat = fd.convert_to_pandas(b)
        scan_min_time = self.scan_time/60.
        dat["min_of_day"] = dat.time.apply(lambda x: scan_min_time*int((x.hour*60+x.minute)/scan_min_time))
        dat = dat.groupby("min_of_day").size().reset_index()
        # Add time in this dataframe
        dat = dat.rename(columns={0:"size"}).drop(columns=["min_of_day"])
        dat["size"] = dat["size"]
        return dat
    
    def train_AR(self, rt=False):
        self.prev_date = dt.datetime.strptime(self.date, "%Y-%m-%d") - dt.timedelta(1)
        logger.info(f"Train background for {self.rad} on {self.prev_date}")
        ar_max_order = int(self.train_hours*3600. / self.scan_time)
        mfname = self.save_train_file + "ar.e%s.d%d.model.pickle"%(self.prev_date.strftime("%d%b%y"),self.train_days)
        dfname = self.save_train_file + "ar.e%s.d%d.model.csv"%(self.prev_date.strftime("%d%b%y"),self.train_days)
        if rt and os.path.exists(mfname): os.system("rm " + mfname)
        if rt and os.path.exists(dfname): os.system("rm " + dfname)
        os.makedirs(self.save_train_file, exist_ok=True)
        if not os.path.exists(mfname):
            logger.info(f"Train an auto regressor model ARm({ar_max_order})")
            dat = self.fetch_echoes_dataset()
            dat.to_csv(dfname, index=False, header=True)
            ar = AutoReg(dat, ar_max_order, old_names=False)
            self.model["ar.resp"] = ar.fit(cov_type="HC0")
            self.model["ar.resp"].save(mfname)
        else: self.model["ar.resp"] = sm.load(mfname)
        return
    
    def update_AR(self, dat):
        if not hasattr(self, "d0"):
            dfname = self.save_train_file + "ar.e%s.d%d.model.csv"%(self.prev_date.strftime("%d%b%y"),self.train_days)
            self.d0 = pd.read_csv(dfname)
        self.d0 = pd.concat([self.d0, dat])
        self.d0 = self.d0.reset_index().drop(columns=["index"])
        logger.info(f"Retrain AR: L({len(self.d0)})")
        ar_max_order = int(self.train_hours*3600. / self.scan_time)
        ar = AutoReg(self.d0, ar_max_order, old_names=False)
        self.model["ar.resp"] = ar.fit(cov_type="HC0")
        return
    
    def forecast(self, L=1, model_name="ar"):
        key = "%s.resp"%model_name
        if not key in self.model.keys(): self.train_AR()
        model = self.model["%s.resp"%model_name]
        if model_name=="ar": pred = model.forecast(L)
        return pred
    
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

class Detectors(object):
    """
    Class is dedicated for SWF phase detection
    """
    
    def __init__(self):
        self.predictors = {}
        self.phases = {}
        self.echoes_dev = {}
        return
    
    def preset(self, r):
        if r not in self.predictors.keys(): self.predictors[r] = PhaseDetector(r)
        if r not in self.phases.keys(): self.phases[r] = "p-SWF"
        if r not in self.echoes_dev.keys(): self.echoes_dev[r] = 0.
        return
    
    def get_echoes_counts(self, o):
        d = pd.DataFrame()
        d["size"] = [len(o)] 
        return d
    
    def detect_SWF_phase(self, r, o, dn):
        d = self.get_echoes_counts(o)
        opd = self.predictors[r]
        p = np.array(opd.forecast(), dtype=int)
        if d["size"].tolist()[0] > 0: pe = abs(d["size"].tolist()[0] - p.tolist()[0])/d["size"].tolist()[0]
        else: pe = -999.
        logger.info(f"Forecast : Observations, {p.tolist()[0]}:{d['size'].tolist()[0]}")
        logger.info(f"PE({pe}) at {dn}")
        self.echoes_dev[r] = pe
        if pe <= 0.5: opd.update_AR(d)
        if (pe > 0.5 and pe <= 0.9) and self.phases[r]=="p-SWF": self.phases[r] = "o-SWF"
        if pe > 0.9 and self.phases[r] in ["o-SWF", "p-SWF"]: self.phases[r] = "b-SWF"
        if (pe > 0.5 and pe <= 0.9) and self.phases[r] in ["o-SWF", "b-SWF"]: self.phases[r] = "r-SWF"
        if pe <= 0.1 and self.phases[r] in ["b-SWF", "r-SWF", "o-SWF"]: self.phases[r] = "p-SWF"
        self.print_summary(dn)
        return pe, self.phases[r]
    
    def print_summary(self, dn):
        for r in self.phases.keys():
            logger.info(f"Infered procs {dn}: {r.upper()}({self.phases[r]}, {self.echoes_dev[r]})")
        return

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("-r", "--rad", default="bks", help="SuperDARN radar code (default bks)")
    p.add_argument("-t", "--retrain", action="store_true", help="Retrain the model (default False)")
    args = p.parse_args()
    logger.info(f"Simulation run using fitacf_amgeo.__main__")
    simulate(args)
    pass