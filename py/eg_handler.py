#!/usr/bin/env python

"""eg_handler.py: module is an example server handler to send data around."""

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

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, unquote

import pydarn
from loguru import logger
import datetime as dt
import json
import numpy as np
import pandas as pd
from rad_fov import FoV

def fetch_data_by_date(dn):
    with open("config/events/20150311T16.json", "r") as f: o = json.load(f)
    idx = o["time"].index(dn)
    dat = {}
    for r in o["rad_states"].keys():
        dat[r] = o["rad_states"][r][idx]
    return dat

class InfoRequestHandler(object):
    
    def __init__(self, o, status):
        for k in o.keys():
            setattr(self, k, o[k])
        self.resp = o
        self.status = status
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
        self.resp["status"] = self.status
        self.resp["desc"] = "Radar: %s [%.2f,%.2f]"%(self.rad.upper(), self.hdw.geographic[0], self.hdw.geographic[1]) + "<br>" +\
                "Station ID: %s"%(self.hdw.stid) + "<br>" +\
                "Boresight: %.1f"%self.hdw.boresight + "<br>" +\
                "Beam Separation: %.2f"%self.hdw.beam_separation + "<br>" +\
                "Status: %s"%self.get_status_by_radpos()
        return
    
    def get_color_by_radpos(self):
        cols = dict(
            "N": {"r": 0, "g": 255, "b": 0},
            "O": {"r": 255, "g": 0, "b": 0},
            "B": {"r": 0, "g": 0, "b": 0},
            "R": {"r": 0, "g": 0, "b": 255}
        )
        return cols[self.status]
    
    def get_status_by_radpos(self):
        stats = dict(
            "N": "p-SWF",
            "O": "o-SWF",
            "B": "b-SWF",
            "R": "r-SWF"
        )
        return stats[self.status]
    
    def create_fov(self, lats, lons):
        fov = []
        for i in range(lats.shape[0]):
            fov.append([lons[i,0], lats[i,0]])
        for i in range(lats.shape[1]):
            fov.append([lons[0,i], lats[0,i]])
        for i in range(lats.shape[0]):
            fov.append([lons[i,-1], lats[i,-1]])
        for i in range(lats.shape[1]-1,0,-1):
            fov.append([lons[-1,i], lats[-1,i]])
        fov.append([lons[-1,0], lats[-1,0]])
        fov.append(fov[0])
        return fov
    
    @staticmethod
    def compiles(req, status="N"):
        rh = InfoRequestHandler(req, status)
        rh.parse_radar_info()
        return rh.resp


class TCPHandler(BaseHTTPRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """
    
    def do_GET(self):
        if (".js" in self.path) or (".ico" in self.path):
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
            query = urlparse(unquote(self.path)).query
            req = dict(q.split("=") for q in query.split("&"))
            dat = fetch_data_by_date(req["dn"])
            o = dict()
            for r in dat.keys():
                req["rad"] = r
                o[r] = InfoRequestHandler.compiles(req, dat[r])
            self.wfile.write(bytes(json.dumps(o), "utf-8"))
        return

def server(args=None):
    """
    This method hanles forking the server in
    background.
    """
    with open("config/server.json", "r") as f: o = json.load(f)
    HOST, PORT = o["HOST"], o["PORT"]
    logger.info(f"Forking Server at, {HOST}:{PORT}")
    with HTTPServer((HOST, PORT), TCPHandler) as server: server.serve_forever()
    return
    
if __name__ == "__main__":
    server()    
    pass