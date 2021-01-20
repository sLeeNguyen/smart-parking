import json
import paho.mqtt.client as mqtt

from core.consumers import send_parking_state_data
from devices.models import Device

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
SUB_TOPICS = ("device/auth", "device/status", "device/control",)
RECONNECT_DELAY_SECS = 2


class MQTTClient(mqtt.Client):
    __instance = None

    def __init__(self):
        super().__init__()
        print("Create instance of MQTTClient")

    @classmethod
    def __setup_instance(cls):
        client = cls.__instance
        client.on_connect = cls._on_connect
        client.on_message = cls._on_message
        client.on_publish = cls._on_publish
        client.on_subscribe = cls._on_subscribe
        client.on_disconnect = cls._on_disconnect

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = MQTTClient()
            cls.__setup_instance()
        return cls.__instance

    # The callback for when the client receives a CONNACK response from the server.
    def _on_connect(client, userdata, flags, rc):
        print("Connected with result code " + str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        for topic in SUB_TOPICS:
            client.subscribe(topic, qos=1)

    # The callback for when a PUBLISH message is received from the server.
    def _on_message(client, userdata, msg):
        print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
        data = json.loads(msg.payload)
        device_id = data['device_id']
        try:
            device = Device.objects.get(pk=device_id)
            slot = int(data['slot'])
            status = int(data['status'])
            if status not in [0, 1] or slot not in [1, 2, 3, 4, 5, 6]:
                return
            if device.set_slot(status=status, pos=slot):
                device.save()
                if device.is_active:
                    send_parking_state_data({
                        "id": "%s-%s" % (device.position, data['slot']),
                        "deviceId": data['device_id'],
                        "position": data['slot'],
                        "status": data['status']
                    })
        except (Device.DoesNotExist, ValueError):
            print()
            pass

    def _on_publish(mosq, obj, mid):
        print("mid: " + str(mid))

    def _on_subscribe(mosq, obj, mid, granted_qos):
        print("Subscribed: " + str(mid) + " " + str(granted_qos))

    def _on_log(mosq, obj, level, string):
        print(string)

    def _on_disconnect(client, userdata, rc):
        client.loop_stop(force=False)
        if rc != 0:
            print("Failed to connect, return code " + str(rc))
        else:
            print("Disconnected: rc:" + str(rc))

    def default_connect(self):
        print("Made a default connection to broker %s:%s" % (MQTT_BROKER, MQTT_PORT))
        self.connect(MQTT_BROKER, MQTT_PORT)
