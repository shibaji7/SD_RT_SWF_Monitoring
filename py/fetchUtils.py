#!/usr/bin/env python

"""fetchUtils.py: utility module to fetch fitacf<v> level data."""

__author__ = "Chakraborty, S."
__copyright__ = ""
__credits__ = []
__license__ = "MIT"
__version__ = "1.0."
__maintainer__ = "Chakraborty, S."
__email__ = "shibaji7@vt.edu"
__status__ = "Research"

import bz2
import datetime as dt
import glob
import os

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pydarn
import tidUtils
from dataUtils import Beam, Scan
from loguru import logger
from scipy import stats


def smooth(x, window_len=101, window="hanning"):
    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")
    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")
    if window_len < 3:
        return x
    if not window in ["flat", "hanning", "hamming", "bartlett", "blackman"]:
        raise ValueError(
            "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"
        )
    s = np.r_[x[window_len - 1 : 0 : -1], x, x[-2 : -window_len - 1 : -1]]
    if window == "flat":
        w = numpy.ones(window_len, "d")
    else:
        w = eval("np." + window + "(window_len)")
    y = np.convolve(w / w.sum(), s, mode="valid")
    d = window_len - 1
    y = y[int(d / 2) : -int(d / 2)]
    return y


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


class FetchData(object):
    """Class to fetch data from fitacf files for one radar for atleast a day"""

    def __init__(
        self,
        rad,
        date_range,
        ftype="fitacf",
        files=None,
        verbose=True,
    ):
        """
        initialize the vars
        rad = radar code
        date_range = [ start_date, end_date ]
        files = List of files to load the data from
        e.x :   rad = "sas"
                date_range = [
                    datetime.datetime(2017,3,17),
                    datetime.datetime(2017,3,18),
                ]
        """
        self.rad = rad
        self.date_range = date_range
        self.files = files
        self.verbose = verbose
        self.regex = "/sd-data/{year}/{ftype}/{rad}/{date}.*.{ftype}.bz2"
        self.ftype = ftype
        if (rad is not None) and (date_range is not None) and (len(date_range) == 2):
            self._create_files()
        self.s_params = [
            "bmnum",
            "noise.sky",
            "tfreq",
            "scan",
            "nrang",
            "intt.sc",
            "intt.us",
            "mppul",
            "rsep",
            "cp",
            "frang",
            "smsep",
            "lagfr",
            "channel",
            "mplgs",
            "nave",
            "noise.search",
            "mplgexs",
            "xcf",
            "noise.mean",
            "ifmode",
            "bmazm",
            "rxrise",
            "mpinc",
        ]
        self.v_params = ["v", "w_l", "gflg", "p_l", "slist"]
        self.hdw_data = pydarn.read_hdw_file(self.rad)
        self.lats, self.lons = pydarn.Coords.GEOGRAPHIC(self.hdw_data.stid)
        return

    def _create_files(self):
        """
        Create file names from date and radar code
        """
        if self.files is None:
            self.files = []
        reg_ex = self.regex
        days = (self.date_range[1] - self.date_range[0]).days + 2
        ent = -1
        for d in range(-1, days):
            e = self.date_range[0] + dt.timedelta(days=d)
            fnames = sorted(
                glob.glob(
                    reg_ex.format(
                        year=e.year,
                        rad=self.rad,
                        ftype=self.ftype,
                        date=e.strftime("%Y%m%d"),
                    )
                )
            )
            for fname in fnames:
                tm = fname.split(".")[1]
                sc = fname.split(".")[2]
                dus = dt.datetime.strptime(
                    fname.split(".")[0].split("/")[-1] + tm + sc, "%Y%m%d%H%M%S"
                )
                due = dus + dt.timedelta(hours=2)
                if (ent == -1) and (dus <= self.date_range[0] <= due):
                    ent = 0
                if ent == 0:
                    self.files.append(fname)
                if (ent == 0) and (dus <= self.date_range[1] <= due):
                    ent = -1
        return

    def _parse_data(self, data, s_params, v_params, by):
        """
        Parse data by data type
        data: list of data dict
        params: parameter list to fetch
        by: sort data by beam or scan
        """
        _b, _s = [], []
        if self.verbose:
            logger.info("Started converting to beam data.")
        for d in data:
            time = dt.datetime(
                d["time.yr"],
                d["time.mo"],
                d["time.dy"],
                d["time.hr"],
                d["time.mt"],
                d["time.sc"],
                d["time.us"],
            )
            if time >= self.date_range[0] and time <= self.date_range[1]:
                bm = Beam()
                bm.set(time, d, s_params, v_params)
                _b.append(bm)
        if self.verbose:
            logger.info("Converted to beam data.")
        if by == "scan":
            if self.verbose:
                logger.info("Started converting to scan data.")
            scan, sc = 0, Scan(None, None)
            sc.beams.append(_b[0])
            for _ix, d in enumerate(_b[1:]):
                if d.scan == 1 and d.time != _b[_ix].time:
                    sc.update_time()
                    _s.append(sc)
                    sc = Scan(None, None)
                    sc.beams.append(d)
                else:
                    sc.beams.append(d)
            sc.update_time()
            _s.append(sc)
            if self.verbose:
                logger.info("Converted to scan data.")
        return _b, _s, True

    def convert_to_pandas(
        self,
        beams,
    ):
        """
        Convert the beam data into dataframe
        """
        if "time" not in self.s_params:
            self.s_params.append("time")
        _o = dict(
            zip(
                self.s_params + self.v_params,
                ([] for _ in self.s_params + self.v_params),
            )
        )
        for b in beams:
            l = len(getattr(b, "slist"))
            for p in self.v_params:
                _o[p].extend(getattr(b, p))
            for p in self.s_params:
                _o[p].extend([getattr(b, p)] * l)
        L = len(_o["slist"])
        for p in self.s_params + self.v_params:
            if len(_o[p]) < L:
                l = len(_o[p])
                _o[p].extend([np.nan] * (L - l))
        return pd.DataFrame.from_records(_o)

    def scans_to_pandas(
        self,
        scans,
        start_scnum=0,
        flt=False,
    ):
        """
        Convert the scan data into dataframe
        """
        if "time" not in self.s_params:
            self.s_params.append("time")
        if "srange" not in self.v_params:
            self.v_params.append("srange")
        if "intt" not in self.s_params:
            self.s_params.append("intt")
        _o = dict(
            zip(
                self.s_params + self.v_params + ["scnum", "scan_time"],
                ([] for _ in self.s_params + self.v_params + ["scnum", "scan_time"]),
            )
        )
        for idn, s in enumerate(scans):
            for b in s.beams:
                l = len(getattr(b, "slist"))
                for p in self.v_params:
                    _o[p].extend(getattr(b, p))
                for p in self.s_params:
                    _o[p].extend([getattr(b, p)] * l)
                _o["scnum"].extend([idn + start_scnum] * l)
                _o["scan_time"].extend([getattr(b, "scan_time")] * l)
            L = len(_o["slist"])
            for p in self.s_params + self.v_params:
                if len(_o[p]) < L:
                    l = len(_o[p])
                    _o[p].extend([np.nan] * (L - l))
        return pd.DataFrame.from_records(_o)

    def __get_location__(self, row):
        """
        Get locations
        """
        lat, lon, dtime = (
            self.lats[row["slist"], row["bmnum"]],
            self.lons[row["slist"], row["bmnum"]],
            row["time"],
        )
        row["glat"], row["glon"] = lat, lon
        return row

    def pandas_to_beams(
        self,
        df,
    ):
        """
        Convert the dataframe to beam
        """
        if "time" not in self.s_params:
            self.s_params.append("time")
        beams = []
        for bm in np.unique(df.bmnum):
            o = df[df.bmnum == bm]
            d = o.to_dict(orient="list")
            for p in self.s_params:
                d[p] = d[p][0]
            b = Beam()
            b.set(o.time.tolist()[0], d, self.s_params, self.v_params)
            beams.append(b)
        return beams

    def pandas_to_scans(
        self,
        df,
    ):
        """
        Convert the dataframe to scans
        """
        if "time" not in self.s_params:
            self.s_params.append("time")
        scans = []
        for sn in np.unique(df.scnum):
            o = df[df.scnum == sn]
            beams = self.pandas_to_beams(o)
            sc = Scan(None, None)
            sc.beams.extend(beams)
            sc.update_time()
            scans.append(sc)
        return scans

    def fetch_data(
        self,
        by="beam",
    ):
        """
        Fetch data from file list and return the dataset
        params: parameter list to fetch
        by: sort data by beam or scan
        """
        data = []
        for f in self.files:
            with bz2.open(f) as fp:
                fs = fp.read()
            if self.verbose:
                logger.info(f"File:{f}")
            reader = pydarn.SuperDARNRead(fs, True)
            records = reader.read_fitacf()
            data += records
        if (by is not None) and (len(data) > 0):
            data = self._parse_data(data, self.s_params, self.v_params, by)
            return data
        else:
            return (None, None, False)

    def plot_RTI(self, beams=[], nGates=100, date_range=None, angle_th=100.0, vhm=None):
        """
        Plot RTI plots by beams
        """
        date_range = date_range if date_range else self.date_range
        beams = beams if beams and len(beams) > 0 else self.frame.bmnum.unique()

        # Reload dataset
        del self.frame
        del self.medframe
        file = os.path.join(tidUtils.get_folder(self.date_range[0]), f"{self.rad}.csv")
        mfile = os.path.join(
            tidUtils.get_folder(self.date_range[0]), f"{self.rad}_med.csv"
        )
        self.frame = pd.read_csv(file, parse_dates=["time"])
        self.medframe = pd.read_csv(mfile, parse_dates=["time"])

        for b in beams:
            file = (
                tidUtils.get_folder(self.date_range[0]) + f"/{self.rad}-{'%02d'%b}.png"
            )
            rt = RTI(
                100,
                date_range,
                f"{self.date_range[0].strftime('%Y-%m-%d')}/{self.rad}/{b}",
                num_subplots=2,
                angle_th=angle_th,
                vhm=vhm,
            )
            rt.addParamPlot(
                self.frame, b, "", xlabel="", cbar=False, fov=(self.lats, self.lons)
            )
            rt.addParamPlot(self.medframe, b, "", cbar=True, fov=(self.lats, self.lons))
            rt.save(file)
            rt.close()
        return

    def plot_FoV(self, scan_num=None, date=None, tec_mat_file=None):
        """
        Plot FoV plots by scan_num/date
        """
        if scan_num:
            scan = self.scans[scan_num]
            file = (
                tidUtils.get_folder(scan.stime)
                + f"/{self.rad}-Fan-{scan.stime.strftime('%H.%M')}.png"
            )
            fov = Fan([self.rad], scan.stime)
            fov.generate_fov(self.rad, self.frame, tec_mat_file=tec_mat_file)
            fov.save(file)
            fov.close()
        elif date:
            file = (
                tidUtils.get_folder(scan.stime)
                + f"/{self.rad}-Fan-{date.strftime('%H.%M')}.png"
            )
            fov = Fan([self.rad], date)
            fov.generate_fov(self.rad, self.frame, tec_mat_file=tec_mat_file)
            fov.save(file)
            fov.close()
        else:
            tec, tec_times = tidUtils.read_tec_mat_files(tec_mat_file)
            for scan in self.scans:
                file = (
                    tidUtils.get_folder(scan.stime)
                    + f"/{self.rad},{scan.stime.strftime('%H-%M')}.png"
                )
                fov = Fan([self.rad], scan.stime, tec=tec, tec_times=tec_times)
                fov.generate_fov(self.rad, self.frame, laytec=True)
                fov.save(file)
                fov.close()
        return

    @staticmethod
    def fetch(
        rad,
        date_range,
        ftype="fitacf",
        files=None,
        verbose=False,
    ):
        """
        Static method to fetch datasets
        """
        fd = FetchData(rad, date_range, ftype, files, verbose)
        _, scans, data_exists = fd.fetch_data(by="scan")
        if data_exists:
            fd.frame = fd.scans_to_pandas(scans)
            fd.scans = scans
            if verbose:
                logger.info(f"Data length {rad}: {len(fd.frame)}")
        #             if len(fd.frame) > 0:
        #                 fd.frame = fd.frame.apply(fd.__get_location__, axis=1)
        return fd


