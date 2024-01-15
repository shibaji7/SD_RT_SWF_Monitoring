"""
drap.py: Run new DRAP model
"""

__author__ = "Chakraborty, S."
__copyright__ = ""
__credits__ = []
__license__ = "MIT"
__version__ = "1.0."
__maintainer__ = "Chakraborty, S."
__email__ = "shibaji7@vt.edu"
__status__ = "Research"

import numpy as np
from goes import FlareTS
from pysolar.solar import get_altitude
import datetime as dt

import matplotlib.pyplot as plt
import mplstyle
from cartoUtils import SDCarto
import cartopy
import matplotlib.ticker as mticker
import tidUtils
from cartopy.mpl.gridliner import LATITUDE_FORMATTER, LONGITUDE_FORMATTER
import os

class DRAP(object):

    def __init__(self, event, date=None):
        self.event = event
        for k in self.event.keys():
            setattr(self, k, self.event[k])
        self.date = date if date else self.event_peaktime
        self.flareTS = FlareTS([self.event_starttime, self.event_endtime])
        self.run_event_analysis()
        return

    def run_event_analysis(self, date=None):
        date = date if date else self.date
        goes = self.flareTS.dfs["goes"].copy()
        goes["time"] = goes.time.apply(lambda x: x.replace(microsecond=0))
        goes = goes[goes.time==date]
        F = goes.xrsb.tolist()[0]
        lats = np.arange(-90,90,1)
        lons = np.arange(-180,180,2)
        lat_grd, lon_grd = np.meshgrid(lats, lons)
        absp = np.zeros_like(lat_grd)*np.nan
        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                absp[i,j] = self.calc_absorption(lat, lon, date, F)
        self.draw_image(date, lat_grd, lon_grd, absp)
        return

    def calc_absorption(self, lat, lon, date, F):
        ax = np.nan
        sza = self.get_solar(lat, lon, date)
        if sza < 105.:
            COS = np.cos(np.deg2rad(sza)) if sza <= 90. else 0.
            ax = COS * F * 12080
        return ax

    def get_solar(self, lat, lon, date):
        date = date.to_pydatetime()
        date = date.replace(tzinfo=dt.timezone.utc)
        sza = float(90)-get_altitude(lat, lon, date)
        return sza

    def draw_image(self, date, lat_grd, lon_grd, absp):
        self.fig = plt.figure(dpi=240)
        proj = cartopy.crs.PlateCarree(-90.0)
        #proj = cartopy.crs.Stereographic(central_longitude=-90.0, central_latitude=45.0)
        ax = self.fig.add_subplot(
            111,
            projection="SDCarto",
            map_projection=proj,
            coords=self.coord,
            plot_date=self.date,
        )
        ax.overaly_coast_lakes(lw=0.4, alpha=0.4)
        ax.set_extent([-180, 180, -90, 90], crs=cartopy.crs.PlateCarree())
        # plt_lons = np.arange(-180, 181, 15)
        # mark_lons = np.arange(-180, 181, 30)
        # plt_lats = np.arange(40, 90, 10)
        # gl = ax.gridlines(crs=cartopy.crs.PlateCarree(), linewidth=0.5)
        # gl.xlocator = mticker.FixedLocator(plt_lons)
        # gl.ylocator = mticker.FixedLocator(plt_lats)
        # gl.xformatter = LONGITUDE_FORMATTER
        # gl.yformatter = LATITUDE_FORMATTER
        # gl.n_steps = 90
        # ax.mark_latitudes(plt_lats, fontsize="small", color="darkred")
        # ax.mark_longitudes(mark_lons, fontsize="small", color="darkblue")
        self.proj = proj
        self.geo = cartopy.crs.PlateCarree(-90.0)
        ax.text(
            -0.02,
            0.99,
            "Coord: Geo",
            ha="center",
            va="top",
            transform=ax.transAxes,
            fontsize="small",
            rotation=90,
        )
        ax.text(
            0.05,
            1.05,
            self.event_peaktime.strftime("%Y-%m-%d %H:%M") + " UT",
            ha="left",
            va="center",
            transform=ax.transAxes,
            fontsize="small"
        )
        XYZ = self.proj.transform_points(self.geo, lon_grd, lat_grd)
        Px = np.ma.masked_invalid(absp)
        im = ax.pcolor(
                XYZ[:, :, 0],
                XYZ[:, :, 1],
                Px.T,
                transform=self.proj,
                cmap="jet",
                vmax=5,
                vmin=0,
                alpha=0.4,
            )
        ax._add_colorbar(im, r"$A_{30}$, dB")
        self.save()
        self.close()
        return

    def save(self, figname=None, folder="assets/data/figures/drap/"):
        os.makedirs(folder, exist_ok=True)
        figname = figname if figname else folder + f"{self.event_starttime.strftime('%Y%m%d')}.png"
        self.fig.savefig(figname, bbox_inches="tight")        
        return

    def close(self):
        plt.close()
        return
