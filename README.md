
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

1.  Install your OS on the device where you want to run this project. The Nottinghack Urchin
    runs on a RPi 3 running Raspbian GNU/Linux 12 (bookworm) [lite/minimal image]. Some
    packages over the base install should be installed:
    - `sox`
    - `espeak`
    - `espeak-ng`
    - `bind9-dnsutils`
    - `scanlogd` (optional - if you want to be informed of portscans)
    - `gnumeric` (optional - if you want to edit the database via the spreadsheet)
    - `mosquitto` (optional - if you want to run a local MQTT server for testing)

2.  Clone project; create a virtual env and install Python dependencies:
```
    $ git clone https://github.com/mousefad/urchinware-2.git ~/dorcas
    $ cd ~/dorcas
    $ python -m venv .
    $ pip install --upgrade pip
    $ pip install .
```

3.  Decide where you want to put the config database, and set the `DORCAS_DATABASE`
    environment variable. You'll want to add this to your shell init files too.

```
    $ export DORCAS_DATABASE=~/dorcas/db.sqlite3
```

4.  Generate a config database from the sample, `dorcas/sample/db.xml` (this file is a
    *GNUmeric* spreadsheet for easy viewing/editing). This command will generate the file
    at the path defined by `DORCAS_DATABASE`.
```
    $ python dorcas/database.py load dorcas/sample/db.xml 
```

5.  Run with `python -m dorcas --config default`


Configuration
=============

The database can store multiple configurations - one per record in the `CONFIGS` table. Only
one configuration can be active when the program is running. The configuration to use can be
selected using the `--config <id>` option when starting the program. If the `--config` option
is not used, the program will select the record where the `ID` field matches the hostname of
the machine where the program is running.

A configuration selects a record from the `BROKERS` table to decide which MQTT broker to
connect to. At time of writing broker certificates are not supported (since the one at 
Nottingham hackspace is open / unencrypted).

Other tables:

* `VOICES` - parameters for the `espeak` text-to-speech engine.
* `EFFECTS` - post-procesing of speech audio with `play` (part of SOX).
* `IGNORES` - patterns of MQTT messages to ignore.
* `SPECIAL_DAYS` - define holidays and such.
* `GREETINGS` - generic and personalized greetings.
* `MUSINGS` - responses to general MQTT events and interctions with DonationBot.

Editing Config With GNUmeric
----------------------------

The sample config database is provided as a *GNUmeric* spreadsheet in XML format, which is
convenient to read and edit using the GNUmeric Free software application. This can then be
converted to an SQLite database withthe following command (from the repo root directory):

```
$ python dorcas/database.py load path/to/spreadsheet.xml
```

The spreadsheet will be concerted into an SQLite database which will be saved to the path 
defined by the `DORCAS_DATABASE` environment variable.

Editing the spreadsheet and re-generating the SQLite database is a fairly convenient way to
work, but you do you - edit that database however you like.


Greetings
---------

Greetings are triggered when someone enters the front door of the hackspace (i.e. the door is
opened from the outside with an RFID card).

One Greeting will be selected and the Action performed. Greetings are selected from the 
`GREETINGS` table in database as follows:

1. Select where `GREETINGS.MEMBER is NULL or GREETINGS.MEMBER == <member_name>`
2. Drop records where `GREETINGS.CONDITION` is not `NULL` and the condition evaulates to `False`.
3. From the remaining records select one greeting randomly (weighted by the `WEIGHT` value).
4. Perform the ACTION (see *Actions*, below).

Musings
-------

Musings are triggered by sensations. Sensations occur when any MQTT message is seen (with the
topic and message from the MQTT message.  Some sensations are generated internally (e.g. when
Urchin starts up or shuts down, or when Urchin becomes bored). 

Every time a sensation is experienced by the Brain, records in the `MUSINGS` database table are
evaluated as followed:

1. Select all records where `MUSINGS.TOPIC` matches the `topic` of the Sensation.
2. Drop records where `MUSINGS.CONDITION` is not `NULL` and the condition evaulates to `False`.
3. From the remaining records select one musing randomly (weighted by the `WEIGHT` value).
4. Perform the ACTION (see *Actions*, below).


Actions
-------

Actions are little Python programs that are performed when Urchin wants to do something.  Only a 
small number of functions are available in actions. These functions can be used to say things
(in different voices), pause, play audio files, control the eye LEDs and spublish MQTT messages.

The can only call a very limited number of functions: `say`, `play`, `pause`, `publish`, `eyes`, 
`random`.



Acknowldgements & Copyright Notices
===================================

`dorcas/sample/audio/cuckoo_chime.wav`
--------------------------------------

Is cut from `Cuckoo Clock-Half hour.wav` by *lonemonk* --
https://freesound.org/s/88725/
License: Attribution 3.0

`dorcas/sample/audio/announcement_chimes.wav` 
---------------------------------------------

`Tannoy chime 02.wav` by *kwahmah_02* 
https://freesound.org/s/245953/
License: Attribution 3.0


TODO
====

* Systemd .service unit file.
* React to how busy the space is based on stuff like number of people in and out.
* Greetings for people with bookings on tools, e.g. "your booking on the <thing>
  starts in 25 minutes."
* Messing with the hackspace's train departures sign for fun and profit.
* In silent mode, eyes should flicker.
* Condition variable should support JSON PATH syntax for elements with a JSON value for a
  state key.
* Make state variables available in actions.
* Prevent actions from assigning to anything.
* Restore template expansion of text in speech



