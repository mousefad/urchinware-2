# Python built-in modules
import os
import sys
import threading
import subprocess as sp
import logging
import time
import glob
import cachetools.func
import pathlib

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
        log.debug(
            f"Audio.interrupt_sound(stop_path={stop_path!r}, instance={instance!r}"
        )
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

    def play(self, id, bg=True, volume=1.0):
        """Play an audio file by id

        Arguments:
        id - the file name without the preceding audio dir e.g. "creepy/toll.mp3"
        bg - if True, audio player is spawned and put in background, else play() will block
        volume - between 0.0 and 1.0
        """
        log.info(f"play id={id!r} bg={bg} volime={volume!r}")
        if self.halt:
            log.debug(
                f"Audio.play not adding because player not-running / shutting down"
            )
            return
        path = self.get_path(id)
        log.debug(f"play path={path!r}")
        cmd = ["play", "-q", path, "vol", str(volume)]
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

    def get_path(self, id):
        """Get the full path of an audio file from the id

        Arguments:
        id - the file name without the preceding audio dir e.g. "creepy/toll.mp3"
        """
        for d in self.search_paths():
            path = os.path.join(d, id)
            if os.path.exists(path):
                return path
        raise RuntimeError(f"could not locate audio file with id={id}")

    def find(self, searchstr="", subdir=""):
        """Get a list of audio file ids from a subdir of audio search paths that contain searchstr in the basename.

        searchstr - value to be searched for in file basenames.
        subdir - sub-directory to search in within each path in DORCAS_AUDIO_DIRS.
        """
        # don't want to use a set because we'll lose order, so we'll list and test
        # before adding.
        ids = list()

        def already_have(basename):
            return sum([1 for x in ids if os.path.basename(x) == basename]) > 0

        def add_id(id):
            if not already_have(id):
                ids.append(id)

        for d in [os.path.join(x, subdir) for x in self.search_paths()]:
            plp = pathlib.Path(d)
            for fullpath in [
                str(p) for p in filter(lambda x: x.is_file(), plp.glob("*"))
            ]:
                idx = len(d) - len(subdir)
                id = fullpath[idx:]
                bn = os.path.basename(id)
                if searchstr in bn:
                    add_id(id)
        return ids

    def all(self):
        ids = set()
        for d in self.subdirs():
            for id in self.find(subdir=d):
                ids.add(os.path.join(d,id))
        return sorted(list(ids))

    def subdirs(self, searchstr=""):
        """Get a listof audio file sub-directories (without the DORCAS_AUDIO_DIR prefixes)"""

        def str_eq(s1, s2):
            if case_sensitive:
                return s1 == s2
            else:
                return s1.lower() == s2.lower()

        dirs = set([""])
        for d in self.search_paths():
            plp = pathlib.Path(d)
            start_idx = len(d) + 1
            for pp in [
                str(p)[start_idx:] for p in filter(lambda x: x.is_dir(), plp.rglob("*"))
            ]:
                if searchstr in pp:
                    dirs.add(str(pp))
        return dirs

    def search_paths(self):
        """Get list of dirs to search for audio files from DORCAS_AUDIO_DIRS and sample audio dir."""
        paths = list()

        def add_path(p):
            if p not in paths:
                paths.append(p)

        try:
            [add_path(p) for p in os.environ["DORCAS_AUDIO_DIRS"].split(":")]
        except:
            pass
        add_path(
            os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "sample", "audio")
            )
        )
        return paths


if __name__ == "__main__":
    import coloredlogs
    import random
    coloredlogs.install(level=logging.INFO)
    log.info("start test")
    dummy_brain = {}
    Audio(dummy_brain, kill_on_halt=False)
    Audio().start()
    # list files in each subdir category
    for subdir in Audio().subdirs():
        log.info(f"audio files in subdir {subdir!r}:")
        for id in Audio().find(subdir=subdir):
            log.info(f" {id}")
    log.info("play (blocking)")
    for _ in range(2):
        Audio().play("cuckoo_chime.mp3", bg=False)
        time.sleep(0.75)
    log.info("play (non-blocking)")
    for _ in range(2):
        Audio().play("cuckoo_chime.mp3", bg=True)
        time.sleep(0.75)
    Audio().stop()
    Audio().wait()
    log.info("done")
