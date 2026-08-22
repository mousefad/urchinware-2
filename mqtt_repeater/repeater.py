#!/usr/bin/env python3

import click
import paho.mqtt.client as mqtt

def parse_address(address_str, default_port):
    parts = address_str.split(':')
    host = parts[0]
    port = int(parts[1]) if len(parts) > 1 else default_port
    return host, port

@click.command()
@click.option('--source', default='localhost:1883', help='Source broker (hostname:port)')
@click.option('--destination', default='localhost:2883', help='Destination broker (hostname:port)')
def main(source, destination):
    src_host, src_port = parse_address(source, 1883)
    dst_host, dst_port = parse_address(destination, 2883)

    # Initialize destination client
    # Note: If using paho-mqtt v2.0+, you may need to initialize with:
    # mqtt.Client(mqtt.CallbackAPIVersion.VERSION1) or VERSION2
    dest_client = mqtt.Client()
    dest_client.connect(dst_host, dst_port)
    dest_client.loop_start()

    def on_connect(client, userdata, flags, rc):
        client.subscribe("#")

    def on_message(client, userdata, msg):
        dest_client.publish(msg.topic, msg.payload, qos=msg.qos, retain=msg.retain)

    # Initialize source client
    src_client = mqtt.Client()
    src_client.on_connect = on_connect
    src_client.on_message = on_message

    src_client.connect(src_host, src_port)

    try:
        src_client.loop_forever()
    except KeyboardInterrupt:
        pass
    finally:
        src_client.loop_stop()
        dest_client.loop_stop()
        src_client.disconnect()
        dest_client.disconnect()

if __name__ == '__main__':
    main()
