#!/usr/bin/env sh

set -euo pipefail

mkdir /media/mmcblk0p2
mount /dev/mmcblk0p2 /media/mmcblk0p2
setup-alpine

if [ -e /media/mmcblk0p1/root.tar ]; then
    cd /
    tar xf /media/mmcblk0p1/root.tar
fi
lbu add /root
lbu exclude /root/.cache
lbu exclude /root/.local
sed -i '/mmcblk0p2/s/noauto,ro/rw,noatime,nodiscard,active_logs=2,alloc_mode=reuse,compress_algorithm=zstd,compress_chksum/' /etc/fstab
sed -i '/community$/s/^#//' /etc/apk/repositories
sed -i '$ { p; s|^|@testing | ; s|/alpine/.*|/alpine/edge/testing| }' /etc/apk/repositories
apk update
apk add tmux bash python3 py3-pip avahi avahi-tools mosquitto mosquitto-clients sox espeak-ng sqlite git rsync vim alsa-utils
rc-update add avahi-daemon default
sed -i '/root/s|/bin/sh|/bin/bash|' /etc/passwd
cat >/etc/profile.d/urchin.sh <<"EOD"
if [ -t 1 ]; then
    [ "$TERM" = "xterm-kitty" ] && export TERM="xterm-256color"
    export DORCAS_HOME=/opt/urchin
    export DORCAS_DATABASE="$DORCAS_HOME/db.sqlite3"
    export DORCAS_AUDIO_DIRS="$DORCAS_HOME/audio"
    export EDITOR=vim
    [ -r "$DORCAS_HOME/venv/bin/activate" ] && source "$DORCAS_HOME/venv/bin/activate"
    alias ls='ls -F --color=auto'
    alias l='ls -l'
    alias ll='l -A'
    alias vi='$EDITOR -o'
    alias g=git
fi
EOD
cat >/etc/motd <<"EOD"

  ____                             _   _          _     _
 / ___|_ __ ___  ___ _ __  _   _  | | | |_ __ ___| |__ (_)_ __
| |   | '__/ _ \/ _ \ '_ \| | | | | | | | '__/ __| '_ \| | '_ \
| |___| | |  __/  __/ |_) | |_| | | |_| | | | (__| | | | | | | |
 \____|_|  \___|\___| .__/ \__, |  \___/|_|  \___|_| |_|_|_| |_|
                    |_|    |___/

If you guessed the password or otherwise obtained access without
getting permission, well done!  :D

Feel free to have a look around, but please don't break things or 
change settings in a way that is intended to upset people. Cheek 
is encouraged, being a dick is not.

Happy hacking,
-Mouse

EOD

rm -f /etc/mosquitto/*
cat >/etc/mosquitto/mosquitto.conf <<EOD
# Setup for test mode mosquitto server
pid_file /var/run/mosquitto/mosquitto.pid
persistence false
log_dest file /var/log/mosquitto/mosquitto.log
allow_anonymous true
listener 2883
EOD
cat >/etc/conf.d/mosquitto <<EOD
start_pre() {
    checkpath -d -m 775 -o mosquitto:mosquitto /var/run/mosquitto
    checkpath -d -m 775 -o mosquitto:mosquitto /var/log/mosquitto
}
EOD
lbu commit

mkdir -p /media/mmcblk0p2/urchin
ln -s /media/mmcblk0p2/urchin /opt/urchin
lbu add /opt/urchin
lbu commit
cd /opt/urchin
echo creating $PWD/venv...
python3 -m venv venv
mkdir bin
cat >bin/activate <<"EOD"
export DORCAS_HOME="/opt/urchin"
export DORCAS_DATABASE="$DORCAS_HOME/db.sqlite3"
export DORCAS_AUDIO_DIRS="$DORCAS_HOME/audio"
source "$DORCAS_HOME/venv/bin/activate"
EOD
source bin/activate
pip install --upgrade pip
git clone https://github.com/mousefad/urchinware-2.git urchinware-2
cd urchinware-2
git checkout -b alpine-dev origin/alpine-dev
# For this to be helpful will need your github keys in the ~/.ssh dir
git remote set-url origin git@github.com:mousefad/urchinware-2.git
pip install .
