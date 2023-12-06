#!/usr/bin/env python

"""server.py: module is an UDP socket server to send data around."""

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

import datetime as dt
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote, urlparse

import numpy as np
import pandas as pd
import pydarn
from analysis import Detectors
from getfitdata import FetchData
from loguru import logger
from rad_fov import FoV


class DataMemory(object):
    def __init__(
        self,
        rads=["wal", "bks", "fhe", "fhw", "cve", "cvw", "kap", "gbr", "sas", "pgr"],
        Ts=dt.datetime(2015, 3, 11, 16),
        Te=dt.datetime(2015, 3, 11, 17),
    ):
        self.rads = rads
        self.Ts = Ts
        self.Te = Te
        self.frames = {}
        self.load_data()
        return

    def load_data(self):
        for r in self.rads:
            fd = FetchData(r, [self.Ts, self.Te])
            b, _ = fd.fetch_data()
            o = fd.convert_to_pandas(b)
            v, p, bm, gt, time = [], [], [], [], []
            if len(o) > 0:
                v, p, bm, gt, time = (
                    o.v.tolist(),
                    o.p_l.tolist(),
                    o.bmnum.tolist(),
                    o.slist.tolist(),
                    o.time.tolist(),
                )
            df = pd.DataFrame()
            df["v"], df["p"], df["bm"], df["gt"], df["time"] = v, p, bm, gt, time
            self.frames[r] = df
        return

    def get_data(self, rad, Ts, Te):
        df = self.frames[rad]
        o = df[(df.time >= Ts) & (df.time < Te)]
        return o


class DataRequestHandler(object):
    def __init__(self, o, retro_sim=True):
        for k in o.keys():
            setattr(self, k, o[k])
        self.resp = {}
        if retro_sim:
            self.simulate_retro_data()
        return

    def real_time_feed(self):
        return

    def simulate_retro_data(self):
        Ts = dt.datetime.strptime(self.dn, "%Y-%m-%dT%H:%M:%S")
        Te = Ts + dt.timedelta(seconds=float(self.scan_time))
        self.resp["start"] = self.dn
        self.resp["end"] = Te.strftime("%Y-%m-%dT%H:%M:%S")
        self.resp["rad"] = self.rad
        logger.info(f"Req- {self.rad} {Ts}-{Te}!")
        v, p, bm, gt, time = self.fetchdata(self.rad, [Ts, Te])
        rsp = {
            "velo": np.round(v, 1).tolist(),
            "powr_l": np.round(p, 1).tolist(),
            "beam": bm,
            "gate": gt,
            "ts": time,
        }
        self.resp["data"] = rsp
        return

    def fetchdata(self, r, dates):
        fd = FetchData(r, dates)
        b, _ = fd.fetch_data()
        o = fd.convert_to_pandas(b)
        v, p, bm, gt, time = [], [], [], [], []
        if len(o) > 0:
            v, p, bm, gt, time = (
                o.v.tolist(),
                o.p_l.tolist(),
                o.bmnum.tolist(),
                o.slist.tolist(),
                o.time.tolist(),
            )
            time = [t.to_pydatetime().strftime("%Y-%m-%dT%H:%M:%S") for t in time]
        return v, p, bm, gt, time

    @staticmethod
    def compiles(req):
        rh = DataRequestHandler(req)
        return rh.resp


class InfoRequestHandler(object):
    def __init__(self, o):
        for k in o.keys():
            setattr(self, k, o[k])
        self.resp = o
        return

    def parse_radar_info(self, gates=15):
        self.hdw = pydarn.read_hdw_file(self.rad)
        self.rad_fov = FoV(hdw=self.hdw, ngates=gates)
        self.resp["beams"] = np.arange(self.hdw.beams).tolist()
        self.resp["gates"] = np.arange(gates).tolist()
        self.resp["loc"] = list(self.hdw.geographic)
        self.resp["fov"] = self.create_fov(self.rad_fov.latFull, self.rad_fov.lonFull)
        self.resp["color"] = self.get_color_by_radpos()
        self.resp["alpha"] = 0.8
        self.resp["desc"] = (
            "Radar: %s [%.2f,%.2f]"
            % (self.rad.upper(), self.hdw.geographic[0], self.hdw.geographic[1])
            + "<br>"
            + "Station ID: %s" % (self.hdw.stid)
            + "<br>"
            + "Boresight: %.1f" % self.hdw.boresight
            + "<br>"
            + "Beam Separation: %.2f" % self.hdw.beam_separation
            + "<br>"
            + "Status: p-SWF"
        )
        self.resp["dn"] = "2015-03-11T16:00:00"
        return

    def get_color_by_radpos(self):
        c = {"r": 255, "g": 0, "b": 0}
        if self.rad in ["gbr", "pgr", "sas", "kap"]:
            c = {"r": 0, "g": 0, "b": 255}
        return c

    def create_fov(self, lats, lons):
        fov = []
        for i in range(lats.shape[0]):
            fov.append([lons[i, 0], lats[i, 0]])
        for i in range(lats.shape[1]):
            fov.append([lons[0, i], lats[0, i]])
        for i in range(lats.shape[0]):
            fov.append([lons[i, -1], lats[i, -1]])
        for i in range(lats.shape[1] - 1, 0, -1):
            fov.append([lons[-1, i], lats[-1, i]])
        fov.append([lons[-1, 0], lats[-1, 0]])
        fov.append(fov[0])
        return fov

    @staticmethod
    def compiles(req):
        rh = InfoRequestHandler(req)
        rh.parse_radar_info()
        return rh.resp


