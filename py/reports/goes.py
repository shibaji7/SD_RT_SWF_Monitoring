#!/usr/bin/env python

"""goes.py: goes module for data fetching."""

__author__ = "Chakraborty, S."
__copyright__ = ""
__credits__ = []
__license__ = "MIT"
__version__ = "1.0."
__maintainer__ = "Chakraborty, S."
__email__ = "shibaji7@vt.edu"
__status__ = "Research"


import numpy as np
import datetime as dt
import pandas as pd

import matplotlib
matplotlib.style.use(["science", "ieee"])
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
import matplotlib.dates as mdates

class GOES(object):
    """
    Load .csv type files from NGDC server
    directly into memory, process and plot
    the dataset.
    """

    def __init__(self, dates=[dt.datetime(2015,3,11), dt.datetime(2015,3,11)], sat_nr=15):
        self.dates = dates
        self.sat_nr = 15
        return

    def load_data(self):
        """
        Load .csv files into memory
        """
        self.dat = pd.DataFrame()
        dtime = "{:d}{:02d}{:02d}"
        fname = "g{:d}_xrs_2s_{}_{}.csv"
        url = "https://satdat.ngdc.noaa.gov/sem/goes/data/full/{:d}/{:02d}/goes{:d}/csv/"
        d = self.dates[0]
        while d <= self.dates[1]:
            dlt = dtime.format(d.year, d.month, d.day)
            fn = fname.format(self.sat_nr, dlt, dlt)
            uri = url.format(d.year, d.month, self.sat_nr)
            uri += fn
            self.dat = pd.concat([self.dat, pd.read_csv(uri, skiprows=139, parse_dates=["time_tag"])])
            d += dt.timedelta(1)
        return self

    def analyze_flare(self):
        """
        Analyze flare timing and class
        """
        p = np.max(self.dat.B_FLUX)
        self.c = ""
        if p >= 1e-4: self.c = "X" + ""
        elif p >= 1e-5: self.c = "M" + ""
        elif p >= 1e-6: self.c = "C" + ""
        self.id_c = self.dat.time_tag.tolist()[self.dat.B_FLUX.tolist().index(p)]
        return self

    def plot_TS(self, dates):
        """
        Plot time series data in-memory
        """
        fig = plt.figure(figsize=(7, 3), dpi=150)
        ax = fig.add_subplot(111)
        ax.set_xlabel("Time, UT", fontdict={"size":12, "fontweight": "bold"})
        ax.set_ylabel(r"Irradiance, $W/m^2$", fontdict={"size":12, "fontweight": "bold"})
        ax.set_title("GOES X-Ray", loc="left", fontdict={"size":12, "fontweight": "bold"})
        ax.xaxis.set_major_formatter(DateFormatter(r"%H^{%M}"))
        hours = mdates.HourLocator(byhour=range(0, 24, 1))
        ax.xaxis.set_major_locator(hours)
        dtime = (dates[1]-dates[0]).total_seconds()/3600.
        if dtime < 4.:
            minutes = mdates.MinuteLocator(byminute=range(0, 60, 30))
            ax.xaxis.set_minor_locator(minutes)
            ax.xaxis.set_minor_formatter(DateFormatter(r"%H^{%M}"))
        ax.semilogy(self.dat.time_tag, self.dat.A_FLUX, "b", ls="-", lw=1.0, alpha=0.7, label="HXR")
        ax.semilogy(self.dat.time_tag, self.dat.B_FLUX, "r", ls="-", lw=1.0, alpha=0.7, label="SXR")
        ax.legend(loc=1)
        ax.set_xlim(dates)
        ax.set_ylim(1e-8,1e-2)
        ax.axhline(1e-4, color="r", ls="--", lw=0.6, alpha=0.7)
        ax.axhline(1e-5, color="orange", ls="--", lw=0.6, alpha=0.7)
        ax.axhline(1e-6, color="darkgreen", ls="--", lw=0.6, alpha=0.7)
        ax.text(dates[0]+dt.timedelta(minutes=5), 3e-6, "C", fontdict={"size":10, "color":"darkgreen"})
        ax.text(dates[0]+dt.timedelta(minutes=5), 3e-5, "M", fontdict={"size":10, "color":"orange"})
        ax.text(dates[0]+dt.timedelta(minutes=5), 3e-4, "X", fontdict={"size":10, "color":"red"})
        ax.axvline(self.id_c, color="k", ls="--", lw=0.6, alpha=0.7)
        ax.text(self.id_c, 2e-2, "Class: "+self.c+" / Time:"+self.id_c.strftime("%H:%M")+" UT", ha="center", va="center", 
                fontdict={"size":10, "color":"k"})
        return self

if __name__ == "__main__":
    GOES().load_data()
