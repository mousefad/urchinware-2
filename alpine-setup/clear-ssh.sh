#!/usr/bin/env bash

sed -i -e '/irchin/d' -e '/192\.168\.1\.151/d' -e '/10\.42\.0\.169/d' ~/.ssh/known_hosts
