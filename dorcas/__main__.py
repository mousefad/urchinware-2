#!/usr/bin/env python

# core python modules
import os
import sys
import logging
from logging.handlers import SysLogHandler
import time
import socket
import argparse
from signal import signal, SIGTERM, SIGINT, SIGHUP, SIGUSR1, SIGUSR2

# project modules
from dorcas.brain import Brain
from dorcas.database import *

# no argument since this is the root logger
log = logging.getLogger()


def main():
    args = parse_args()
    setup_logging(args.debug, args.quiet, args.syslog)
    log.debug(f"{args}")
    log.info("START")
    DB(path=os.environ["DORCAS_DATABASE"], debug=args.debug > 1)
    if args.list_config:
        for n, rec in enumerate(DB().session.query(Config).all()):
            if args.verbose:
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
                print(f"  journald_logging    : {rec.journald_logging}")
            else:
                print(rec.id)
        sys.exit(0)

    [signal(x, sig_halt) for x in [SIGTERM, SIGHUP, SIGINT]]
    signal(SIGUSR1, sig_set_debug)
    signal(SIGUSR2, sig_clear_debug)
    if args.config is None:
        args.config = socket.gethostname()
        log.info(
            f"config selected from hostname: {args.config} ; use --config option to over-ride."
        )
    Brain(args.config, mute_mqtt=args.no_publish).run()
    log.info("END")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="This is 'dorcas' - the soul of the Creepy Urchin."
    )
    parser.add_argument(
        "--config", "-c",
        default=None,
        help=("specify the configuration to use (defined in database/config table). "
              "If none is specified, the hostname will be used as the config name")
    )
    parser.add_argument(
        "--debug", "-D",
        action='count', 
        default=0,
        help="produce more diagnostic output"
    )
    parser.add_argument(
        "--list-config", "-l",
        action="store_true",
        help="list available configs and exit"
    )
    parser.add_argument(
        "--no-publish", "-n",
        action="store_true",
        help="do not publish messages to MQTT"
    )
    parser.add_argument(
        "--quiet", "-q",
        action='count', 
        default=0,
        help="produce less diagnostic output"
    )
    parser.add_argument(
        "--syslog", "-s",
        action="store_true",
        help="log to syslog instead of stderr"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="be more verbose"
    )

    return parser.parse_args()


def setup_logging(debug, quiet, syslog):
    log.addHandler(get_log_handler(syslog))
    log.setLevel(get_log_level(debug, quiet))


def get_log_handler(syslog):
    handler = SysLogHandler("/dev/log") if syslog else logging.StreamHandler()
    if syslog:
        handler = SysLogHandler("/dev/log")
        fmt = f"{get_log_program()}[{os.getpid()}]: %(message)s"
    else:
        handler = logging.StreamHandler()
        fmt = f"%(asctime)s {get_log_program()}[{os.getpid()}]: %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
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
