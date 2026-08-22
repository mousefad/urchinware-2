#!/usr/bin/env python

# core python modules
import os
import sys
import logging
import time
import socket
from signal import signal, SIGTERM, SIGINT, SIGHUP, SIGUSR1, SIGUSR2

# pip-installed modules
import click

# project modules
from dorcas.brain import Brain
from dorcas.database import *

# no argument since this is the root logger
log = logging.getLogger()


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
@click.option("--syslog", "-s", is_flag=True, help="Log to syslog instead of stderr.")
def main(config, debug, list_config, log_path, no_publish, quiet, verbose, syslog):
    setup_logging(debug, quiet, syslog)
    log.info("START")
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
    signal(SIGUSR1, sig_set_debug)
    signal(SIGUSR2, sig_clear_debug)
    if config is None:
        config = socket.gethostname()
        log.info(
            f"config selected from hostname: {config} ; use --config option to over-ride."
        )
    Brain(config, mute_mqtt=no_publish).run()
    log.info("END")


def setup_logging(debug, quiet, syslog):
    log.addHandler(get_log_handler(syslog))
    log.setLevel(get_log_level(debug, quiet))


def get_log_handler(syslog):
    handler = SysLogHandler("/dev/log") if syslog else logging.StreamHandler()
    formatter = logging.Formatter(f"{get_log_program()}[{os.getpid()}]: %(message)s")
    handler.setFormatter(formatter)
    return handler


def get_log_program():
    if len(sys.argv) > 0:
        return os.path.basename(sys.argv[0])
    else:
        return "[no-argv]"


def get_log_level(debug, quiet):
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


def sig_set_debug(sig, frame):
    log.info(f"received signal {sig!r}; setting debug")
    log.setLevel(logging.DEBUG)


def sig_clear_debug(sig, frame):
    log.info(f"received signal {sig!r}; clearing debug")
    log.setLevel(logging.INFO)


if __name__ == "__main__":
    main()
