#!/usr/bin/env python

"""flare.py: module is dedicated to fetch solar irradiance data."""

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
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger
from sunpy import timeseries as ts
from sunpy.net import Fido
from sunpy.net import attrs as a


def setup(science=True):
    if science:
        import mplstyle
        plt.rcParams.update(
            {
                "figure.figsize": np.array([8, 6]),
                "text.usetex": True,
                "font.family": "sans-serif",
                "font.sans-serif": [
                    "Tahoma",
                    "DejaVu Sans",
                    "Lucida Grande",
                    "Verdana",
                ],
                "font.size": 12,
            }
        )
    return


class FlareInfo(object):
    """
    This class is dedicated to plot GOES
    from the repo using SunPy
    """

    def __init__(self, dates, fl_class="C1.0"):
        """
        Parameters
        ----------
        dates: list of datetime object for start and end of TS
        """
        self.flare = {}
        self.dates = dates
        result = Fido.search(
            a.Time(
                self.dates[0].strftime("%Y-%m-%d %H:%M"),
                self.dates[1].strftime("%Y-%m-%d %H:%M"),
            ),
            a.hek.FL,
            a.hek.FL.GOESCls > fl_class,
            a.hek.OBS.Observatory == "GOES",
        )
        # Retrieve HEKTable from the Fido result and then load
        hek_results = result["hek"]
        if len(hek_results) > 0:
            self.flare = hek_results[
                "event_starttime",
                "event_peaktime",
                "event_endtime",
                "fl_goescls",
                "ar_noaanum",
            ].to_pandas()
            self.flare["cls"] = self.flare.fl_goescls.apply(lambda x: x[0])
        return


