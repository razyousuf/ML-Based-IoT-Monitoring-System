# **Smart IoT Temperature and Motion Monitoring System with Machine Learning**

### **Overview**
This project is an IoT-based adaptive system that uses temperature and motion sensors to monitor environmental conditions and control LEDs/fans for two different zones (Dog Room and Raz Room). It leverages **MicroPython**, **MQTT** for messaging, **FastAPI** for machine learning-based predictions, and an **LCD display** to show real-time sensor data. The system supports both manual control (via MQTT commands) and automatic sensor-based control, making it an efficient solution for smart homes or remote monitoring systems.

---

### **Table of Contents**
- [Project Features](#project-features)
- [System Architecture](#system-architecture)
- [Hardware Setup](#hardware-setup)
- [Software Setup](#software-setup)
  - [Libraries](#libraries)
  - [MQTT Broker](#mqtt-broker)
  - [Machine Learning API](#machine-learning-api)
  - [Connecting to WiFi](#connecting-to-wifi)
  - [Running the Code](#running-the-code)
- [Usage](#usage)
  - [Manual Control via MQTT](#manual-control-via-mqtt)
  - [Data Monitoring](#data-monitoring)
  - [Machine Learning Predictions](#machine-learning-predictions)
- [Future Improvements](#future-improvements)
- [Contributors](#contributors)

---

### **Project Features**
- **Temperature and Humidity Monitoring**: Uses DHT22 sensors to measure temperature and humidity for both the Dog Room and Raz Room.
- **Motion Detection**: PIR motion sensors detect movement in each room, enabling automatic responses.
- **MQTT Communication**: Real-time control and data publishing using MQTT protocol.
- **LED/Fan Control**: Adaptive control of LEDs (acting as fans) based on sensor data and user commands.
- **Machine Learning Model**: Predicts future temperature changes using a FastAPI-based ML model deployed on a remote server.
- **LCD Display**: Displays current status, sensor readings, and room conditions in real-time.
- **Google Home Integration**: Supports external control via MQTT master topics for integration with voice assistants.

---

### **System Architecture**
The project architecture involves the following components:
1. **Sensors and Actuators** (ESP32/ESP8266):
   - Reads temperature, humidity, and motion data.
   - Sends this data to the MQTT broker and LCD.
   - Receives control commands to activate LEDs/fans based on sensor input.
   
2. **MQTT Broker**:
   - Handles communication between the ESP devices and other control systems like Google Home or a mobile app.
   
3. **FastAPI-based Machine Learning API**:
   - A remote **FastAPI** server hosts a **Random Forest machine learning model** trained to predict temperature, humidity and motion based on historical data.
   - The API is queried by the ESP device to adjust the system automatically based on predictions.

---

### **Hardware Setup**
The following hardware components are used in this project:
- **ESP32 or ESP8266**: For running MicroPython and connecting to the internet.
- **DHT22 Sensors (x2)**: For temperature and humidity measurement in two zones.
- **PIR Motion Sensors (x2)**: To detect movement in the Dog Room and Raz Room.
- **LEDs (x2)**: To represent fans or light control in each room.
- **I2C LCD Display (4x20)**: To show real-time data and status of the system.
- **Wires & Breadboard**: For connecting sensors, LEDs, and other peripherals.

**Pin Configuration**:
| Component        | Pin         |
|------------------|-------------|
| DHT Sensor 1     |             |
| DHT Sensor 2     |             |
| Red LED (Dog)    |             |
| Blue LED (Raz)   |             |
| Motion Sensor 1  |             |
| Motion Sensor 2  |             |
| I2C LCD (SCL/SDA)|             |

---

### **Software Setup**

#### **Libraries**
The project requires the following libraries to run on **MicroPython**:
1. `umqtt.simple` - MQTT client for ESP32.
2. `dht` - For reading data from DHT22 sensors.
3. `led_pwm.py` - Custom class for controlling the brightness of the LEDs.
4. `i2c_lcd.py` - For controlling the I2C LCD display.

#### **MQTT Broker**
Broker details in the project:
```bash
  MQTT_BROKER = "your_broker_address"
  MQTT_CLIENT = "wokwi001"  # Replace with your device ID
```


#### **Machine Learning API**
The **FastAPI-based ML model** is deployed on a remote server to predict temperature based on historical sensor data. The **ESP32/ESP8266** device sends periodic sensor readings to the API, and in return, the API provides predictions that help the system adjust its behavior (e.g., turning on/off fans, LEDs).

##### **ML API Endpoint**:
- **URL**: 
- **Method**: POST
- **Request Format**:
  
```bash
  {
    "current_temp": 23.5,
    "current_humidity": 60,
    "room": "dog_room"
  }
```

- **Response Example**:
```bash
  {
    "predicted_temp": 24.8
  }
```


#### **Connecting to WiFi**
Edit the **WiFi credentials** in the code to connect to your local WiFi:

```bash
  WIFI_SSID = "Your-SSID"
  WIFI_PASSWORD = "Your-PASSWORD"
```

---

### **Running the Code**
1. **Flash MicroPython**: Ensure your ESP32/ESP8266 board is running MicroPython. You can flash the latest version from [MicroPython's official website](https://micropython.org/download/esp32/).
2. **Upload the Code**: Use tools like **Thonny IDE** or **ampy** to upload the `.py` files to your ESP32/ESP8266 board.
3. **Run the Code**: After uploading, the device will:
   - Connect to WiFi and the MQTT broker.
   - Start reading data from the DHT22 sensors and motion detectors.
   - Send sensor data to the **FastAPI** ML server for predictions.
   - Display the data on the LCD and publish it to the MQTT topics.

---

### **Usage**

#### **Manual Control via MQTT**
You can manually control the LEDs (fans) via MQTT commands. Send control messages to the `iot/device/{device_id}/control` topic in JSON format. Examples include:

 - Turn on the Red LED (Dog Room):
   ```bash
     {"command": "lamp/red/on"}
   ```
 - Turn off the Blue LED (Raz Room):
   ```bash
    {"command": "lamp/blue/off"}
  ```
 - Adjust brightness of LEDs:

   ```bash 
    {"command": "lamp/red/brightness/50"}
   ```


#### **Data Monitoring**
The system continuously sends temperature, humidity, and motion data to the telemetry topic:

  ```bash
    {
  "device_id": "wokwi001",
  "temp": 24.5,
  "humidity": 60,
  "motion_dog": "true",
  "motion_raz": "false",
  "type": "sensor"
  }
  ```


#### **Machine Learning Predictions**
The system also queries the **FastAPI** ML server to receive predictions for real-time temperature adjustments. The predicted data is automatically applied to adjust the LEDs/fans accordingly. You can monitor these predictions via the API logs or a connected MQTT dashboard.

---

### **Future Improvements**
1. **Refine the ML Model**: Continuously improve the machine learning model with more data for better accuracy in predictions.
2. **Add More Sensors**: Extend the system to monitor more rooms or environmental factors (CO2, light levels, etc.).
3. **Mobile App Interface**: Develop a mobile app for better control and visualization of sensor data.

---

Feel free to reach out for feedback or suggestions through my email address at razyousufi350@gmail.com
