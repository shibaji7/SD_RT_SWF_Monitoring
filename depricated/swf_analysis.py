#!/usr/bin/env python

"""
    swf_analysis.py: This module is dedicated for fetching the GOES X-ray timeseries
                        for a given date and time limit and SuperDARN observations 
                        from a specific radar/beam with a time limit. The module provides
                        some helper functions to extract peak, start and end of a flare 
                        from GOES data. Inaddition it can also provides SWF onset, blackout 
                        start, stop, and recovery observed by a radar (total / beam-by-beam).
"""

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
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pydarnio as pydarn
from loguru import logger
from sunpy import timeseries as ts
from sunpy.net import Fido
from sunpy.net import attrs as a
from sunpy.time import parse_time


class FetchFitData(object):
    """
    This class uses pyDarn to access local repository for radar observations.
    """

    def __init__(
        self,
        sDate,
        eDate,
        rad,
        ftype="fitacf",
        files=None,
        regex="/sd-data/{year}/{ftype}/{rad}/{date}.*{ftype}*.bz2",
    ):
        """
        Parameters:
        -----------
        sDate = Start datetime of analysis
        eDate = End datetime of analysis
        rad = Radar code
        ftype = SD 'fit' file type [fitacf/fitacf3]
        files = List of files to load the data from (optional)
        regex = Regular expression to locate files
        """
        self.rad = rad
        self.sDate = sDate
        self.eDate = eDate
        self.files = files
        self.regex = regex
        self.ftype = ftype
        if (rad is not None) and (sDate is not None) and (eDate is not None):
            self.__createFileList__()
        return

    def __createFileList__(self):
        """
        Create file names from date and radar code
        """
        if self.files is None:
            self.files = []
        reg_ex = self.regex
        days = (self.eDate - self.sDate).days + 2
        for d in range(-1, days):
            e = self.sDate + dt.timedelta(days=d)
            fnames = glob.glob(
                reg_ex.format(
                    year=e.year,
                    rad=self.rad,
                    ftype=self.ftype,
                    date=e.strftime("%Y%m%d"),
                )
            )
            fnames.sort()
            for fname in fnames:
                tm = fname.split(".")[1]
                sc = fname.split(".")[2]
                d0 = dt.datetime.strptime(
                    fname.split(".")[0].split("/")[-1] + tm + sc, "%Y%m%d%H%M%S"
                )
                d1 = d0 + dt.timedelta(hours=2)
                if (self.sDate <= d0) and (d0 <= self.eDate):
                    self.files.append(fname)
                elif d0 <= self.sDate <= d1:
                    self.files.append(fname)
        self.files = list(set(self.files))
        self.files.sort()
        self.fetch_data()
        return

    def fetch_data(
        self,
        scalerParams=[
            "bmnum",
            "noise.sky",
            "tfreq",
            "scan",
            "nrang",
            "intt.sc",
            "intt.us",
            "mppul",
            "nrang",
            "rsep",
            "cp",
            "frang",
            "smsep",
            "lagfr",
            "channel",
        ],
        vectorParams=["v", "w_l", "gflg", "p_l", "slist", "v_e"],
    ):
        """
        Fetch data from file list and return the dataset
        params: parameter list to fetch
        by: sort data by beam or scan
        scan_prop: provide scan properties if by='scan'
                   {"s_mode": type of scan, "s_time": duration in min}
        """
        records = []
        for f in self.files:
            with bz2.open(f) as fp:
                fs = fp.read()
            logger.info(f"Read file - {f}")
            reader = pydarn.SDarnRead(fs, True)
            records += reader.read_fitacf()
        self.records = pd.DataFrame()
        self.echoRecords = []
        for rec in records:
            time = dt.datetime(
                rec["time.yr"],
                rec["time.mo"],
                rec["time.dy"],
                rec["time.hr"],
                rec["time.mt"],
                rec["time.sc"],
                rec["time.us"],
            )
            eRec = {
                "time": time,
                "bmnum": rec["bmnum"],
                "eCount": len(rec["slist"]) if "slist" in rec.keys() else 0,
            }
            o = pd.DataFrame()
            for p in vectorParams:
                if p in rec.keys():
                    o[p] = rec[p]
                else:
                    o[p] = [np.nan]
            for p in scalerParams:
                o[p] = rec[p]
            o["time"] = time
            self.records = pd.concat([self.records, o])
            self.echoRecords.append(eRec)
        self.echoRecords = pd.DataFrame.from_records(self.echoRecords)
        return


