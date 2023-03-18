import datetime

from pydantic import BaseModel as PydanticBaseModel, validate_model


class BaseModel(PydanticBaseModel):
    def check(self):
        *_, validation_error = validate_model(self.__class__, self.__dict__)
        if validation_error:
            raise validation_error


class DeviceSensors(BaseModel):
    battery: str
    temperature: str
    humidity: str
    co2: str


class DeviceConfig(BaseModel):
    deveui: str
    """LoRaWAN Device EUI"""

    name: str
    """Airnominal Station Name"""

    uuid: str
    """Airnominal Station ID"""

    token: str
    """Airnominal Station Token"""

    lat: float
    """Airnominal Station Latitude"""

    lon: float
    """Airnominal Station Longitude"""

    sensors: DeviceSensors
    """Airnominal Sensor Short IDs"""


class MilesightRawPayload(BaseModel):
    time: datetime.datetime
    """Measurement Timestamp"""

    deveui: str
    """LoRaWAN Device EUI"""

    payload: str
    """LoRaWAN Payload"""

    fcnt: int
    """LoRaWAN Frame Counter"""

    fport: int
    """LoRaWAN Frame Port"""


class MilesightDecodedPayload(BaseModel):
    time: datetime.datetime
    """Measurement Timestamp"""

    deveui: str
    """LoRaWAN Device EUI"""

    battery: float
    """Battery Measurement"""

    temperature: float
    """Temperature Measurement"""

    humidity: float
    """Humidity Measurement"""

    co2: float
    """CO2 Measurement"""
