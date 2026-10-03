import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_weather(city: str) -> str:
    """Fetch current weather data for a city."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Error: API key not found"

    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        description = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
        humidity = data["main"]["humidity"]

        return f"Current weather in {city}: {description}. Temperature: {temperature}°C, Humidity: {humidity}%"
    except Exception as e:
        return f"Error fetching weather data: {str(e)}"