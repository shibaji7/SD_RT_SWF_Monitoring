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

import socketserver
from loguru import logger
import datetime as dt
import json
import numpy as np

from getfitdata import FetchData 

class RequestHandler(object):
    
    def __init__(self, o, retro_sim=True):
        for k in o.keys():
            setattr(self, k, o[k])
        self.resp = {}
        if retro_sim: self.simulate_retro_data()
        return
    
    def simulate_retro_data(self):
        Ts = dt.datetime.strptime(self.dn, "%Y-%m-%d %H:%M")
        Te = Ts + dt.timedelta(seconds=self.scan_time)
        self.resp["start"] = self.dn
        self.resp["end"] = Te.strftime("%Y-%m-%d %H:%M")
        logger.info(f"Req- {self.rad} {Ts}-{Te}!")
        v, p, bm, gt, time = self.fetchdata(self.rad, [Ts, Te])
        rsp = {
            "rad": self.rad,
            "velo": v,
            "powr_l": p,
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
            v, p, bm, gt, time = np.round(o.v, 1).tolist(), np.round(o.p_l, 1).tolist(),\
                o.bmnum.tolist(), o.slist.tolist(), o.time.tolist()
            time = [t.to_pydatetime().strftime("%Y-%m-%d %H:%M:%S") for t in time]
        return v, p, bm, gt, time
    
    @staticmethod
    def compiles(req):
        rh = RequestHandler(req)
        return rh.resp

class TCPHandler(socketserver.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """
    
    def handle(self):
        req = self.request.recv(1024*4).strip()
        logger.info("{} wrote!".format(self.client_address[0]))
        req = json.loads(req)
        ret = RequestHandler.compiles(req)
        self.request.sendall(bytes(json.dumps(ret), "utf-8"))
        return
    
def server(args=None):
    """
    This method hanles forking the server in
    background.
    """    
    with open("config/server.json", "r") as f: o = json.load(f)
    HOST, PORT = o["HOST"], o["PORT"]
    logger.info(f"Forking Server at, {HOST}:{PORT}")
    with socketserver.TCPServer((HOST, PORT), TCPHandler) as server:
        server.serve_forever()
    return
    
if __name__ == "__main__":
    server()    
    pass