from machine import Pin, PWM, I2C
from umqtt.simple import MQTTClient
import ujson
import network
import utime as time
import dht
from led_pwm import LED
from machine import SoftI2C
from i2c_lcd import I2cLcd


# Device Setup
DEVICE_ID = "wokwi002"

# WiFi Setup
WIFI_SSID = "Wokwi-GUEST"
WIFI_PASSWORD = ""

# MQTT Setup
MQTT_BROKER = "5ef675a2962542dc975a98b116ba9add.s1.eu.hivemq.cloud"
MQTT_CLIENT = DEVICE_ID
MQTT_TELEMETRY_TOPIC = 'iot/device/{0}/telemetry'.format(DEVICE_ID)
MQTT_CONTROL_TOPIC = 'iot/device/{0}/control'.format(DEVICE_ID)
MQTT_MASTER_TELEMETRY_TOPIC = 'iot/telemetry'.format(DEVICE_ID)
MQTT_MASTER_CONTROL_TOPIC = 'iot/control'.format(DEVICE_ID)

# DHT Sensor Setup
DHT_PIN = Pin(15)
dht_sensor = dht.DHT22(DHT_PIN)

DHT_PIN_RED = Pin(25)
dht_sensor_dog_red = dht.DHT22(DHT_PIN_RED)

# LED/LAMP Setup
RED_LED = LED(12)
BLUE_LED = LED(13)
FLASH_LED = Pin(2, Pin.OUT)


# Turn On LED
RED_LED.on(60)
BLUE_LED.on(60)

# Motion Sensor LED
RAZ_MOTION_BLUE = Pin(14, Pin.IN, Pin.PULL_UP)
DOG_MOTION_RED = Pin(26, Pin.IN, Pin.PULL_UP)


# gateway time variable
gateway_time = "08:00:00"   # default gateway time = 8:00 AM
gateway_day = "monday"   # default day = monday
temp_diff_dog = 0.0   # add difference to dog temp
temp_diff_raz = 0.0   # add difference to dog temp

# Define LCD params
AddressOfLcd = 0x27
# connect scl to GPIO 22, sda to GPIO 21
i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=400000)
lcd = I2cLcd(i2c, AddressOfLcd, 4, 20)


# Methods
def did_recieve_callback(topic, message):
    print('\n\nData Recieved! \ntopic = {0}, message = {1}'.format(
        topic, message))

    if topic == MQTT_CONTROL_TOPIC.encode():
        # Get the command message from json command.
        command_message = ujson.loads(message.decode())["command"]
        if command_message == "lamp/red/on":
            RED_LED.on()
            send_led_status()
        elif command_message == "lamp/red/off":
            RED_LED.off()
            send_led_status()
        elif command_message == "lamp/blue/on":
            BLUE_LED.on()
            send_led_status()
        elif command_message == "lamp/blue/off":
            BLUE_LED.off()
            send_led_status()
        elif command_message == "lamp/on":
            RED_LED.on()
            BLUE_LED.on()
            send_led_status()
        elif command_message == "lamp/off":
            RED_LED.off()
            BLUE_LED.off()
            send_led_status()
        elif command_message == "status":
            mqtt_client_publish(MQTT_TELEMETRY_TOPIC, get_sensor_json_data())
            send_led_status()
        elif len(command_message.split('/')) == 4 and command_message.split('/')[2] == "brightness":
            # "lamp/red/brightness/34"
            brightness_commands = command_message.split('/')
            brightness_value = float(brightness_commands[3])
            if (brightness_commands[1] == "red"):
                RED_LED.set_brightness(brightness_value)
            if (brightness_commands[1] == "blue"):
                BLUE_LED.set_brightness(brightness_value)

            send_led_status()
        else:
            return

    # MQTT_MASTER_CONTROL_TOPIC is used for Google Home Integration.
    if topic == MQTT_MASTER_CONTROL_TOPIC.encode():
        # Get the command message from json command.

        
        try:
            received_message = ujson.loads(message.decode())
        except ValueError:
            received_message = {}

        command_data = {}
        if 'type' in received_message:
            if received_message['type'] == "ml_api_command":
                if "data" in received_message:
                    command_data = received_message['data']
                    cmd_gateway = command_data['device_id'].split("::")[0]
                    print("GATEWAY ID = ", cmd_gateway)
                    if cmd_gateway == DEVICE_ID:
                        process_commands(command_data)
                    else:
                        print("ML Message is not for this device")
            elif received_message['type'] == "ping" and received_message['id'] == DEVICE_ID:
                print("PING Message Received")
            else:
                print("Message not of type COMMAND or PING")
        else:
            print("Message type invalid, do not process.")


