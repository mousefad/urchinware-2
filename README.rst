In Acts 8 verses 36-39, some woman called Dorcas falls ill and dies, and
then rises again. No worshippers for her, just more thankless life.
Thanks God! Anyhow, Dorcas is the name of the second incarnation of this
stupid talking Creepy Urchin thing at Nottingham Hackspace.

Some time in 2024 it fell ill and died (just like Dorcas - it must be
prophesy!). Probably what happened is that it was unplugged or there was
a power outage, and then either nobody could figure out how to (or
didn’t want to) turn on the crotch-speaker.

Subsequently, the speaker was removed and various random wires and
crappy speakers were shoved into the chest cavity in the vain hope it
would start working again. The SD card also had bad sectors and the Pi
was starting to boot unreliably. The LCD screen had long since been
removed by some fiendish parts pilferer.

Poor little Dorcas needs a refit, so here we are.

Version 2.0 of UrchinWare(tm) has some minor changes:

Full re-write - the old code was horrible (Jeeer!):

-  Putting data in Sqlite3 rather than hard-coding everything (wowsers!)
-  Splitting modules into separate files (zammo!)
-  Stripping out the display parts since there is no display (hurrah!)
-  Simpler dependencies (not more Qt or need for a display server -
   huzzah!)
-  New features! (zaaaaap!)


Building & Running
==================

1. Install your OS on the device where you want to run this project. The
   Nottinghack Urchin runs on a RPi 3 running Raspbian GNU/Linux 12
   (bookworm) [lite/minimal image]. Some packages over the base install
   should be installed:

   -  ``sox``
   -  ``espeak``
   -  ``espeak-ng``
   -  ``bind9-dnsutils``
   -  ``sqlite3``
   -  ``pigpiod``
   -  ``scanlogd`` (optional - if you want to be informed of portscans)
   -  ``gnumeric`` (optional - if you want to edit the database via the
      spreadsheet)
   -  ``mosquitto`` (optional - if you want to run a local MQTT server
      for testing)

   Run: `sudo systemctl enable pigpiod ; sudo systemctl start pigpiod`

2. Clone project; create a virtual env and install Python dependencies:

::

       $ git clone https://github.com/mousefad/urchinware-2.git ~/dorcas
       $ cd ~/dorcas
       $ python -m venv .
       $ . bin/activate
       $ pip install --upgrade pip
       $ pip install .

3. Set a couple of environment variables so the program can find
   relevant files:

::

       $ export DORCAS_DATABASE=~/dorcas/db.sqlite3
       $ export DORCAS_AUDIO_DIRS=~/dorcas/audio

4. Generate a config database from the sample, ``dorcas/sample/db.xml``
   (this file is a *GNUmeric* spreadsheet for easy viewing/editing).
   This command will generate the file at the path defined by
   ``DORCAS_DATABASE``.

::

       $ python dorcas/database.py load dorcas/sample/db.xml 

5. Run with ``python -m dorcas --config default``


Configuration
=============

The database can store multiple configurations - one per record in the
``CONFIGS`` table. Only one configuration can be active when the program
is running. The configuration to use can be selected using the
``--config <id>`` option when starting the program. If the ``--config``
option is not used, the program will select the record where the ``ID``
field matches the hostname of the machine where the program is running.

A configuration selects a record from the ``BROKERS`` table to decide
which MQTT broker to connect to. At time of writing broker certificates
are not supported (since the one at Nottingham hackspace is open /
unencrypted).

Other tables:

-  ``VOICES`` - parameters for the ``espeak`` text-to-speech engine.
-  ``EFFECTS`` - post-procesing of speech audio with ``play`` (part of
   SOX).
-  ``IGNORES`` - patterns of MQTT messages to ignore.
-  ``SPECIAL_DAYS`` - define holidays and such.
-  ``GREETINGS`` - generic and personalized greetings.
-  ``MUSINGS`` - responses to general MQTT events and interctions with
   DonationBot.

Editing Config With GNUmeric
----------------------------

The sample config database is provided as a *GNUmeric* spreadsheet in
XML format, which is convenient to read and edit using the GNUmeric Free
software application. This can then be converted to an SQLite database
withthe following command (from the repo root directory):

::

   $ python dorcas/database.py load path/to/spreadsheet.xml

The spreadsheet will be converted into an SQLite database which will be
saved to the path defined by the ``DORCAS_DATABASE`` environment
variable.

