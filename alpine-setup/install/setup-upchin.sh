#!/usr/bin/env sh

set -euo pipefail

mkdir /media/mmcblk0p2
mount /dev/mmcblk0p2 /media/mmcblk0p2
mkdir -p /etc/ssh/authorized_keys.d
chmod 700 /etc/ssh/authorized_keys.d
cp /media/mmcblk0p1/root.pub /etc/ssh/authorized_keys.d/root
chmod 600 /etc/ssh/authorized_keys.d/root

setup-alpine

sed -i '/mmcblk0p2/s/noauto,ro/rw,noatime,nodiscard,active_logs=2,alloc_mode=reuse,compress_algorithm=zstd,compress_chksum/' /etc/fstab
sed -i '/community$/s/^#//' /etc/apk/repositories
sed -i '/^AuthorizedKeysFile/cAuthorizedKeysFile /etc/ssh/authorized_keys.d/%u .ssh/authorized_keys' /etc/ssh/sshd_config
apk update
apk add tmux bash python3 py3-pip avahi avahi-tools mosquitto mosquitto-clients sox espeak-ng sqlite git rsync vim
rc-update add avahi-daemon default
sed -i '/root/s|/bin/sh|/bin/bash|' /etc/passwd
cat >/etc/profile.d/urchin.sh <<EOD
if [ "\$TERM" = "xterm-kitty" ]; then
    export TERM="xterm-256color"
fi
alias ls='ls -F --color=auto'
alias l='ls -l'
alias ll='l -A'
alias vi='vim -o'
EOD
cat >/etc/motd <<EOD

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
lbu commit

mkdir -p /media/mmcblk0p2/urchin
ln -s /media/mmcblk0p2/urchin /opt/urchin
lbu add /opt/urchin
lbu commit
cd /opt/urchin
echo working in $PWD
echo creating venv...
python3 -m venv venv
mkdir bin
cat >bin/activate <<EOD
export DORCAS_HOME="/opt/urchin"
export DORCAS_DATABASE="\$DORCAS_HOME/db.sqlite3"
export DORCAS_AUDIO_DIRS="\$DORCAS_HOME/audio"
source "\$DORCAS_HOME/venv/bin/activate"
EOD
source bin/activate
pip install --upgrade pip
git clone https://github.com/mousefad/urchinware-2 urchinware-2
cd urchinware-2
pip install .

echo "might want to reboot now"
