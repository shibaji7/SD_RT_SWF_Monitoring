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

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, unquote

from loguru import logger
import datetime as dt
import json
import numpy as np

from getfitdata import FetchData 

class DataRequestHandler(object):
    
    def __init__(self, o, retro_sim=True):
        for k in o.keys():
            setattr(self, k, o[k])
        self.resp = {}
        if retro_sim: self.simulate_retro_data()
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
            "ts": time
        }
        self.resp["data"] = rsp
        return
    
    def fetchdata(self, r, dates):
        fd = FetchData(r, dates)
        b, _ = fd.fetch_data()
        o = fd.convert_to_pandas(b)
        v, p, bm, gt, time = [], [], [], [], []
        if len(o) > 0: 
            v, p, bm, gt, time = o.v.tolist(), o.p_l.tolist(),\
                o.bmnum.tolist(), o.slist.tolist(), o.time.tolist()
            time = [t.to_pydatetime().strftime("%Y-%m-%dT%H:%M:%S") for t in time]
        return v, p, bm, gt, time
    
    @staticmethod
    def compiles(req):
        rh = DataRequestHandler(req)
        return rh.resp

class InfoRequestHandler(object):
    
    def __init__(self, o, retro_sim=True):
        for k in o.keys():
            setattr(self, k, o[k])
        self.resp = {}
        return
    
    @staticmethod
    def compiles(req):
        rh = InfoRequestHandler(req)
        return rh.resp
    

class TCPHandler(BaseHTTPRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """
    
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        query = urlparse(unquote(self.path)).query
        req = dict(q.split("=") for q in query.split("&"))
        if "method" not in req.keys(): self.wfile.write(bytes(json.dumps({"msg": "Method 'method' missing"}), "utf-8"))
        else:
            if req["method"] == "data":
                ret = DataRequestHandler.compiles(req)
                self.wfile.write(bytes(json.dumps(ret), "utf-8"))
            elif req["method"] == "rad_infos":
                ret = InfoRequestHandler.compiles(req)
                self.wfile.write(bytes(json.dumps(ret), "utf-8"))
            else: self.wfile.write(bytes(json.dumps({"msg": "Method 'method' implemented"}), "utf-8"))
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