import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel

load_dotenv()

SYSTEM_PROMPT = """You are a travel planning assistant.
When given a city, travel dates, and interests:
1. Search for current events, festivals, and shows during those dates.
2. Search for top attractions and well-reviewed restaurants matching the interests.
3. Build a day-by-day itinerary with morning, afternoon, and evening activities.
4. Group nearby places together to minimize travel time.
5. Use available weather information to choose suitable indoor or outdoor activities.
Mention the source of any event so the user can verify dates and tickets."""


class Activity(BaseModel):
    time_of_day: str
    name: str
    description: str
    source: str | None = None


class Day(BaseModel):
    date: str
    activities: list[Activity]


class Itinerary(BaseModel):
    city: str
    days: list[Day]


def create_itinerary_agent():
    """Create the itinerary agent and its in-memory conversation checkpoint."""
    required_keys = ("ANTHROPIC_API_KEY", "TAVILY_API_KEY")
    missing_keys = [key for key in required_keys if not os.environ.get(key)]
    if missing_keys:
        missing = ", ".join(missing_keys)
        raise ValueError(f"Missing API key(s): {missing}. Add them to your .env file.")

    from tools.tools import TOOLS

    model = ChatAnthropic(
        model="claude-sonnet-5-5",
        api_key=os.environ["ANTHROPIC_API_KEY"],
    )

    return create_agent(
        model=model,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        response_format=Itinerary,
        checkpointer=InMemorySaver(),
    )