class FlareTS(object):
    """
    This class is dedicated to plot GOES, RHESSI, and SDO data
    from the repo using SunPy
    """

    def __init__(self, dates, verbose=True, flare_info=None):
        """
        Parameters
        ----------
        dates: list of datetime object for start and end of TS
        """
        self.dates = dates
        self.verbose = verbose
        self.dfs = {}
        self.flare_info = flare_info
        self.__loadGOES__()
        return

    def __loadGOES__(self):
        """
        Load GOES data from remote/local repository
        """
        self.flare = {}
        self.dfs["goes"], self.goes, self.flareHEK = pd.DataFrame(), [], None
        result = Fido.search(
            a.Time(
                self.dates[0].strftime("%Y-%m-%d %H:%M"),
                self.dates[1].strftime("%Y-%m-%d %H:%M"),
            ),
            a.Instrument("XRS") | a.hek.FL & (a.hek.FRM.Name == "SWPC"),
        )
        if len(result) > 0:
            if self.verbose:
                logger.info(f"Fetching GOES ...")
            tmpfiles = Fido.fetch(result, progress=False)
            for tf in tmpfiles:
                self.goes.append(ts.TimeSeries(tf))
                self.dfs["goes"] = pd.concat(
                    [self.dfs["goes"], self.goes[-1].to_dataframe()]
                )
            self.dfs["goes"].index.name = "time"
            self.dfs["goes"] = self.dfs["goes"].reset_index()
            self.dfs["goes"] = self.dfs["goes"][
                (self.dfs["goes"].time >= self.dates[0])
                & (self.dfs["goes"].time <= self.dates[1])
            ]
            # Retrieve HEKTable from the Fido result and then load
            hek_results = result["hek"]
            if len(hek_results) > 0:
                self.flare = hek_results[
                    "event_starttime",
                    "event_peaktime",
                    "event_endtime",
                    "fl_goescls",
                    "ar_noaanum",
                ]
        return

    def __loadRHESSI__(self):
        """
        Load RHESSI data from remote/local repository
        """
        self.rhessi, self.dfs["rhessi"] = [], pd.DataFrame()
        result = Fido.search(
            a.Time(self.dates[0], self.dates[1]), a.Instrument("RHESSI")
        )
        if len(result) > 0:
            logger.info(f"Fetched RHESSI: \n {result}")
            tmpfiles = Fido.fetch(result)
            for tf in tmpfiles:
                if "obssum" in tf:
                    self.rhessi.append(ts.TimeSeries(tf))
                    self.dfs["rhessi"] = pd.concat(
                        [self.dfs["rhessi"], self.rhessi[-1].to_dataframe()]
                    )
            self.dfs["rhessi"].index.name = "time"
            self.dfs["rhessi"] = self.dfs["rhessi"].reset_index()
        logger.info(f"Data from RHESSI XRS: \n {self.dfs['rhessi'].head()}")
        return

    def plot_TS(self, dates=None):
        """
        Plot time series data in-memory
        """
        dates = dates if dates else self.dates
        setup()
        self.fig = plt.figure(figsize=(6, 2.5), dpi=150)
        ax = self.fig.add_subplot(111)
        self.plot_TS_from_axes(ax, dates)
        return

    def plot_TS_from_axes(self, ax, dates=None, xlabel="Time (UT)"):
        """
        Plot time series data in-memory
        """
        dates = dates if dates else self.dates
        ax.set_xlabel(xlabel, fontdict={"size": 12, "fontweight": "bold"})
        ax.set_ylabel(
            r"Irradiance ($W/m^2$)", fontdict={"size": 12, "fontweight": "bold"}
        )
        ax.text(
            1.05,
            0.99,
            "GOES X-Ray",
            ha="center",
            va="top",
            fontdict={"size": 12, "fontweight": "bold"},
            transform=ax.transAxes,
            rotation=90,
        )
        ax.xaxis.set_major_formatter(mdates.DateFormatter(r"%H^{%M}"))
        hours = mdates.HourLocator(byhour=range(0, 24, 1))
        ax.xaxis.set_major_locator(hours)
        dtime = (dates[1] - dates[0]).total_seconds() / 3600.0
        if dtime < 4.0:
            minutes = mdates.MinuteLocator(byminute=range(0, 60, 30))
            ax.xaxis.set_minor_locator(minutes)
            ax.xaxis.set_minor_formatter(mdates.DateFormatter(r"%H^{%M}"))
        del_t = np.rint(
            (
                self.dfs["goes"].time.tolist()[2] - self.dfs["goes"].time.tolist()[1]
            ).total_seconds()
        )
        N = int((self.dates[1] - self.dates[0]).total_seconds() / del_t)
        ax.semilogy(
            self.dfs["goes"].time.tolist()[:N],
            self.dfs["goes"].xrsa.tolist()[:N],
            "b",
            ls="-",
            lw=1.0,
            alpha=0.7,
            label=r"$\lambda_0\sim (0.05-0.4)$ nm",
        )
        ax.semilogy(
            self.dfs["goes"].time.tolist()[:N],
            self.dfs["goes"].xrsb.tolist()[:N],
            "r",
            ls="-",
            lw=1.0,
            alpha=0.7,
            label=r"$\lambda_1\sim (0.1-0.8)$ nm",
        )
        ax.legend(loc=1)
        ax.set_xlim(dates)
        ax.set_ylim(1e-8, 1e-2)
        ax.axhline(1e-4, color="r", ls="--", lw=0.6, alpha=0.7)
        ax.axhline(1e-5, color="orange", ls="--", lw=0.6, alpha=0.7)
        ax.axhline(1e-6, color="darkgreen", ls="--", lw=0.6, alpha=0.7)
        ax.text(
            self.dates[0] + dt.timedelta(minutes=5),
            3e-6,
            "C",
            fontdict={"size": 10, "color": "darkgreen"},
        )
        ax.text(
            self.dates[0] + dt.timedelta(minutes=5),
            3e-5,
            "M",
            fontdict={"size": 10, "color": "orange"},
        )
        ax.text(
            self.dates[0] + dt.timedelta(minutes=5),
            3e-4,
            "X",
            fontdict={"size": 10, "color": "red"},
        )
        if len(self.flare) > 0:
            ax.axvline(
                self.flare["event_starttime"].to_datetime()[0],
                color="r",
                ls="--",
                lw=0.6,
                alpha=0.7,
            )
            ax.axvline(
                self.flare["event_endtime"].to_datetime()[0],
                color="r",
                ls="--",
                lw=0.6,
                alpha=0.7,
            )
            ax.axvline(
                self.flare["event_peaktime"].to_datetime()[0],
                color="k",
                ls="--",
                lw=0.6,
                alpha=0.7,
            )
            ar = str(self.flare["ar_noaanum"][0]) if self.flare["ar_noaanum"][0] else "-"
            txt = f"Class: {self.flare['fl_goescls'][0]} \n"
            txt += f"AR: {ar}"
            ax.text(
                0.05, 1.1,
                txt,
                ha="left", va="center",
                transform=ax.transAxes,
                fontdict={"size": 8, "color": "k"},
            )
            txt = fr"$F_s-${self.flare['event_starttime'].to_datetime()[0].strftime('%H:%M')}, "
            txt += fr"$F_p-${self.flare['event_peaktime'].to_datetime()[0].strftime('%H:%M')}, "
            txt += fr"$F_e-${self.flare['event_endtime'].to_datetime()[0].strftime('%H:%M')}, "
            ax.text(
                0.95, 1.2,
                txt,
                ha="right", va="center",
                transform=ax.transAxes,
                fontdict={"size": 8, "color": "k"},
            )
        if len(self.flare_info) > 0:
            ax.axvline(
                self.flare_info["event_starttime"],
                color="r",
                ls="--",
                lw=0.6,
                alpha=0.7,
            )
            ax.axvline(
                self.flare_info["event_endtime"],
                color="r",
                ls="--",
                lw=0.6,
                alpha=0.7,
            )
            ax.axvline(
                self.flare_info["event_peaktime"],
                color="k",
                ls="--",
                lw=0.6,
                alpha=0.7,
            )
            ar = str(self.flare_info["ar_noaanum"]) if self.flare_info["ar_noaanum"] else "-"
            txt = f"Class: {self.flare_info['fl_goescls']} \n"
            txt += f"AR: {ar}"
            ax.text(
                0.05, 1.1,
                txt,
                ha="left", va="center",
                transform=ax.transAxes,
                fontdict={"size": 8, "color": "k"},
            )
            txt = fr"$F_s-${self.flare_info['event_starttime'].strftime('%H:%M')} UT "+"\n"
            txt += fr"$F_p-${self.flare_info['event_peaktime'].strftime('%H:%M')} UT"+"\n"
            txt += fr"$F_e-${self.flare_info['event_endtime'].strftime('%H:%M')} UT"
            ax.text(
                0.95, 1.15,
                txt,
                ha="right", va="center",
                transform=ax.transAxes,
                fontdict={"size": 8, "color": "k"},
            )
            for k, v in zip(
                ["event_peaktime", "event_starttime", "event_endtime"],
                [f"$F_p$", f"$F_s$", f"$F_e$"]
            ):
                ax.text(
                    self.flare_info[k],
                    2e-2,
                    v,
                    ha="center",
                    va="center",
                    fontdict={"size": 8, "color": "k"},
                )
        if xlabel == "":
            ax.set_xticklabels([])
        return

    def save(self, figname=None, folder="assets/data/figures/goes/"):
        os.makedirs(folder, exist_ok=True)
        figname = figname if figname else folder + f"{self.dates[0].strftime('%Y%m%d')}.png"
        self.fig.savefig(figname, bbox_inches="tight")        
        return

    def close(self):
        plt.close()
        return


if __name__ == "__main__":
    dates = [dt.datetime(2021, 10, 28, 15), dt.datetime(2021, 10, 28, 16)]
    FlareTS(dates).plot_TS()
