from ast import *
import asyncio
from enum import Enum
import json
from typing import Any
from fastapi.responses import JSONResponse
import joblib
import numpy as np
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Header, Path, Query, Request
from helpers import convert_features, fahrenheit_to_celsius, predict_map
from mqtt_client import MQTTClient
from app_constants import ConnectionParams



# API description.
app = FastAPI(
    title="Raz IoT ML API",
    description="**This Python API is designed to connect with IoT devices and run ML commands.**",
    version="1.0.0",
)

class RoomType(Enum):
    """Room Type Enum"""
    DOG = "dog"
    RAZ = "raz"

class DayType(Enum):
    """Weekday Type Enum"""
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"


# ------------ CLASSES --------------
class ApiResponse(BaseModel):
    """ApiResponse Object"""
    status: str
    payload: Any

class Command(BaseModel):
    """Command Object"""
    name: str = Field(description="Command Name")
    value: Any = Field(description="Set Value")

class Device(BaseModel):
    """Device Object"""
    device_id: str = Field(description="Device Id.")
    command_ack: bool = Field(description="Acknoledge response")
    commands: list[Command] = Field(description="List of Commands")

class PredictFeatures(BaseModel):
    """PredictFeatures Model"""
    time: str = Field(description="time format: HH:MM:SS")
    day: DayType = Field(description="Day string: monday, tuesday, wednesday, etc...")
    motion: bool = Field(description="Room motion: Bool")
    temp_df: int = Field(description="Room temp: deg. F")
    room_type: RoomType = Field(description="Room temp: deg. F")

# -----------------------------------

# ------------ API's ----------------
@app.post("/execute")
async def execute_command(params: Device) -> ApiResponse:
    # # MQTT Configuration
    response_event = push_commands_to_device(params)
        
    try:
        # Wait for the acknowledgment and retrieve the payload
        if params.command_ack:
            response_payload = await asyncio.wait_for(response_event.get(), timeout=10)
            response = {"status": "success", "payload": response_payload}
            return ApiResponse(**response)
        else:
            response = {"status": "success", "payload": []}
            return ApiResponse(**response)
        
    except asyncio.TimeoutError:
        # Handle the case where no response payload was received within a timeout
        return JSONResponse(content={"status": "ack-timeout", "message": "device might be offline"}, status_code=404)
    

@app.post("/execute/prediction/{gateway_id}")
async def execute_predictio(gateway_id:str, prediction_params: PredictFeatures) -> ApiResponse:
    #Get Prediction
    raz_predict, dog_predict = get_predictions([prediction_params])
    prediction = predict_map(raz_predict + dog_predict)[0]

    device_name = None
    if prediction_params.room_type.value == RoomType.DOG.value:
        device_name = RoomType.DOG.value + "_fan"
    else:
        device_name = RoomType.RAZ.value + "_fan"

    # format device command
    device = {
        "device_id": gateway_id + "::" + device_name,
        "command_ack": False,
        "commands": [
            {
                "name": "state",
                "value": prediction
            }
        ]
    }

    # send command to device
    params = Device(**device)
    response_event = push_commands_to_device(params)
        
    try:
        # Wait for the acknowledgment and retrieve the payload
        if params.command_ack:
            response_payload = await asyncio.wait_for(response_event.get(), timeout=10)
            response = {"status": "success", "payload": response_payload}
            return ApiResponse(**response)
        else:
            response = {"status": "success", "payload": prediction}
            return ApiResponse(**response)
        
    except asyncio.TimeoutError:
        # Handle the case where no response payload was received within a timeout
        return JSONResponse(content={"status": "ack-timeout", "message": "device might be offline"}, status_code=404)



@app.post("/predict")
def predict(params: list[PredictFeatures]) -> ApiResponse:

    raz_predict, dog_predict = get_predictions(params)
    predictions = raz_predict + dog_predict
    predictions = predict_map(predictions)
    
    response = {"status": "success", "payload": predictions}
    return ApiResponse(**response)


@app.post("/set_clock/{gateway_id}")
async def set_time(gateway_id:str, 
                   time: str = Query(..., description="gateway time", example="08:00:00"), 
                   day: DayType = Query(..., description="Day", example=DayType.sunday),
                   dog_temp_diff: float = Query(..., description="themometer Fahrenheit (F) calibration difference [adds a negative or positive number]", example=0),
                   raz_temp_diff: float = Query(..., description="themometer Fahrenheit (F) calibration difference [adds a negative or positive number]", example=0)) -> ApiResponse:
    # format device command
    device = {
        "device_id": gateway_id + "::time",
        "command_ack": False,
        "commands": [
            {
                "name": "time",
                "value": time
            },
            {
                "name": "day",
                "value": day.value
            },
            {
                "name": "temp_diff_dog",
                "value": fahrenheit_to_celsius(32 + dog_temp_diff)
            },
            {
                "name": "temp_diff_raz",
                "value": fahrenheit_to_celsius(32 + raz_temp_diff)
            }
        ]
    }

    # send command to device
    params = Device(**device)
    response_event = push_commands_to_device(params)
        
    try:
        # Wait for the acknowledgment and retrieve the payload
        if params.command_ack:
            response_payload = await asyncio.wait_for(response_event.get(), timeout=10)
            response = {"status": "success", "payload": response_payload}
            return ApiResponse(**response)
        else:
            response = {"status": "success", "payload": device}
            return ApiResponse(**response)
        
    except asyncio.TimeoutError:
        # Handle the case where no response payload was received within a timeout
        return JSONResponse(content={"status": "ack-timeout", "message": "device might be offline"}, status_code=404)






# --------------------------------------------

# ------------ HELPER METHODS ----------------
def get_predictions(params):
    raz_fan_model = joblib.load("./models/raz_fan_model.joblib")
    dog_fan_model = joblib.load("./models/dog_fan_model.joblib")
    
    raz_fan_features = []
    dog_fan_features = []
    for feature in params:
        if feature.room_type == RoomType.RAZ:
            raz_fan_features.append(convert_features(feature))
        elif feature.room_type == RoomType.DOG:
            dog_fan_features.append(convert_features(feature))


    raz_predict = []
    dog_predict = []
    if len(raz_fan_features) > 0:
        raz_df = np.array(raz_fan_features)
        # Make predictions using the loaded model
        raz_predict = raz_fan_model.predict(raz_df).tolist()

    if len(dog_fan_features) > 0:
        dog_df = np.array(dog_fan_features)
        # Make predictions using the loaded model
        dog_predict = dog_fan_model.predict(dog_df).tolist()

    return raz_predict,dog_predict


def push_commands_to_device(params):
    # # MQTT Configuration
    MQTT_BROKER_PORT = 8883  # WSS MQTT over TLS port

    mqtt_client = MQTTClient(ConnectionParams.SERVER_URL, MQTT_BROKER_PORT, ConnectionParams.USERNAME, ConnectionParams.PASSWORD)

    # Set up the response callback and event
    response_event = asyncio.Queue()  # Use an asyncio.Queue to store the payloads

    def handle_response(message):
        try:
            payload = json.loads(message.decode())
             # Process the response here
            print("Received response:", payload)
            # Put the payload into the queue
            response_event.put_nowait(payload)
        except:
            print("_____ ERROR LOADING MQTT RESPONSE _____")

    #if params.command_ack:
    mqtt_client.set_response_callback(handle_response)
    mqtt_client.subscribe_response_topic(ConnectionParams.MASTER_TELEMETRY_TOPIC)
    
    # Send the command to the MQTT broker
    mqtt_client.send_command(ConnectionParams.MASTER_CONTROL_TOPIC, params.model_dump())
    return response_event