def mqtt_connect():
    print("Connecting to MQTT broker ...", end="")
    mqtt_client = MQTTClient(MQTT_CLIENT, MQTT_BROKER, user="raziotmachinelearning",
                             password="machinelearningiotraz", ssl=True, ssl_params={'server_hostname': MQTT_BROKER})
    mqtt_client.set_callback(did_recieve_callback)
    mqtt_client.connect()
    print("Connected.")
    mqtt_client.subscribe(MQTT_CONTROL_TOPIC)
    # subscribe to master topics for Google Home Control
    mqtt_client.subscribe(MQTT_MASTER_CONTROL_TOPIC)
    return mqtt_client


def create_control_json_data(command, command_id):
    # import ujson
    data = ujson.dumps({
        "device_id": DEVICE_ID,
        "command_id": command_id,
        "command": command
    })
    return data

def get_sensor_json_data():
    data = ujson.dumps({
        "device_id": DEVICE_ID,
        "temp": dht_sensor.temperature(),
        "humidity": dht_sensor.humidity(),
        "motion_dog": "true" if motion_detected_red else "false",
        "motion_raz": "true" if motion_detected_blue else "false",
        "type": "sensor"
    })
    return data


def get_all_parts_settings():
    data = {
        "device_id": DEVICE_ID,
        "temp": dht_sensor.temperature(),
        "humidity": dht_sensor.humidity(),
        "red_led": True if RED_LED.value() == 1 else False,
        "blue_led": True if BLUE_LED.value() == 1 else False,
        "motion_dog": "true" if motion_detected_red else "false",
        "motion_raz": "true" if motion_detected_blue else "false",
        "red_led_brightness": RED_LED.get_brightness(),
        "blue_led_brightness": BLUE_LED.get_brightness(),
        "motion_time_settings": get_motion_time_settings()
    }

    return data


def get_motion_time_settings():
    global motion_detected_red
    global motion_detected_blue
    global temp_diff_dog
    global temp_diff_raz

    dog_room_temp_val = dht_sensor_dog_red.temperature() + temp_diff_dog
    raz_room_temp_val = dht_sensor.temperature() + temp_diff_raz

    data = [{
        "time": gateway_time,
        "day": gateway_day,
        "motion": motion_detected_red,
        "temp_df": celsius_to_fahrenheit(dog_room_temp_val),
        "room_type": "dog"
    },
        {
        "time": gateway_time,
        "day": gateway_day,
        "motion": motion_detected_blue,
        "temp_df": celsius_to_fahrenheit(raz_room_temp_val),
        "room_type": "raz"
    }
    ]

    dog_fan_state = "ON" if RED_LED.value() == 1 else "OFF"
    raz_fan_state = "ON" if BLUE_LED.value() == 1 else "OFF"

    lcd_print(0, "DAY: " + gateway_day[0:3].upper() + " | " + gateway_time)
    lcd_print(1, "DFN: " + dog_fan_state + " | " + "RFN: " + raz_fan_state)
    lcd_print(2, "DTP: " + str(dog_room_temp_val) + "C | " + str(celsius_to_fahrenheit(dog_room_temp_val)) + "F")
    lcd_print(3, "RTP: " + str(raz_room_temp_val) + "C | " + str(celsius_to_fahrenheit(raz_room_temp_val)) + "F")

    return data


def celsius_to_fahrenheit(celsius):
    fahrenheit = (celsius * 9/5) + 32
    return round(fahrenheit)


def create_master_json_data():
    data = ujson.dumps(get_all_parts_settings())
    return data


def mqtt_client_publish(topic, data):
    try:
        print("\nUpdating MQTT Broker...")
        mqtt_client.publish(topic, data)
        print(data)
    except:
        print("MQTT client may not be initialized.")


