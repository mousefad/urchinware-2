# Built-in python modules
import re
import time

# PIP-installed modules
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import cachetools.func
from singleton_decorator import singleton

# Project modules
from dorcas.sensation import Sensation
from dorcas.database import *
from dorcas.worker import Worker


log = logging.getLogger(os.path.basename(sys.argv[0]))


@singleton
class MqttClient(Worker):
    """MQTT client configured as per config in database"""
    def __init__(self, brain):
        self.brain = brain
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion(2),
            client_id=brain.config.broker.client_id,
            transport="tcp",
            protocol=mqtt.MQTTv31,
            clean_session=self.brain.config.broker.clean,
        )
        self.client.on_connect = self.cb_connect
        self.client.on_connect_fail = self.cb_connect_fail
        self.client.on_message = self.cb_message
        self.receivers = set()

    @property
    @cachetools.func.ttl_cache(ttl=23)
    def ignores(self):
        ignore_list = list()
        for rec in DB().session.query(Ignore).all():
            ignore_list.append((re.compile(rec.topic_re), re.compile(rec.message_re)))
        return ignore_list

    @property
    @cachetools.func.ttl_cache(ttl=23)
    def mqtt_host(self):
        return self.brain.config.broker.host

    @property
    @cachetools.func.ttl_cache(ttl=23)
    def mqtt_port(self):
        return self.brain.config.broker.port

    def start(self):
        log.debug(f"mqtt.start")
        code = self.client.connect(
            self.mqtt_host,
            port=self.mqtt_port, 
            keepalive=self.brain.config.broker.keep_alive
        )
        log.debug(f"connect code={code!r}")
        code = self.client.loop_start()
        log.debug(f"loop_start code={code!r}")
        self.client.subscribe("#", 2)

    def stop(self):
        log.debug(f"mqtt.stop")
        # TODO: shut down MQTT client thread properly
        pass

    def wait(self):
        log.debug(f"mqtt.wait")
        # TODO: shut down MQTT client thread properly
        pass

    def run(self):
        while not halt:
            time.sleep(1)

    def register_receiver(self, fn):
        self.receivers.add(fn)

    def unregister_receiver(self, fn):
        self.receivers.remove(fn)

    def publish(self, topic, message):
        if not self.brain.get("mute_mqtt"):
            publish.single(topic, message, hostname=self.mqtt_host, port=self.mqtt_port)

    def cb_connect(self, *args):
        log.info(f"MQTT connect success: {args}")

    def cb_connect_fail(self, *args):
        self.experience(Sensation("nh/urchin/error/mqtt", "connection to MQTT broker failed"))
        log.error(f"MQTT connect failure: {args}")

    def cb_message(self, client, user_data, message, properties=None):
        if len(self.receivers) == 0:
            return
        str_message = message.payload.decode() if type(message.payload) is bytes else str(message.payload)
        desc = f"topic={message.topic!r} message={str_message!r}"
        if self.drop(message.topic, str_message):
            log.log(logging.DEBUG - 1, f"MQTT ignore message: {desc}")
            return
        log.log(logging.DEBUG - 1, f"MQTT message: {desc}")
        s = Sensation(message.topic, str_message)
        for receiver in self.receivers:
            receiver(s)

    def drop(self, topic, message):
        for trx, mrx in self.ignores:
            if trx.match(topic) and mrx.match(message):
                return True
        return False

