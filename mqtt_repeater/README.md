This directory contains a simple MQTT repeater. 

The idea is that while testing, we want to get a feed of live messages from the real Nottinghack
MQTT broker, but we don't want to publish messages there since it would mess up the "production"
Urchin.

The repeater works by subscribing to all messages from the "real" MQTT broker, and re-publishing 
each to a second MQTT broker running locally on the test host (port 2883). Urchin config on the
test host can be set up to connect to the second MQTT server and is free to publish there without 
affecting the production broker.


Running the repeater
--------------------

1. Setup a local Mosquitto service to listen on port 2883. On an Alpine Linux installation
   set up with the `alpine-setup` method in this repo, it should be configured, but will need to
   be started manually with : `rc-service mosquitto start`

2. If remote, use `ssh` port forwarding to duplicate traffic from the Nottinghack MQTT server to
   the test host. `ssh -L 1883:localhost:1883 <connection-deets>`

   - `mkdir $HOME/.ssh ; chmod 700 $HOME/.ssh`
   - `lbu add $HOME/.ssh`
   - Copy your Nottinghack remote access config / keys to `$HOME/.ssh`
   - `lbu commit`
   - `ssh -N -L 1883:localhost:1883 <remote-server-id>`
   - leave the `ssh` command running until done with the repeater

3. Start the repeater. The first argument is the name of the MQTT broker to listen to:
   `./repeater.py localhost:1883`

   If running on-site, replace `localhost` with the name of the Nottinghack MQTT broker host.