class Fadeout(object):
    """
    This class takes help from sunpy and FetchFitData class to identify flare
    and SWF signatures in GOES X-ary and SuperDARN observations, respectively,
    at a given time and SuperDARN radar.
    """

    def __init__(
        self,
        sDate,
        eDate,
        rads=[],
    ):
        """
        Properties:
        -----------
        sDate = Start datetime of analysis
        eDate = End datetime of analysis
        rads = List of radar codes
        """
        self.sDate = sDate
        self.eDate = eDate
        self.rads = rads
        self.setThresholds()
        # Dictionary of Dataframe holding all datasets
        self.dfs = {}
        self.__loadGOES__()
        self.__loadDARN__()
        return

    def setThresholds(
        self,
        thOnset=0.2,
        thBlackoutS=0.6,
        thBlackoutE=0.5,
        thRecovery=0.95,
    ):
        """
        Set threhsolds values for different phases.

        Parameters:
        -----------
        thOnset = Threshold for onset
        thBlackoutS = Threshold for blackout start
        thBlackoutE = Threshold for blackout end
        thRecovery = Threshold for recovery

        Operation:
        ----------
        tOnset: eCount <= thOnset*BGC
        tBlackoutS: eCount <= thBlackoutS*BGC & (time > tOnset)
        tBlackoutE: eCount >= thBlackoutE*BGC & (time > tBlackoutS)
        tRecovery: eCount >= thRecovery*BGC & (time > tBlackoutE)
        *BGC: Background echo counts.
        """
        self.thOnset = thOnset
        self.thBlackoutS = thBlackoutS
        self.thBlackoutE = thBlackoutE
        self.thRecovery = thRecovery
        return

    def __loadGOES__(self):
        """
        Load GOES data from remote/local repository
        """
        self.dfs["goes"], self.goes, self.flareHEK = pd.DataFrame(), [], None
        result = Fido.search(
            a.Time(
                self.sDate.strftime("%Y-%m-%d %H:%M"),
                self.eDate.strftime("%Y-%m-%d %H:%M"),
            ),
            a.Instrument("XRS") | a.hek.FL & (a.hek.FRM.Name == "SWPC"),
        )
        if len(result) > 0:
            logger.info(f"Fetching GOES ...")
            tmpfiles = Fido.fetch(result)
            # Retrieve HEKTable from the Fido result and then load
            self.flareHEK = result["hek"]
            for tf in tmpfiles:
                self.goes.append(ts.TimeSeries(tf))
                self.dfs["goes"] = pd.concat(
                    [self.dfs["goes"], self.goes[-1].to_dataframe()]
                )
            self.dfs["goes"].index.name = "time"
            self.dfs["goes"] = self.dfs["goes"].reset_index()
            self.dfs["goes"] = self.dfs["goes"][
                (self.dfs["goes"].time >= self.sDate)
                & (self.dfs["goes"].time <= self.eDate)
            ]
        return

    def __loadDARN__(self):
        """
        Load SuperDARN data from local repository
        """
        self.dfs["goes"], self.darns = pd.DataFrame(), {}
        for rad in self.rads:
            self.darns[rad] = FetchFitData(
                self.sDate,
                self.eDate,
                rad,
            )
        return

    def getGOES(self):
        """
        Fetch GOES data.

        Returns:
        --------
        o = Dataframe object conatining the TS
        desciption = Description of the DF columns
                        including unit and line/color
                        preference on figure panel.
                        Also, the flare details including
                        timings and class.
        """
        o = self.dfs["goes"]
        desciption = {
            "time": {
                "desc": "Datetime of the timeseries",
                "unit": "UT",
            },
            "xrsa": {
                "desc": "Shorter X-ray (0.05-0.4 nm)",
                "unit": "W/m^2",
                "color": "b",  # Plot color
                "line": True,  # Plot as a line
            },
            "xrsb": {
                "desc": "Longer X-ray (0.1-0.8 nm)",
                "unit": "W/m^2",
                "color": "r",  # Plot color
                "line": True,  # Plot as a line
            },
        }
        if self.flareHEK and len(self.flareHEK) > 0:
            for hek in self.flareHEK:
                if (hek["event_peaktime"] > self.sDate) and (
                    hek["event_peaktime"] < self.eDate
                ):
                    break
            desciption["flare"] = {
                "class": hek["fl_goescls"],
                "sTime": parse_time(hek["event_starttime"]).datetime,
                "eTime": parse_time(hek["event_endtime"]).datetime,
                "pTime": parse_time(hek["event_peaktime"]).datetime,
            }
        return o, SimpleNamespace(**desciption)

    def getDARN(self, rad, bmnum=None):
        """
        Fetch SuperDARN data.

        Parameters:
        -----------
        rad = Radar code
        bmnum = Beam number of the radar (if None all all beams will be selected)

        Returns:
        --------
        o = Dataframe object conatining the TS
        desciption = Description of the DF columns
                        including unit and line/color
                        preference on figure panel.
                        Also, the scatter details
                        including SWF timings.
        """
        o = self.darns[rad].echoRecords if rad in self.rads else pd.DataFrame()
        o = o[o.bmnum == bmnum] if (len(o) > 0) and bmnum else o
        desciption = {
            "time": {
                "desc": "Datetime of the timeseries",
                "unit": "UT",
            },
            "bmnum": {
                "desc": "Beam number of radar",
                "unit": None,
            },
            "eCount": {
                "desc": "Number of echoes pea beam sounding",
                "unit": None,
                "color": "k",  # Plot color
                "line": False,  # Plot as scatter
            },
        }
        if len(o) > 0:
            desciption.update(self.__extractTimimgs__(o))
        return o, desciption

    def __extractTimimgs__(self, o):
        """
        Extract onset, blackout (start/end), and recovery phase timings.

        Operation:
        ----------
        tOnset: eCount <= thOnset*BGC
        tBlackoutS: eCount <= thBlackoutS*BGC & (time > tOnset)
        tBlackoutE: eCount >= thBlackoutE*BGC & (time > tBlackoutS)
        tRecovery: eCount >= thRecovery*BGC & (time > tBlackoutE)
        *BGC: Background echo counts.
        """
        o.eCount = (
            o.eCount.rolling(2, min_periods=1)
            .apply(np.median)
            .fillna(method="bfill")
            .fillna(method="ffill")
        )
        swf = {
            "tOnset": None,
            "tBlackoutS": None,
            "tBlackoutE": None,
            "tRecovery": None,
        }
        BGC = np.median(
            o[
                (o.time > self.sDate) & (o.time > self.sDate + dt.timedelta(minutes=2))
            ].eCount
        )
        swf["tOnset"] = o[o.eCount <= BGC * self.thOnset].time.iloc[0]
        swf["tBlackoutS"] = o[
            (o.eCount <= BGC * self.thBlackoutS) & (o.time >= swf["tOnset"])
        ].time.iloc[0]
        swf["tBlackoutE"] = o[
            (o.eCount >= BGC * self.thBlackoutE) & (o.time >= swf["tBlackoutS"])
        ].time.iloc[0]
        swf["tRecovery"] = o[
            (o.eCount >= BGC * self.thRecovery) & (o.time >= swf["tBlackoutE"])
        ].time.iloc[0]
        return swf

    @staticmethod
    def compile(sDate, eDate, rads):
        """
        This is a static method that compiles 'Fadeout' object
        """
        return Fadeout(sDate, eDate, rads)


if __name__ == "__main__":
    # Example code to invoke Fadeout object
    fo = Fadeout.compile(
        dt.datetime(2022, 3, 31, 18, 15),
        dt.datetime(2022, 3, 31, 19, 15),
        ["fhe"],
    )
    goes, desc = fo.getGOES()
    logger.info(f"Flare info - {desc}")
    sd, desc = fo.getDARN("fhe")
    logger.info(f"SWF info - {desc}")
