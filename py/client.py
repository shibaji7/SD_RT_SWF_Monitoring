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

import socket
from loguru import logger
import json
import datetime as dt

import schedule

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
        return
    
    def run_case(self):
        """
        Main method for running main
        """
        global I
        dn = dt.datetime.strptime(self.date, "%Y-%m-%d") + dt.timedelta(seconds=I*self.scan_time)
        if not hasattr(self, "sock"): self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for r in self.rads:
            req = {
                "rad": r,
                "dn": dn.strftime("%Y-%m-%d %H:%M"),
                "scan_time": self.scan_time
            }
            self.sock.connect((self.HOST, self.PORT))
            self.sock.sendall(bytes(json.dumps(req, indent=4, sort_keys=True), "utf-8"))
            o = self.rcv_data()
            break
        I += 1
        return
    
    def rcv_data(self):
        """
        Recieve data
        """
        dat_str = ""
        dat_str = str(self.sock.recv(4096*32), "utf-8")
        o = json.loads(dat_str)
        return o
    
    @staticmethod
    def simulate(args):
        cli = Client(args)
        cli.run_case()
        return
    

def run(args):
    """
    This method hanles forking the client in
    background.
    """
    schedule.every(2).seconds.do(Client.simulate, args)
    while True: schedule.run_pending()
    return

if __name__ == "__main__":
    run(None)
    pass