Editing the spreadsheet and re-generating the SQLite database is a
fairly convenient way to work, but you do you - edit that database
however you like.

Greetings
---------

Greetings are triggered when someone enters the front door of the
hackspace (i.e. the door is opened from the outside with an RFID card).

One Greeting will be selected and the Action performed. Greetings are
selected from the ``GREETINGS`` table in the database as follows:

1. Select where
   ``GREETINGS.MEMBER is NULL or GREETINGS.MEMBER == <member_name>``
2. Drop records where ``GREETINGS.CONDITION`` is not ``NULL`` or the
   condition evaluates to ``False`` (see *Conditions*, below).
3. From the remaining records select one greeting randomly (weighted by
   the ``WEIGHT`` value).
4. Perform the ACTION (see *Actions*, below).

Musings
-------

Musings are triggered by sensations. Sensations occur when any MQTT
message is seen (with the topic and message from the MQTT message. Some
sensations are generated internally (e.g. when Urchin starts up or shuts
down, or when Urchin becomes bored).

Every time a sensation is experienced by the Brain, records in the
``MUSINGS`` database table are evaluated as followed:

1. Select all records where ``MUSINGS.TOPIC`` matches the ``topic`` of
   the Sensation.
2. Drop records where ``MUSINGS.CONDITION`` is not ``NULL`` or the
   condition evaulates to ``False`` (see *Conditions*, below).
3. From the remaining records select one musing randomly (weighted by
   the ``WEIGHT`` value).
4. Perform the ACTION (see *Actions*, below).

Conditions
----------

Greetings and Musings are filtered by Conditions. A condition is a
Python expression that evaluates to True or False. Conditions are
evaulated with a limited execution context with access only to Brain
State Variables and the following functions:

-  ``random()`` Call Python ``random.random()``.

-  ``random_choice(list)`` Call Python ``random.choice(list)``

-  ``random_int(a, b)`` Call Python ``random.randint(a, b)``.

Actions
-------

Actions are small Python programs that are performed as a consequency of
a Greeting or Musing. Actions execute in a limited execution context
with access only to Brain State Variables and the following functions:

-  ``eyes(final, duration=0.5)`` Fade Urchin’s eyes to intensity level
   ``final`` (value between 0.0 and 1.0), taking ``duration`` number of
   seconds to do so. This operation is non-blocking.

-  ``log(message)`` Print ``message`` to diagnostic output with level
   ``logging.INFO``.

-  ``pause(seconds)`` Block execution of the action for the specified
   number of seconds.

-  ``play(file_id, bg=True, volume=1.0)`` Play an audio file, found
   under any of the directories defined in the environment variable
   ``DORCAS_AUDIO_DIRS`` (separated by the ``:`` character). ``volume``
   is a floating point value between 0.0 and 1.0. The ``bg`` value
   determines if the play operation blocks or if playing of the audio
   file is performed in the background.

-  ``publish(topic, message)`` Publish a message over MQTT with the
   specified topic and message payload.

-  ``random()`` Call Python ``random.random()``.

-  ``random_choice(list)`` Call Python ``random.choice(list)``

-  ``random_int(a, b)`` Call Python ``random.randint(a, b)``.

-  ``say(text, voice="default")`` cause Urchin to say ``text`` using
   voice from ``VOICES`` table where ``ID`` == ``voice``.

Brain State Variables
---------------------

Dorcas’ mind holds some state that is visible to most classes, and can
be used in Actions and Conditions.


Acknowldgements & Copyright Notices
===================================

``dorcas/sample/audio/cuckoo_chime.wav``
----------------------------------------

Is cut from ``Cuckoo Clock-Half hour.wav`` by *lonemonk* –
https://freesound.org/s/88725/ License: Attribution 3.0

``dorcas/sample/audio/announcement_chimes.wav``
-----------------------------------------------

``Tannoy chime 02.wav`` by *kwahmah_02* https://freesound.org/s/245953/
License: Attribution 3.0


TODO
====

-  Systemd .service unit file.
-  React to how busy the space is based on stuff like number of people
   in and out.
-  Greetings for people with bookings on tools, e.g. “your booking on
   the starts in 25 minutes.”
-  Have Thespian wait for say() and play() to finish before ending.

   -  add wait() function maybe, and have an implicit call to it at the
      end of each performance?