class SDAnalysis(object):
    """
    This class is dedicated to analyze the SD
    data in ground scatter echoes and exract
    requried parameters for report.
    """

    def __init__(
        self,
        dates,
        rads=["bks", "fhe", "fhw"],
    ):
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
                fdata = FetchData.fetch(r, self.dates)
                self.dat[r] = fdata
        return

    # TODO
    def fetch_parameters(self, echoes, time):
        """
        Ftech SD fit data and analyze
        groundscatter echoes, extract timings and
        phases.
        """
        scores = [0, 1, 2, 3]
        descriptions = [
            "Ineffective",
            "Detectable",
            "Moderate",
            "Severe",
        ]
        score = 0
        description = descriptions[score]
        o = pd.DataFrame()
        o["echoes"], o["time"] = echoes, time
        timings = {}
        timings["median"] = np.median(echoes[:100])
        timings["med"] = stats.median_absolute_deviation(echoes[:100])
        if np.min(echoes) <= 0.5 * timings["median"]:
            timings["peak_blackout"] = time[np.argmin(echoes)]
            d = o[
                (o.time < timings["peak_blackout"])
                & (o.echoes >= 0.9 * timings["median"])
            ]
            if len(d) > 0:
                timings["onset"] = d.time.tolist()[-1]
                d = o[
                    (o.time < timings["peak_blackout"])
                    & (o.echoes < 0.5 * timings["median"])
                ]
                if len(d) > 0:
                    timings["start_blackout"] = d.time.tolist()[0]
                    d = o[
                        (o.time > timings["peak_blackout"])
                        & (o.echoes > 0.5 * timings["median"])
                    ]
                    if len(d) > 0:
                        timings["end_blackout"] = d.time.tolist()[0]
                        d = o[
                            (o.time > timings["peak_blackout"])
                            & (o.echoes >= 0.9 * timings["median"])
                        ]
                        if len(d) > 0:
                            timings["recovery"] = d.time.tolist()[0]
                        else:
                            timings["recovery"] = o.time.tolist()[-5]
                    else:
                        timings["end_blackout"] = o.time.tolist()[-10]
                        timings["recovery"] = o.time.tolist()[-5]
                else:
                    timings["end_blackout"] = o.time.tolist()[-10]
                    timings["recovery"] = o.time.tolist()[-5]
                d = o[
                    (o.time >= timings["start_blackout"])
                    & (o.time <= timings["end_blackout"])
                ]
                dmedian = np.median(d.echoes)
                if dmedian <= 0.25 * timings["median"]:
                    score = 3
                    description = descriptions[score]
                elif (dmedian <= 0.5 * timings["median"]) and (
                    dmedian >= 0.25 * timings["median"]
                ):
                    score = 2
                    description = descriptions[score]
                elif (dmedian >= 0.5 * timings["median"]) and (
                    dmedian <= 0.75 * timings["median"]
                ):
                    score = 1
                    description = descriptions[score]
        timings["score"] = str(score)
        timings["description"] = description
        return timings

    def plot_TS(self, bm=None):
        """
        Plot time series data
        """
        self.get_SD_data()
        fig = plt.figure(figsize=(6, 2.5 * len(self.rads)), dpi=150)
        for i, r in enumerate(self.rads):
            o = self.dat[r]
            if len(o) > 0:
                if bm:
                    o = o[o.bmnum == bm]

                tfreq = np.unique(np.round((2 * (o.tfreq / 1e3)) / 2))
                tfreq = [str(x) for x in tfreq]
                o = o.groupby("time").count().reset_index()
                ax = fig.add_subplot(len(self.rads), 1, i + 1)
                ax.set_ylabel(r"$<E>$", fontdict={"size": 12, "fontweight": "bold"})
                text = r"Radar: {}, Beam: {}, $f_0\sim$ {} MHz".format(
                    r.upper(), bm, "/".join(tfreq)
                )
                ax.text(
                    0.1,
                    0.9,
                    text,
                    ha="left",
                    va="center",
                    transform=ax.transAxes,
                    fontdict={"size": 8, "fontweight": "bold"},
                )
                ax.xaxis.set_major_formatter(DateFormatter(r"%H^{%M}"))
                hours = mdates.HourLocator(byhour=range(0, 24, 1))
                ax.xaxis.set_major_locator(hours)
                dtime = (self.dates[1] - self.dates[0]).total_seconds() / 3600.0
                if dtime < 4.0:
                    minutes = mdates.MinuteLocator(byminute=range(0, 60, 10))
                    ax.xaxis.set_minor_locator(minutes)
                    ax.xaxis.set_minor_formatter(DateFormatter(r"%H^{%M}"))
                ax.set_ylim(0, 40)
                ax.set_xlim(self.dates)
                ax.plot(o.time, o.v, "ko", ms=1.2, alpha=0.8)
        ax.set_xlabel("Time, UT", fontdict={"size": 12, "fontweight": "bold"})
        fig.subplots_adjust(hspace=0.2)
        return self

    def plot_summary_TS(self):
        setup()
        self.fig = plt.figure(figsize=(6, 2.5), dpi=150)
        ax = self.fig.add_subplot(111)
        self.plot_summary_TS_from_axes(ax)
        return

    def plot_summary_TS_from_axes(self, ax, xlabel="Time (UT)"):
        """
        Plot time series data
        """
        self.get_SD_data()
        ax.set_ylabel(r"Echoes ($<E>$)", fontdict={"size": 12, "fontweight": "bold"})
        ax.xaxis.set_major_formatter(mdates.DateFormatter(r"%H^{%M}"))
        hours = mdates.HourLocator(byhour=range(0, 24, 1))
        ax.xaxis.set_major_locator(hours)
        dtime = (self.dates[1] - self.dates[0]).total_seconds() / 3600.0
        if dtime < 4.0:
            minutes = mdates.MinuteLocator(byminute=range(0, 60, 30))
            ax.xaxis.set_minor_locator(minutes)
            ax.xaxis.set_minor_formatter(mdates.DateFormatter(r"%H^{%M}"))
        ax.set_ylim(0, 40)
        ax.set_xlim(self.dates)
        ax.set_xlabel("Time (UT)", fontdict={"size": 12, "fontweight": "bold"})
        text = r"Radars: [{}]".format(", ".join(self.rads))
        ax.text(
            0.05,
            0.95,
            text,
            ha="left",
            va="center",
            transform=ax.transAxes,
            fontdict={"size": 10, "fontweight": "bold"},
        )
        ax.text(
            1.05,
            0.99,
            "SuperDARN",
            ha="center",
            va="top",
            fontdict={"size": 12, "fontweight": "bold"},
            transform=ax.transAxes,
            rotation=90,
        )

        df = pd.DataFrame()
        for i, r in enumerate(self.rads):
            if hasattr(self.dat[r], "frame"):
                o = self.dat[r].frame
                if len(o) > 0:
                    df = pd.concat([df, o])
        if len(df) > 0:
            df = df.groupby("time").count().reset_index()
            timings = self.fetch_parameters(smooth(np.array(df.v)), df.time.tolist())
            import pytz
            cet = pytz.timezone('US/Central')
            offset = cet.utcoffset(df.time.tolist()[0],is_dst = True)
            local_times = [
                t + offset
                for t in df.time.tolist()
            ]
            ax.plot(df.time, df.v, "ko", ms=1.2, alpha=0.8)
            ax.plot(df.time, smooth(np.array(df.v)), "r-", lw=0.8, alpha=0.8)
            twax = ax.twiny()
            twax.xaxis.set_major_formatter(mdates.DateFormatter(r"%H^{%M}"))
            twax.xaxis.set_ticks_position("bottom")
            twax.spines["bottom"].set_position(("outward", 36))
            twax.xaxis.set_label_position("bottom")
            twax.set_xlabel("Time (US/CST)", fontdict={"size": 12, "fontweight": "bold"})
            twax.plot(local_times, [np.nan]*len(local_times))
            twax.set_xlim(local_times[0], local_times[-1])
            ax.axhline(timings["median"], color="b", ls="-", lw=0.5)
            text = ""
            if "onset" in timings:
                ax.axvline(timings["onset"], color="darkred", ls="-", lw=0.8)
                text += f"O-{timings['onset'].strftime('%H:%M:%S')} UT [Onset]" + "\n"
                ax.text(
                    timings["onset"],
                    41,
                    "O",
                    ha="center",
                    va="center",
                    fontdict={"size": 8, "color": "k"},
                )
            if "start_blackout" in timings:
                ax.axvline(timings["start_blackout"], color="k", ls="-", lw=0.8)
                text += fr"$B_s$-{timings['start_blackout'].strftime('%H:%M:%S')} UT [Blackout Start]" + "\n"
                ax.text(
                    timings["start_blackout"],
                    41,
                    r"$B_s$",
                    ha="center",
                    va="center",
                    fontdict={"size": 8, "color": "k"},
                )
            if "end_blackout" in timings:
                ax.axvline(timings["end_blackout"], color="b", ls="-", lw=0.8)
                text += fr"$B_e$-{timings['end_blackout'].strftime('%H:%M:%S')} UT [Blackout End]" + "\n"
                ax.text(
                    timings["end_blackout"],
                    41,
                    r"$B_e$",
                    ha="center",
                    va="center",
                    fontdict={"size": 8, "color": "k"},
                )
            if "recovery" in timings:
                ax.axvline(timings["recovery"], color="g", ls="-", lw=0.8)
                text += f"R-{timings['recovery'].strftime('%H:%M:%S')} UT [Recovery]" 
                ax.text(
                    timings["recovery"],
                    41,
                    "R",
                    ha="center",
                    va="center",
                    fontdict={"size": 8, "color": "k"},
                )
            ax.text(
                0.65,
                1.15,
                text,
                ha="left",
                va="center",
                fontdict={"size": 8, "fontweight": "bold"},
                transform=ax.transAxes,
            )
        self.fig.subplots_adjust(hspace=0.25)
        return timings

    def save(self, figname=None, folder="assets/data/figures/rads/"):
        os.makedirs(folder, exist_ok=True)
        figname = figname if figname else folder + f"{self.dates[0].strftime('%Y%m%d')}.png"
        self.fig.savefig(figname, bbox_inches="tight")
        return
    
    def close(self):
        plt.close()
        return