"""tools.py - custom tools for the trip planner agent.

Usage in your agent file:
    from tools import TOOLS
    agent = create_agent(model=model, tools=TOOLS, system_prompt=SYSTEM_PROMPT)

Requires:  pip install requests langchain langchain-tavily python-dotenv
Env vars:  ANTHROPIC_API_KEY, TAVILY_API_KEY  (put them in a .env file)

Weather, travel time and currency tools use free APIs that need no key.
"""

import math
from datetime import date as Date, datetime

import requests
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_tavily import TavilySearch

load_dotenv()  # loads keys from .env into the environment

TIMEOUT = 10
# Nominatim (OpenStreetMap) requires an identifying User-Agent.
HEADERS = {"User-Agent": "trip-planner-learning-project/0.1"}

# Open-Meteo returns WMO weather codes; translate them to words the model can use.
WMO_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "freezing fog",
    51: "light drizzle", 53: "drizzle", 55: "heavy drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain",
    71: "light snow", 73: "snow", 75: "heavy snow",
    80: "light showers", 81: "showers", 82: "violent showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "severe thunderstorm with hail",
}


@tool
def get_weather(city: str, date: str) -> str:
    """Get the weather forecast for a city on a given date (YYYY-MM-DD).
    Use this to decide between indoor and outdoor activities.
    Forecasts only cover roughly the next 16 days."""
    try:
        target = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return f"Invalid date '{date}'. Use the format YYYY-MM-DD."

    days_ahead = (target - Date.today()).days
    if days_ahead < 0:
        return "That date is in the past, so no forecast is available."
    if days_ahead > 15:
        return (
            "That date is more than 16 days away, so no reliable forecast exists. "
            "Tell the user the weather is unknown and suggest packing for typical "
            "conditions for that time of year."
        )

    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
        timeout=TIMEOUT,
    ).json()
    if not geo.get("results"):
        return f"Could not find a city called '{city}'."
    place = geo["results"][0]

    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "daily": (
                "weather_code,temperature_2m_max,temperature_2m_min,"
                "precipitation_probability_max,wind_speed_10m_max"
            ),
            "start_date": date,
            "end_date": date,
            "timezone": "auto",
        },
        timeout=TIMEOUT,
    )
    if resp.status_code != 200:
        return f"Forecast unavailable: {resp.text}"

    d = resp.json()["daily"]
    condition = WMO_CODES.get(d["weather_code"][0], "unknown conditions")
    return (
        f"{place['name']}, {place.get('country', '')} on {date}: {condition}. "
        f"Low {d['temperature_2m_min'][0]}°C, high {d['temperature_2m_max'][0]}°C. "
        f"Rain chance {d['precipitation_probability_max'][0]}%. "
        f"Max wind {d['wind_speed_10m_max'][0]} km/h."
    )

_search = TavilySearch(max_results=5)


@tool
def find_events(city: str, date: str, interests: str) -> str:
    """Find concerts, festivals, exhibitions and shows happening in a city on
    ONE specific date (YYYY-MM-DD). Call once per day of the trip.
    'interests' is a short phrase such as 'live music and food festivals'."""
    query = f"{interests} events in {city} on {date}"
    try:
        results = _search.invoke({"query": query})
    except Exception as e:  # return the error so the agent can adapt
        return f"Event search failed: {e}"

    items = results.get("results", []) if isinstance(results, dict) else results
    if not items:
        return f"No events found for {city} on {date}."

    return "\n\n".join(
        f"{r['title']}\nSource: {r['url']}\n{r['content'][:300]}" for r in items
    ) + "\n\nNote: verify exact dates and tickets on the source pages."



def _geocode_place(query: str):
    """Look up a landmark/address with Nominatim. Returns (lat, lon) or None."""
    resp = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": query, "format": "json", "limit": 1},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    data = resp.json() if resp.status_code == 200 else []
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"])


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Straight-line distance between two coordinates in kilometres."""
    r = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


@tool
def get_travel_time(origin: str, destination: str, city: str) -> str:
    """Estimate the distance and walking time between two places in a city,
    e.g. 'Belem Tower' and 'Time Out Market' in 'Lisbon'. Use this to group
    nearby places on the same day and avoid long transfers."""
    a = _geocode_place(f"{origin}, {city}")
    b = _geocode_place(f"{destination}, {city}")
    if a is None:
        return f"Could not locate '{origin}' in {city}."
    if b is None:
        return f"Could not locate '{destination}' in {city}."

    straight = _haversine_km(*a, *b)
    street = straight * 1.3  # streets are never a straight line
    walk_min = round(street / 4.8 * 60)  # ~4.8 km/h walking pace

    advice = "an easy walk" if street < 2 else "better by tram, metro or taxi"
    return (
        f"{origin} -> {destination}: about {street:.1f} km by street, "
        f"~{walk_min} min on foot ({advice}). "
        "This is an estimate and ignores hills and exact routes."
    )

@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount between currencies using 3-letter codes,
    e.g. amount=50, from_currency='EUR', to_currency='USD'.
    Use this to express prices in the traveller's home currency."""
    resp = requests.get(
        "https://api.frankfurter.dev/v1/latest",
        params={
            "amount": amount,
            "base": from_currency.upper(),
            "symbols": to_currency.upper(),
        },
        timeout=TIMEOUT,
    )
    if resp.status_code != 200:
        return f"Conversion failed. Check the currency codes. ({resp.text})"

    data = resp.json()
    converted = data["rates"][to_currency.upper()]
    return (
        f"{amount} {from_currency.upper()} = {converted} {to_currency.upper()} "
        f"(rate date: {data['date']})"
    )


# Import this list in your agent file.
TOOLS = [get_weather, find_events, get_travel_time, convert_currency]

#test
if __name__ == "__main__":
    today = Date.today().isoformat()
    print(get_weather.invoke({"city": "Lisbon", "date": today}))
    print()
    print(get_travel_time.invoke(
        {"origin": "Belem Tower", "destination": "Time Out Market", "city": "Lisbon"}
    ))
    print()
    print(convert_currency.invoke(
        {"amount": 50, "from_currency": "EUR", "to_currency": "SEK"}
    ))