#!/usr/bin/env bash

shopt -s execfail

if [ $# -ne 1 ] || [ "$1" = "-h" ] || [ "$1" == ---help ]; then
    cat <<EOD
Usage:

  ${0##*/} user@host:/opt/urchin


EOD

else
    cd "${DORCAS_HOME?ERROR - must set DORCAS_HOME}"
    rsync -av --exclude .venv ./ "${1%/}/"
fi
