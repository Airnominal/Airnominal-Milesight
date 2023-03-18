import base64
import json
import os
import secrets
import sys

import httpx
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import parse_obj_as

from models import DeviceConfig, MilesightDecodedPayload, MilesightRawPayload

CONFIG_ROOT_PATH = os.getenv("MILESIGHT_ROOT_PATH") or ""
CONFIG_USERNAME = os.getenv("MILESIGHT_SUBMIT_USERNAME")
CONFIG_PASSWORD = os.getenv("MILESIGHT_SUBMIT_PASSWORD")
CONFIG_API = os.getenv("MILESIGHT_SUBMISSION_API")

with open("devices.json", encoding="utf-8") as file:
    DEVICES = parse_obj_as(dict[str, DeviceConfig], json.load(file))

app = FastAPI(root_path=CONFIG_ROOT_PATH)
security = HTTPBasic(auto_error=False)


def authorize(credentials: HTTPBasicCredentials):
    """Check if username and password are correct"""

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Basic"},
        )

    is_correct_username = secrets.compare_digest(credentials.username.encode("utf8"), CONFIG_USERNAME.encode("utf8"))
    is_correct_password = secrets.compare_digest(credentials.password.encode("utf8"), CONFIG_PASSWORD.encode("utf8"))

    if not is_correct_username or not is_correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )


def decode(raw: MilesightRawPayload) -> MilesightDecodedPayload:
    """Decode raw Milesight AM103 payload"""

    def read_uint16_le(data: bytes) -> int:
        value = (data[1] << 8) + data[0]
        return value & 0xffff

    def read_int16_le(data: bytes) -> int:
        ref = read_uint16_le(data)
        return ref - 0x10000 if ref > 0x7fff else ref

    decoded = MilesightDecodedPayload.construct()
    decoded.time = raw.time
    decoded.deveui = raw.deveui

    payload = base64.b64decode(raw.payload)
    i = 0

    while i < len(payload):
        channel_id = payload[i]
        channel_type = payload[i + 1]

        # BATTERY
        if channel_id == 0x01 and channel_type == 0x75:
            decoded.battery = payload[i + 2]
            i += 3

        # TEMPERATURE
        elif channel_id == 0x03 and channel_type == 0x67:
            decoded.temperature = read_int16_le(payload[i + 2:i + 4]) / 10
            i += 4

        # HUMIDITY
        elif channel_id == 0x04 and channel_type == 0x68:
            decoded.humidity = payload[i + 2] / 2
            i += 3

        # CO2
        elif channel_id == 0x07 and channel_type == 0x7D:
            decoded.co2 = read_uint16_le(payload[i + 2:i + 4])
            i += 4

        else:
            break

    decoded.check()
    return decoded


@app.post("/")
async def submit(payload: MilesightRawPayload, credentials: HTTPBasicCredentials = Depends(security)):
    """Submit Milesight AM103 measurements"""

    if CONFIG_USERNAME and CONFIG_PASSWORD:
        authorize(credentials)

    print("RECEIVED PAYLOAD")

    decoded = decode(payload)
    device = DEVICES[decoded.deveui]

    print("Decoded", decoded, file=sys.stderr)
    print("Device", device, file=sys.stderr)

    timestamp = hex(int(decoded.time.timestamp()))[2:]
    message = f"{device.uuid}_{device.token}_{timestamp}_LAT_{device.lat}_LON_{device.lon}"

    for quantity, code in device.sensors.dict().items():
        message += f"_{code}_{getattr(decoded, quantity)}"

    message += "END"

    print("Message", message, file=sys.stderr)

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(CONFIG_API, json={"data": message})
        print("Response", response, file=sys.stderr)

    return {"success": True, "message": "Data received successfully"}
