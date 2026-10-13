import json
from urllib.error import URLError
from urllib.request import urlopen

from mock_data.environment import climate_for

POWER_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
FILL_VALUE = -900


def climate_from_nasa(latitude: float, longitude: float) -> dict | None:
    query = (
        f"{POWER_URL}?parameters=T2M,PRECTOTCORR&community=AG"
        f"&longitude={longitude}&latitude={latitude}&format=JSON"
    )
    try:
        with urlopen(query, timeout=12) as response:
            payload = json.load(response)
        parameters = payload["properties"]["parameter"]
        temperature = float(parameters["T2M"]["ANN"])
        daily_rain = float(parameters["PRECTOTCORR"]["ANN"])
    except (URLError, TimeoutError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    if temperature < FILL_VALUE or daily_rain < FILL_VALUE:
        return None
    return {
        "annual_rainfall_mm": max(0, round(daily_rain * 365.25)),
        "average_temperature_c": round(temperature, 1),
        "growing_season": climate_for(latitude)["growing_season"],
        "source": "NASA POWER climatology (temperature and rainfall)",
    }
