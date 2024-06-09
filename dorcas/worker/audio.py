# Python built-in modules
import os
import sys
import threading
import subprocess as sp
import logging
import time

# PIP-installed modules
from singleton_decorator import singleton

# Project modules
from dorcas import database
from dorcas.worker import Worker

log = logging.getLogger(os.path.basename(sys.argv[0]))


@singleton
class Audio(Worker):
    BackgroundPlayerLimit = 10
    def __init__(self, brain, kill_on_halt=True):
        super().__init__(brain)
        self.kill_on_halt = kill_on_halt
        self.players = list()

    def run(self):
        log.debug("Audio.run BEGIN")
        while not self.halt:
            time.sleep(0.5)
            self.reap_players()
        if self.kill_on_halt:
            self.kill_players()
        else:
            self.wait_for_players()
        log.debug("Audio.run END")

    def reap_players(self):
        """reap any completed player processes"""
        keep = list()
        for path, p in self.players:
            if p and p.poll() is not None:
                log.debug(f"Audio.reap_players reaped path={path} status={p.wait()}")
            else:
                keep.append((path, p))
        self.players = keep

    def interrupt_sound(self, stop_path, instance=0):
        """Stop a specific sound from playing. If instance == 0, stop all instances, else stop specific instance #."""
        log.debug(f"Audio.interrupt_sound(stop_path={stop_path!r}, instance={instance!r}")
        keep = list()
        count = 0
        for path, p in self.players:
            kill_it = False
            if stop_path == path:
                count += 1
                if instance in (0, count) and p and p.poll() is not None:
                    kill_it = True
            if kill_it:
                p.kill()
                log.debug(f"Audio.interrupt_sound killed; status={p.wait()}")
            else:
                keep.append((path, p))
        self.players = keep

    def kill_players(self):
        log.debug(f"Audio.kill_players")
        for _, p in self.players:
            p.kill()
        self.reap_players()

    def wait_for_players(self):
        log.debug(f"Audio.wait_for_players")
        while len(self.players) > 0:
            time.sleep(0.25)
            self.reap_players()

    def play(self, path, bg=False, volume=1.0):
        log.info(f"play path={path!r} bg={bg}")
        if self.halt:
            log.debug(f"Audio.play not adding because player not-running / shutting down")
            return
        cmd = [ "play", "-q", path, "vol", str(volume) ]
        
        if not bg:
            code = sp.run(cmd).returncode
            return code == 0
        if len(self.players) >= self.BackgroundPlayerLimit:
            return False
        try:
            self.players.append((path, sp.Popen(cmd)))
        except Exception as e:
            log.debug(f"Audio.play exception={e}")
            return False
        return True

if __name__ == "__main__":
    import coloredlogs
    coloredlogs.install(level=logging.INFO)

    if len(sys.argv) != 2:
        log.error("provide path to audio file to test with as param")
        sys.exit(1)
    audio_path = sys.argv[1]

    log.info("start test")
    Audio({}, kill_on_halt=False)
    Audio().start()
    log.info("play (blocking)")
    Audio().play(audio_path)
    for _ in range(4):
        log.info("play (bg)")
        Audio().play(audio_path, bg=True)
        time.sleep(0.42)
    Audio().stop()
    Audio().wait()
    log.info("done")