class PhaseRequestHandler(object):
    def __init__(self):
        self.det = Detectors()
        self.datamem = DataMemory()
        return

    def run(self, rad, dn, scan_time):
        # o = {"rad": rad, "dn": dn, "scan_time":scan_time}
        Ts = dt.datetime.strptime(dn, "%Y-%m-%dT%H:%M:%S")
        Te = Ts + dt.timedelta(seconds=float(scan_time))
        self.resp = {}
        self.det.preset(rad)
        # self.dat = DataRequestHandler.compiles(o)
        self.dat = self.datamem.get_data(rad, Ts, Te)
        self.rad = rad
        self.dn = dt.datetime.strptime(dn, "%Y-%m-%dT%H:%M:%S")
        self.parse_radar_phase()
        return self.resp

    def parse_radar_phase(self):
        # o = pd.DataFrame.from_dict(self.dat["data"])
        pe, ph = self.det.detect_SWF_phase(self.rad, self.dat, self.dn)
        self.resp["dn"] = self.dn.strftime("%Y-%m-%dT%H:%M:%S")
        self.resp["rad"] = self.rad
        self.resp["pe"] = pe
        self.resp["alpha"] = 1.0 / (1.0 + np.exp(pe - 1))
        self.resp["phase"] = ph
        return


PRH = PhaseRequestHandler()


class TCPHandler(BaseHTTPRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """

    def do_GET(self):
        if ".js" in self.path:
            self.send_response(200)
            self.send_header("content-type", "text/html")
            self.send_header("cache-control", "no-cache")
            self.send_header("access-control-allow-origin", "*")
            self.end_headers()
            path = self.path[1:]
            with open(path, "r") as f:
                self.wfile.write(bytes("\n".join(f.readlines()), "utf-8"))
        else:
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.send_header("x-content-type-options", "nosniff")
            self.send_header("cache-control", "no-cache")
            self.send_header("access-control-allow-origin", "*")
            self.end_headers()
            if ".ico" not in self.path:
                query = urlparse(unquote(self.path)).query
                req = dict(q.split("=") for q in query.split("&"))
                if "method" not in req.keys():
                    self.wfile.write(
                        bytes(json.dumps({"msg": "Method 'method' missing"}), "utf-8")
                    )
                else:
                    if req["method"] == "data":
                        ret = DataRequestHandler.compiles(req)
                        self.wfile.write(bytes(json.dumps(ret), "utf-8"))
                    elif req["method"] == "rads_info":
                        ret = InfoRequestHandler.compiles(req)
                        self.wfile.write(bytes(json.dumps(ret), "utf-8"))
                    elif req["method"] == "rads_phase":
                        ret = PRH.run(req["rad"], req["dn"], req["scan_time"])
                        self.wfile.write(bytes(json.dumps(ret), "utf-8"))
                    else:
                        self.wfile.write(
                            bytes(
                                json.dumps({"msg": "Method 'method' implemented"}),
                                "utf-8",
                            )
                        )
        return


def server(args=None):
    """
    This method hanles forking the server in
    background.
    """
    with open("config/server.json", "r") as f:
        o = json.load(f)
    HOST, PORT = o["HOST"], o["PORT"]
    logger.info(f"Forking Server at, {HOST}:{PORT}")
    with HTTPServer((HOST, PORT), TCPHandler) as server:
        server.serve_forever()
    return


if __name__ == "__main__":
    server()