def send_led_status():
    data = ujson.dumps({
        "device_id": DEVICE_ID,
        "red_led": "ON" if RED_LED.value() == 1 else "OFF",
        "blue_led": "ON" if BLUE_LED.value() == 1 else "OFF",
        "motion_dog": "true" if motion_detected_red else "false",
        "motion_raz": "true" if motion_detected_blue else "false",
        "red_led_brightness": RED_LED.get_brightness(),
        "blue_led_brightness": BLUE_LED.get_brightness(),
        "type": "lamp"
    })
    mqtt_client_publish(MQTT_TELEMETRY_TOPIC, data)


def get_part_by_name(name):
    if name == "red_led":
        return RED_LED
    if name == "blue_led":
        return BLUE_LED


def send_ack_data(data):
    mqtt_client_publish(MQTT_MASTER_TELEMETRY_TOPIC, data)


def process_commands(commands):
    global gateway_time
    global gateway_day
    global temp_diff_dog
    global temp_diff_raz

    acknowledge = commands["command_ack"]
    print("YYYYYYY: ", acknowledge)

    if acknowledge:
        data = ujson.dumps({
            "comment": "received, thank you!",
            "gatewayId": DEVICE_ID,
            "data": commands,
        })
        send_ack_data(data)
        print("ACK SENT TO ", DEVICE_ID)

    # part = command["deviceId"].split("::")[1]
    cmd_device = commands["device_id"].split("::")[1]
    if cmd_device == "time":
        all_cmds = commands["commands"]
        for cmd in all_cmds:
            if cmd["name"] == "time":
                gateway_time = cmd["value"]
            if cmd["name"] == "day":
                gateway_day = cmd["value"]
            if cmd["name"] == "temp_diff_dog":
                temp_diff_dog = cmd["value"]
            if cmd["name"] == "temp_diff_raz":
                temp_diff_raz = cmd["value"]
    elif cmd_device == "red_led" or cmd_device == "blue_led":
        all_cmds = commands["commands"]
        for cmd in all_cmds:
            if cmd["name"] == "on":
                get_part_by_name(cmd_device).set_value(
                    0 if cmd["value"] == False else 1)
            if cmd["name"] == "brightness":
                get_part_by_name(cmd_device).set_brightness(cmd["value"])
    elif cmd_device == "dog_fan" or cmd_device == "raz_fan":
        all_cmds = commands["commands"]
        for cmd in all_cmds:
            # set RED_LED if raz fan, othewise set BLUE_LED
            led_control_name = "red_led" if cmd_device == "dog_fan" else "blue_led"
            if cmd["name"] == "state":
                # set LED value as 0 or 1
                if cmd["value"] == "off":
                    get_part_by_name(led_control_name).off()
                else:
                    get_part_by_name(led_control_name).on(60)


def mqtt_ping():
    data = ujson.dumps({
        "device_id": DEVICE_ID,
        "id": DEVICE_ID,
        "type": "ping",
        "devices": []
    })
    mqtt_client_publish(MQTT_MASTER_CONTROL_TOPIC, data)


def get_settings(gateway_id, setting_type, curr_settings):
    return {
        "id": gateway_id,
        "type": setting_type,
        "devices": curr_settings
    }

# Print user input


def lcd_print(row, value, start_col=0, space_padding=True):
    lcd.move_to(start_col, row)
    if space_padding:
        lcd.putstr(pad_string(str(value)))
    else:
        lcd.putstr(str(value))

# Pad String with Spaces


def pad_string(input_string, desired_length=19):
    current_length = len(input_string)
    if current_length >= desired_length:
        return input_string  # No need to pad if it's long enough

    # Calculate the number of spaces needed
    spaces_needed = desired_length - current_length

    # Append the required spaces to the string
    padded_string = input_string + " " * spaces_needed

    return padded_string


# Motion Sensing algorithm
# Initialize variables for the two sensors
motion_detected_red = False
last_motion_time_red = 0
motion_detected_blue = False
last_motion_time_blue = 0

# Function to handle motion detection for a sensor


