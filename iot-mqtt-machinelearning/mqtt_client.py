import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes 
import json
import ssl

class MQTTClient:
    def __init__(self, broker_host, broker_port, username, password):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        # self.mqtt_client = mqtt.Client()
        #self.mqtt_client = mqtt.Client(client_id="myPy",transport='tcp', protocol=mqtt.MQTTv5)
        self.mqtt_client = mqtt.Client(client_id="myPy", transport='tcp', protocol=mqtt.MQTTv5, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)

        # Set up TLS/SSL for secure communication
        self.mqtt_client.tls_set(certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED)

        # Connect to the MQTT broker
        self.mqtt_client.username_pw_set(self.username, self.password)

        properties=Properties(PacketTypes.CONNECT)
        properties.SessionExpiryInterval=30*60 # in seconds
        self.mqtt_client.connect(self.broker_host, port=self.broker_port, clean_start=mqtt.MQTT_CLEAN_START_FIRST_ONLY, properties=properties, keepalive=60);
        self.mqtt_client.loop_start();

        def on_message(m_client, userdata, message):
            print("Received message on topic:", message.topic)
            print("Message payload:", message.payload.decode())
            if self.response_callback:
                self.response_callback(message.payload)

        self.mqtt_client.on_message = on_message

        # Define a callback for handling incoming MQTT messages
        self.response_callback = None

    def subscribe_response_topic(self, response_topic):
        self.mqtt_client.subscribe(response_topic, qos=2)
        print("_______SUBSCRIBED________")

    def set_response_callback(self, callback):
        print("_______CALLBACK_SET________")
        self.response_callback = callback

    def disconnect(self):
        print("_______DISCONNECTED________")
        self.mqtt_client.disconnect()

    def send_command(self, control_topic, command):
        print("_______COMMAND SENT________")
        properties=Properties(PacketTypes.PUBLISH)
        properties.MessageExpiryInterval=3 # in seconds

        # Publish the command to the control topic
        self.mqtt_client.publish(control_topic, payload="", retain=True)
        self.mqtt_client.publish(control_topic, json.dumps({"type" : "ml_api_command", "data": command}), 1, properties = properties, retain=False)


    def on_connect(client, userdata, flags, rc, v5config=None):
        print("_______CONNECTED________")

    def on_publish(client, userdata, mid,tmp=None):
        print("_______PUBLISHED________")

    def get_client_obj(self):
        return self.mqtt_client
    