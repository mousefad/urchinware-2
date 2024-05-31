
In Acts 8 verses 36-39, some woman called Dorcas falls ill and dies, and then rises again.
No worshippers for her, just more thankless life. Thanks God! Anyhow, Dorcas is the name
of the second incarnation of this stupid talking Urchin thing at Nottingham Hackspace.

Some time in 2024 it fell ill and died (just like Dorcas - it must be prophesy!). Probably
what happened is that it was unplugged or there was a power outage, and then either nobody
could figure out how to (or didn't want to) turn on the crotch-speaker.

Subsequently, the speaker was removed and various random wires and crappy speakers were
shoved into the chest cavity in the vain hope it would start working again. The SD card
also had bad sectors and the Pi was starting to boot unreliably. The LCD screen had long
since been removed by some fiendish parts pilferer.

Poor little Dorcas needs a refit, so here we are.

Version 2.0 of UrchinWare(tm) has some minor changes:

Full re-write - the old code was horrible (Jeeer!):

* Putting data in Sqlite3 rather than hard-coding everything (wowsers!)
* Splitting modules into separate files (zammo!)
* Stripping out the display parts since there is no display (hurrah!)
* Simpler dependencies (not more Qt or need for a display server - huzzah!)
* New features! (zaaaaap!)


Building & Running
==================

1. Clone this repo to a Raspberry Pi or Linux machine.  As of writing, Urchin is running
   with a RPi 3 running Raspbian GNU/Linux 12 (bookworm) [lite/minimal image]. RPi packages
   required (over Raspian Lite installation):
   - `sox` .
   - `espeak`.
   - `espeak-ng`.
   - `scanlogd`.
   - `gnumeric`
   - `bind9-dnsutils`
   - `mosquitto` (if you want to run locally with a test MQTT server)

2. cd into the cloned dir and do: `python -m venv $PWD`. 

3. From the cloned dir: `export DORCAS_HOME=$PWD ; . ./project.env`

4. Install dependencies with PIP:
   `sed 1,2d pip-packages.txt | awk '{ print $1 }' | xargs pip install`

5. Create a new config `db_new`.
   Use gnumeric to edit `private/db.xml`:
   - In `CONFIGS` set ID to your hostname, so you don't have to specify with `--config`.
   - In `BROKER` set the host to the host of the MQTT server.
   - Add some entries in `GREETINGS` and `MUSINGS`.
   - Save spreadsheet & update the SQLite3 database with `db_update`

6. Run `./dorcas`.  



TODO
====

* Support playing background audio files.
* Re-organize project to be more Pythonic in terms for distribution and packaging.
* Systemd .service unit file.
* React to how busy the space is based on stuff like number of people in and out.
* Greetings for people with bookings on tools, e.g. "your booking on the <thing>
  starts in 25 minutes."


