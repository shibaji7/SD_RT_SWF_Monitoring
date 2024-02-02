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

    def __init__(self, event, date=None, folder="assets/data/figures/drap/"):
        self.event = event
        for k in self.event.keys():
            setattr(self, k, self.event[k])
        self.date = date if date else self.event_peaktime
        self.flareTS = FlareTS([self.event_starttime, self.event_endtime])
        self.folder = folder
        os.makedirs(folder, exist_ok=True)
        self.figname = self.folder + f"{self.event_starttime.strftime('%Y%m%d')}.png"
        if not os.path.exists(self.figname):
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
        absp, drap_absp = (
            np.zeros_like(lat_grd)*np.nan,
            np.zeros_like(lat_grd)*np.nan
        )
        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                absp[i,j], drap_absp[i,j] = self.calc_absorption(lat, lon, date, F)
        self.draw_image(date, lat_grd, lon_grd, absp, drap_absp)
        return

    def calc_absorption(self, lat, lon, date, F):
        ax, adrap = np.nan, np.nan
        sza = self.get_solar(lat, lon, date)
        if sza < 105.:
            COS = np.cos(np.deg2rad(sza)) if sza <= 90. else 0.
            ax = COS * F * 12080
            HAF = (10*np.log10(F) + 65) * (COS**0.75)
            adrap = (HAF/30)**1.5
        return ax, adrap

    def get_solar(self, lat, lon, date):
        date = date.to_pydatetime()
        date = date.replace(tzinfo=dt.timezone.utc)
        sza = float(90)-get_altitude(lat, lon, date)
        return sza

    def draw_image(self, date, lat_grd, lon_grd, absp, drap_absp):
        self.fig = plt.figure(dpi=240, figsize=(4.5,4.5))
        self.draw_image_axes(
            self.create_ax(211, date, "DRAP2"), 
            drap_absp, lon_grd, lat_grd, True
        )
        self.draw_image_axes(
            self.create_ax(212, date, "X-RAP"), 
            absp, lon_grd, lat_grd, True
        )
        self.save()
        self.close()
        return

    def save(self, figname=None):
        figname = figname if figname else self.figname
        self.fig.savefig(figname, bbox_inches="tight")        
        return

    def close(self):
        plt.close()
        return

    def draw_image_axes(self, ax, Px, lon_grd, lat_grd, add_cbar=True):
        XYZ = self.proj.transform_points(self.geo, lon_grd, lat_grd)
        Px = np.ma.masked_invalid(Px)
        im = ax.pcolor(
                XYZ[:, :, 0],
                XYZ[:, :, 1],
                Px.T,
                transform=self.proj,
                cmap="Reds",
                vmax=5,
                vmin=0,
                alpha=0.7,
            )
        if add_cbar:
            ax._add_colorbar(im, r"$A_{30}$, dB")
        for rad in ["bks","fhe","fhw"]:
            ax.overlay_fov(rad, lineColor="k")
        return

    def create_ax(self, id, date, model, lay_txt=True):
        proj = cartopy.crs.PlateCarree()
        ax = self.fig.add_subplot(
            id,
            projection="SDCarto",
            map_projection=proj,
            coords=self.coord,
            plot_date=self.date,
        )
        ax.overaly_coast_lakes(lw=0.2, alpha=0.4)
        ax.set_extent([-180, 180, -90, 90], crs=cartopy.crs.PlateCarree())
        self.proj = proj
        self.geo = cartopy.crs.PlateCarree()
        if lay_txt:
            ax.text(
                -0.02,
                0.99,
                "Coord: Geo",
                ha="center",
                va="top",
                transform=ax.transAxes,
                fontsize=7,
                rotation=90,
            )
            ax.text(
                0.01,
                1.05,
                date.strftime("%Y-%m-%d %H:%M") + " UT",
                ha="left",
                va="center",
                transform=ax.transAxes,
                fontsize=7
            )
        ax.text(
            0.99,
            1.05,
            f"HF Absorption Model (@30 MHz): {model}",
            ha="right",
            va="center",
            transform=ax.transAxes,
            fontsize=7
        )
        ax.draw_DN_terminator(self.event_peaktime.to_pydatetime())
        return ax
