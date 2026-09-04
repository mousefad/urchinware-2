This directory includes files used for the quick creation of an Alpine Linux SD card for use
with Urchinware-2 (project Dorcas) for the Nottinghack Creepy Urchin.

Use `make_partition.sh` and `copy_boot.sh` to create SD media.


Step 1: Create SD card
----------------------

1. Get a Raspberry Pi 3B or better and an SD card >= 4 GiB in size (as fast as possible)
2. Download the latest Raspberry Pi Alpine Linux release. Choose the `.tar.gz` not the `.img`
   - For the Raspberry Pi 3 you will probably want to use the *armv7* architecture since it 
     is more memory-efficient
   - For later versions of the Raspberry Pi, choose *aarm64*
3. Rename or link to the downloaded Alpine file, naming the link `alpine.tar.gz`
4. Copy/prepare `root/.ssh`, `root/.config` etc. to be installed in `/root` dir of the Pi
5. Copy `db.sqlite3` and `audio` from production Urchin to `app/`
6. Insert SD card
7. Run `sudo ./setup_sd_card.sh` to prepare the SD card


Step 2: Configure & Install Alpine / Urchinware-2
-------------------------------------------------

1. Boot the Pi with the new SD card, monitor and keyboard attached
2. Login as `root`
3. Run `/media/mmcblk0p1/setup.sh`. This script will call `setup-alpine` which is an 
   interactive process. Setup keyboard:
   - keyboard
   - network
   - ntp=busybox
   - ssh=openssh
   - disk mode: choose 'n' to the first question, then default for next 2 (`mmcblk0p2` 
     for the location of the APK cache)

Urchinware will be put in `/opt/urchin` which will be a symlink to `/media/mmcblk0p2/app`
where persistent app data is stored.


Links
-----

* [About the Creepy Urchin](https://wiki.nottinghack.org.uk/index.php?title=Creepy_Urchin)
* [Urchinware-2 Git Repo](https://github.com/mousefad/urchinware-2)
* [Alpine Linux Downloads](https://alpinelinux.org/downloads/)
* [Alpine Linux install on Raspberry Pi](https://wiki.alpinelinux.org/wiki/Raspberry_Pi)


