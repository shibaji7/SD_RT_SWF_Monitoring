#!/usr/bin/env python

"""sdc.py: sdc module for data fetching."""

__author__ = "Chakraborty, S."
__copyright__ = ""
__credits__ = []
__license__ = "MIT"
__version__ = "1.0."
__maintainer__ = "Chakraborty, S."
__email__ = "shibaji7@vt.edu"
__status__ = "Research"

import warnings
warnings.filterwarnings("ignore")


import datetime as dt
import numpy as np
import pandas as pd

import matplotlib
matplotlib.style.use(["science", "ieee"])
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import matplotlib.dates as mdates

import getfitdata as gfd


class SDAnalysis(object):
    """
    This class is dedicated to analyze the SD
    data in ground scatter echoes and exract 
    requried parameters for report.
    """

    def __init__(self, dates=[dt.datetime(2015,3,11,16), dt.datetime(2015,3,11,17)], 
            rads=["wal", "bks", "fhe", "fhw", "cve", "cvw", "gbr", "kap", "sas", "pgr"]):
        self.dates = dates
        self.rads = rads
        return
    
    def get_SD_data(self):
        """
        Fetch data from local repo
        """
        if not hasattr(self, "dat"):
            self.dat = {}
            for r in self.rads:
                fdata = gfd.FetchData( r, self.dates )
                beams, _ = fdata.fetch_data()
                self.dat[r] = fdata.convert_to_pandas(beams)
        return

    # TODO
    def fetch_parameters(self, beam=None):
        """
        Ftech SD fit data and analyze 
        groundscatter echoes, extract timings and
        phases.
        """
        self.get_SD_data()
        self.dat_strm = {}
        self.parames = []
        for r in self.rads:
            dat = {
                "Rad": r.upper(), r"$\text{f}_\text{0}$":None, r"$\text{t}_{\text{onset}}$": None,
                r"$\text{t}_{\text{blackout}}$": None, r"$\text{t}_{\text{rec}_s}$": None, 
                "$\text{t}_{\text{rec}_e}$": None, r"$\tau_{\text{onset}}$": None, 
                r"$\tau_{\text{blackout}}$": None, r"$\tau_{\text{rec}}$": None,
                }
            try:
                o = self.dat[r]
                dat[r"$\text{f}_\text{0}$"] = np.round(np.nanmean(o.tfreq)/1e3, 1)
            except:
                import traceback
                traceback.print_exc()
            self.parames.append(dat)
        self.parames = pd.DataFrame.from_records(self.parames)
        return self

    def plot_TS(self, bm=None):
        """
        Plot time series data
        """
        self.get_SD_data()
        fig = plt.figure(figsize=(6, 2.5*len(self.rads)), dpi=150)
        for i, r in enumerate(self.rads):
            o = self.dat[r]
            if len(o) > 0:
                if bm: o = o[o.bmnum==bm]
                    
                tfreq = np.unique(np.round((2*(o.tfreq/1e3))/2))
                tfreq = [str(x) for x in tfreq]
                o = o.groupby("time").count().reset_index()
                ax = fig.add_subplot(len(self.rads),1,i+1)
                ax.set_ylabel(r"$<E>$",fontdict={"size":12, "fontweight": "bold"})
                text = r"Radar: {}, Beam: {}, $f_0\sim$ {} MHz".format(r.upper(), bm, "/".join(tfreq))
                ax.text(0.1, 0.9, text, ha="left", va="center", transform=ax.transAxes, 
                        fontdict={"size":8, "fontweight": "bold"})
                ax.xaxis.set_major_formatter(DateFormatter(r"%H^{%M}"))
                hours = mdates.HourLocator(byhour=range(0, 24, 1))
                ax.xaxis.set_major_locator(hours)
                dtime = (self.dates[1]-self.dates[0]).total_seconds()/3600.
                if dtime < 4.:
                    minutes = mdates.MinuteLocator(byminute=range(0, 60, 10))
                    ax.xaxis.set_minor_locator(minutes)
                    ax.xaxis.set_minor_formatter(DateFormatter(r"%H^{%M}"))
                ax.set_ylim(0,40)
                ax.set_xlim(self.dates)
                ax.plot(o.time, o.v, "ko", ms=1.2, alpha=0.8)
        ax.set_xlabel("Time, UT", fontdict={"size":12, "fontweight": "bold"})
        fig.subplots_adjust(hspace=0.2)
        return self