def handle_motion(sensor_name, pir_pin, motion_detected, last_motion_time):
    pir_value = pir_pin.value()
    if pir_value == 1:
        if not motion_detected:
            print(f"Motion detected on {sensor_name} Sensor")
            motion_detected = True
            last_motion_time = time.ticks_ms()
        elif time.ticks_diff(time.ticks_ms(), last_motion_time) >= 15000:
            print(
                f"No motion on {sensor_name} Sensor for 4 seconds, resetting state")
            motion_detected = False
    else:
        if motion_detected and time.ticks_diff(time.ticks_ms(), last_motion_time) >= 15000:
            print(f"No motion on {sensor_name} Sensor for 4 seconds")
            motion_detected = False
    return motion_detected, last_motion_time


# Define a function to check and execute a function after a certain delay
def check_and_execute(func, delay_seconds, start_time):
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, start_time) >= (delay_seconds * 1000):
        func()
        # Reset the timer for the function
        return time.ticks_ms()
    return start_time

# Methods to check sensors and ping device status
# Initialize timers for each check_sensors and clear_mqtt_topics
start_time_check_sensors = time.ticks_ms()
start_time_clear_mqtt_topics = time.ticks_ms()

# check sensors
def check_sensors():
    print("\n****** CHECKING : SENSORS ******")
    global master_data_old
    master_data_new = create_master_json_data()

    if master_data_new != master_data_old:
        mqtt_client_publish(MQTT_TELEMETRY_TOPIC, get_sensor_json_data())
        send_led_status()
        master_data_old = master_data_new
        # oled_print()    #print out to OLED

        # update device settings in cloud.
        all_settings = ujson.dumps(
            get_settings(DEVICE_ID, "predict_ml_settings",
                         get_motion_time_settings())
        )
        mqtt_client_publish(MQTT_MASTER_CONTROL_TOPIC, all_settings)

# clear mqtt retained messages
def clear_mqtt_topics():
    # mqtt_ping()
    print("\n****** MQTT : CLEAR ******")
    mqtt_client.publish(MQTT_MASTER_CONTROL_TOPIC, b"", retain=True)
    mqtt_client.publish(MQTT_MASTER_TELEMETRY_TOPIC, b"", retain=True)

# -------------- Application Logic --------------


# Connect to WiFi
wifi_client = network.WLAN(network.STA_IF)
wifi_client.active(True)
print("Connecting device to WiFi")
wifi_client.connect(WIFI_SSID, WIFI_PASSWORD)

# Wait until WiFi is Connected
while not wifi_client.isconnected():
    print("Connecting")
    time.sleep(0.1)
print("WiFi Connected!")
print(wifi_client.ifconfig())

# Connect to MQTT
mqtt_client = mqtt_connect()
mqtt_client_publish(MQTT_CONTROL_TOPIC, create_control_json_data(
    'lamp/off', 'DEVICE-RESET-00'))

# read dht_sensor and register device.
dht_sensor.measure()
time.sleep(0.2)
dht_sensor_dog_red.measure()
time.sleep(0.2)


# init data
master_data_old = ""



while True:
    mqtt_client.check_msg()
    print(". ", end="")

    try:
        FLASH_LED.on()
        dht_sensor.measure()
        # Handle Red Sensor
        motion_detected_red, last_motion_time_red = handle_motion(
            "Red", DOG_MOTION_RED, motion_detected_red, last_motion_time_red)

        # Handle Blue Sensor
        motion_detected_blue, last_motion_time_blue = handle_motion(
            "Blue", RAZ_MOTION_BLUE, motion_detected_blue, last_motion_time_blue)

        time.sleep(0.2)
        dht_sensor_dog_red.measure()
        time.sleep(0.2)
        FLASH_LED.off()
    except:
        pass

    if motion_detected_red or motion_detected_blue:
        print("\nMOTION-DETECTED")


    # Check for sensor updates
    start_time_check_sensors = check_and_execute(check_sensors, 5, start_time_check_sensors)
    
    # Clear MQTT retained message
    start_time_clear_mqtt_topics = check_and_execute(clear_mqtt_topics, 20, start_time_clear_mqtt_topics)

    time.sleep(0.2)