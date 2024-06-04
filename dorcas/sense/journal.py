# Built-in python modules
import os
import sys
import logging
import re
import time
import json
import select
import subprocess as sp

# Project modules
from dorcas.sensation import Sensation
from dorcas.sense import ThreadedHalterSense


log = logging.getLogger(os.path.basename(sys.argv[0]))


def ip_to_hostname(ip):
    try:
        p = sp.run(["dig", "-x", str(ip)], capture_output=True)
        hostname = [x for x in p.stdout.decode().splitlines() if re.match(r"[0-9]", x)][0].split()[-1].rstrip(".")
        assert len(hostname) > 0
        return hostname
    except:
        return "unknown"


class Journal(ThreadedHalterSense):
    """The Journal Sense monitors the system journal (log), creating events when it sees certain log messages"""
    Matchers = [
        (
            re.compile(r"Accepted (\S+) for (\S+) from (\S+) "), 
            "os/login", 
            lambda m: json.dumps({"method": m.group(1), "user": m.group(2), "from": m.group(3), "from_hostname": ip_to_hostname(m.group(3))})
        ),
        (   
            re.compile(r"scanlogd[\d+]: (\S+) to (\S+) "),
            "os/portscan",
            lambda m: json.dumps({"to": m.group(2), "from": m.group(1), "from_hostname": ip_to_hostname(m.group(1))})
        ),
    ]

    def __init__(self, brain):
        super().__init__(brain)
        self.cmd = ["journalctl", "-f", "--since", "now"]
        self.p = None
        self.poll = None
        log.info(f"self.brain.config: {self.brain.config!r}")
        self.interval = self.brain.config.journal_interval

    def start_subprocess(self):
        if self.p:
            log.warning("Journal.start_subprocess: already present")
            return False
        self.p = sp.Popen(
                self.cmd, 
                stdout=sp.PIPE, 
                stderr=sp.PIPE, 
                bufsize=0)
        self.poll = select.poll()
        self.poll.register(self.p.stdout)
        return True

    def stop_subprocess(self):
        if self.p:
            self.p.terminate()
            log.debug("Journal.stop_subprocess: waiting for subprocess")
            status = self.p.wait()
            log.debug(f"Journal.stop_subprocess: subprocess ended with {status}")
            self.p = None
            self.poll = None

    def run(self):
        log.debug("Journal.run")
        self.start_subprocess()
        while not self.halt:
            while self.poll.poll(1) and not self.halt:
                line = self.p.stdout.readline()
                if len(line) > 0:
                    self.process_log_entry(line.decode())
            time.sleep(self.interval) 
        log.debug("Journal.main loop ended")
        self.stop_subprocess()
        log.debug("Journal.run END")

    def process_log_entry(self, line):
        for rx, topic, fn in Journal.Matchers:
            m = rx.search(line)
            if m:
                log.debug(f"got a match topic={topic} {line!r}")
                self.experience(Sensation(topic, fn(m)))
                return
    

