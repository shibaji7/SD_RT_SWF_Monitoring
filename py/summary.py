#!/usr/bin/env python

"""
    summary.py: module to create calender-flare informations and summay plots
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
import random

import cartopy
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import mplstyle
import numpy as np
from cartopy.mpl.gridliner import LATITUDE_FORMATTER, LONGITUDE_FORMATTER
from cartoUtils import SDCarto
from fetchUtils import SDAnalysis
from goes import FlareTS


class Summary(object):
    def __init__(self, event, date=None):
        mplstyle.call()
        SDCarto.call()
        self.event = event
        for k in self.event.keys():
            setattr(self, k, self.event[k])
        self.date = date if date else self.event_peaktime
        file = f"{self.event_starttime.strftime('%Y%m%d')}.png"
        self.file_names = dict(
            goes_file=f"assets/data/figures/goes/{file}",
            sd_file=f"assets/data/figures/rads/{file}",
            summary_file=f"assets/data/figures/sd_summary/{file}",
            summary_dn_file=f"assets/data/figures/sd_dn_summary/{file}",
        )
        return

    def create_overlap_summary_plot(self, date=None):
        date = date if date else self.date
        if not os.path.exists(self.file_names["summary_file"]):
            # GOES plot
            flare_info = dict(
                event_starttime=self.event_starttime,
                event_peaktime=self.event_peaktime,
                event_endtime=self.event_endtime,
                fl_goescls=self.fl_goescls,
                ar_noaanum=self.ar_noaanum,
            )
            self.flareTS = FlareTS(
                [self.start_time, self.end_time], flare_info=flare_info
            )
            goes = self.flareTS.dfs["goes"].copy()
            goes["time"] = goes.time.apply(lambda x: x.replace(microsecond=0))
            self.flareTS.plot_TS()
            self.flareTS.save(self.file_names["goes_file"])
            self.flareTS.close()
            # SD plot
            self.sd = SDAnalysis(dates=[self.start_time, self.end_time], rads=self.rads)
            setattr(self.sd, "sd_timings", self.sd.plot_summary_TS())
            self.sd.save(self.file_names["sd_file"])
            self.sd.close()
            # Summary plot
            self.__run_summary_map_plots__()
            self.__run_summary_plots__()
        return

    def __run_summary_map_plots__(self):
        # Create radars with overlaying plots [at peak]
        folder = f"assets/data/figures/sd_dn_summary/"
        os.makedirs(folder, exist_ok=True)
        self.fig = plt.figure(dpi=300, figsize=(2, 3))
        # proj = cartopy.crs.Stereographic(central_longitude=-90.0, central_latitude=45.0)
        proj = cartopy.crs.PlateCarree(central_longitude=-120)
        ax = self.fig.add_subplot(
            111,
            projection="SDCarto",
            map_projection=proj,
            coords=self.coord,
            plot_date=self.date,
        )
        ax.overaly_coast_lakes(lw=0.2, alpha=0.4)
        ax.set_extent([-130, -50, 30, 70], crs=cartopy.crs.PlateCarree())
        plt_lons = np.arange(-180, 181, 45)
        mark_lons = np.arange(-180, 181, 45)
        plt_lats = np.arange(40, 90, 25)
        gl = ax.gridlines(crs=cartopy.crs.PlateCarree(), linewidth=0.1)
        gl.xlocator = mticker.FixedLocator(plt_lons)
        gl.ylocator = mticker.FixedLocator(plt_lats)
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        gl.n_steps = 90
        self.proj = proj
        self.geo = cartopy.crs.PlateCarree()
        import pytz

        date = self.event_peaktime.to_pydatetime()
        to_cst = date.replace(tzinfo=pytz.utc).astimezone(pytz.timezone("US/Central"))
        txt = f"Flare Peak: {date.strftime('%Y-%m-%d [%H:%M')} UT"
        txt += f" / {to_cst.strftime('%H:%M')} CST]"
        ax.text(
            0.05,
            1.05,
            txt,
            ha="left",
            va="center",
            transform=ax.transAxes,
            fontsize=4,
        )
        ax.text(
            -0.02,
            0.99,
            "Coord: Geo",
            ha="center",
            va="top",
            transform=ax.transAxes,
            fontsize=4,
            rotation=90,
        )
        ax.draw_DN_terminator(self.event_peaktime.to_pydatetime())
        colors = ["b", "k", "r", "m"]
        for rad in self.rads:
            col = random.choice(colors)
            ax.overlay_radar(rad, fontSize=4, font_color=col, markerColor=col)
            ax.overlay_fov(rad, lineColor=col, lineWidth=0.3, fovColor=None)
        ax.text(
            1.01,
            0.99,
            "BKS - Blackstone\n FHE/W - Fort Hays East/West",
            ha="left",
            va="top",
            transform=ax.transAxes,
            fontdict={"size": 3, "color": "k"},
            rotation=90,
        )
        figname = self.file_names["summary_dn_file"]
        self.fig.savefig(figname, bbox_inches="tight")
        plt.close()
        return

    def __run_summary_plots__(self):
        # Merge GOES and SD
        folder = f"assets/data/figures/sd_summary/"
        os.makedirs(folder, exist_ok=True)
        self.fig = plt.figure(figsize=(6, 8), dpi=180)
        self.flareTS.plot_TS_from_axes(self.fig.add_subplot(311), xlabel="")
        self.sd.plot_summary_TS_from_axes(self.fig.add_subplot(312))
        figname = self.file_names["summary_file"]
        self.fig.subplots_adjust(wspace=0.35, hspace=0.35)
        self.fig.savefig(figname, bbox_inches="tight")
        plt.close()
        return
