#!/usr/bin/env python

"""client.py: module is a client side handeing the data request for processing."""

__author__ = "Chakraborty, S."
__copyright__ = "Copyright 2022, SuperDARN@VT"
__credits__ = []
__license__ = "MIT"
__version__ = "1.0."
__maintainer__ = "Chakraborty, S."
__email__ = "shibaji7@vt.edu"
__status__ = "Research"

import http.client
import urllib.parse
from loguru import logger
import json
import datetime as dt
import pandas as pd
import numpy as np

import schedule

from analysis import PhaseDetector

I = 0

class Client(object):
    """
    This is client side that runs in the background 
    and continuously (1-2 mins) based on radar type.
    """
    
    def __init__(self, args):
        logger.info(f"Restart client!")
        with open("config/server.json", "r") as f: 
            o = json.load(f)
            for k in o.keys():
                setattr(self, k, o[k])
        logger.info(f"Invoking Sever {self.HOST}:{self.PORT}")
        self.predictors = {}
        self.phases = {}
        self.echoes_dev = {}
        return
    
    def preset(self, r):
        if r not in self.predictors.keys(): self.predictors[r] = PhaseDetector(r)
        if r not in self.phases.keys(): self.phases[r] = "p-SWF"
        if r not in self.echoes_dev.keys(): self.echoes_dev[r] = 0.
        return
    
    def connect(self):
        """
        Connect to server socket
        """
        self.conn = http.client.HTTPConnection(self.HOST, self.PORT, timeout=10)
        return
    
    def close(self):
        """
        Close server socket connection
        """
        self.conn.close()
        del self.conn
        return
    
    def run_case(self):
        """
        Main method for running main
        """
        global I
        self.dn = dt.datetime.strptime(self.date, "%Y-%m-%d") + dt.timedelta(seconds=I*self.scan_time) +\
                dt.timedelta(hours=self.base_hours)
        if not hasattr(self, "conn"): self.connect()            
        for r in self.rads:
            self.preset(r)
            uri = "/?rad={rad}&dn={dn}&scan_time={scan_time}&method=data".format(rad=r, 
                                                                                 dn=self.dn.strftime("%Y-%m-%dT%H:%M:%S"),
                                                                                 scan_time=self.scan_time)
            self.conn.request("GET", urllib.parse.quote_plus(uri))
            o = self.rcv_data()
            ph = self.detect_SWF_phase(r, o)
            break
        I += 1
        return
    
    def rcv_data(self):
        """
        Recieve data
        """
        resp = self.conn.getresponse()
        dat_str = str(resp.read(4096*32), "utf-8")
        x = json.loads(dat_str)
        o = pd.DataFrame.from_dict(x["data"])
        o["start"], o["end"], o["rad"] = x["start"], x["end"], x["rad"]
        return o
    
    def get_echoes_counts(self, o):
        d = pd.DataFrame()
        d["size"] = [len(o)] 
        return d
    
    def detect_SWF_phase(self, r, o):
        d = self.get_echoes_counts(o)
        opd = self.predictors[r]
        p = np.array(opd.forecast(), dtype=int)
        pe = abs(d["size"].tolist()[0] - p.tolist()[0])/d["size"].tolist()[0]
        logger.info(f"Forecast : Observations, {p.tolist()[0]}:{d['size'].tolist()[0]}")
        logger.info(f"PE({pe}) at {self.dn}")
        self.echoes_dev[r] = pe
        if pe <= 0.3: opd.update_AR(d)
        if (pe > 0.3 and pe <= 0.6) and self.phases[r]=="p-SWF": self.phases[r] = "o-SWF"
        if pe > 0.6 and self.phases[r] in ["o-SWF", "p-SWF"]: self.phases[r] = "b-SWF"
        if (pe > 0.3 and pe <= 0.6) and self.phases[r] in ["o-SWF", "b-SWF"]: self.phases[r] = "r-SWF"
        if pe <= 0.1 and self.phases[r] in ["b-SWF", "r-SWF", "o-SWF"]: self.phases[r] = "p-SWF"
        self.print_summary()
        return
    
    def print_summary(self):
        for r in self.phases.keys():
            logger.info(f"Infered procs {self.dn}: {r.upper()}({self.phases[r]}, {self.echoes_dev[r]})")
        return
    

def run(args):
    """
    This method hanles forking the client in
    background.
    """
    cli = Client(args)
    schedule.every(2).seconds.do(cli.run_case)
    while True: schedule.run_pending()
    return

if __name__ == "__main__":
    run(None)
    pass