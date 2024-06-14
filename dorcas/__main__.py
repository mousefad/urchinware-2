#!/usr/bin/env python

# core python modules
import os
import sys
import logging
import time
import socket
from signal import signal, SIGTERM, SIGINT, SIGHUP

# pip-installed modules
import click
import coloredlogs

# project modules
from dorcas.brain import Brain
from dorcas.database import *

log = logging.getLogger(__name__)


@click.command()
@click.option(
    "--config",
    "-c",
    type=str,
    default=None,
    help="Specify the configuration to use (defined in database/config table). "
    "If none is specified, the hostname will be used as the config name.",
)
@click.option("--debug", "-D", count=True, help="Produce more diagnostic output.")
@click.option(
    "--list-config", "-l", is_flag=True, help="List available configs and exit"
)
@click.option(
    "--log-path", "-L", type=str, help="Log to specified file instead of stderr."
)
@click.option(
    "--no-publish", "-p", is_flag=True, help="Do not publish activity on MQTT"
)
@click.option("--quiet", "-q", count=True, help="Produce less diagnostic output.")
@click.option("--verbose", "-v", is_flag=True, help="Be more verbose.")
def main(config, debug, list_config, log_path, no_publish, quiet, verbose):
    # simpler, more compact logging
    fmt = "%(asctime)s %(message)s"
    if log_path is not None:
        log_path = open(log_path, "a", encoding="utf8", errors="replace")
    coloredlogs.install(level=get_debug_level(debug, quiet), stream=log_path, fmt=fmt)
    log.info(f"START")
    DB(path=os.environ["DORCAS_DATABASE"], debug=debug > 1)

    if list_config:
        for n, rec in enumerate(DB().session.query(Config).all()):
            if verbose:
                if n > 0:
                    print("")
                print(f"Config ID             : {rec.id}")
                print(f"  time_interval       : {rec.time_interval}")
                print(f"  journal_interval    : {rec.journal_interval}")
                print(f"  boredom_minimum     : {rec.boredom_minimum}")
                print(f"  boredom_amount      : {rec.boredom_amount}")
                print(f"  time_interval       : {rec.time_interval}")
                print(f"  broker_id           : {rec.broker_id}")
                print(f"  voice_id            : {rec.voice.id}")
            else:
                print(rec.id)
        sys.exit(0)

    [signal(x, sig_halt) for x in [SIGTERM, SIGHUP, SIGINT]]
    if config is None:
        config = socket.gethostname()
        log.info(
            f"config selected from hostname: {config} ; use --config option to over-ride."
        )
    Brain(config, mute_mqtt=no_publish).run()
    log.info("END")


def get_debug_level(debug, quiet):
    balance = debug - quiet
    if balance == 0:
        return logging.INFO
    elif balance > 0:
        return logging.DEBUG + 1 - balance
    else:
        return logging.WARNING + balance


def sig_halt(sig, frame):
    if Brain().halt:
        log.info(f"received signal {sig!r}; already halting; forcing exit")
        sys.exit(1)
    log.info(f"received signal {sig!r}; requesting halt")
    Brain().stop()


if __name__ == "__main__":
    main()
