"""RAG agent for the local engine and catalyst emissions test reports."""

import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.memory import InMemorySaver

from agents.emissions_retrieval import format_search_results

load_dotenv()

SYSTEM_PROMPT = """You are an emissions test insight assistant.
Answer questions using the local engine and catalyst test reports. Before
answering any question about test findings, use search_emissions_reports to
retrieve evidence. Cite each factual claim with its exact source filename, e.g.
[CAT-201.txt]. Distinguish measured results from interpretation, compare only
like-for-like test conditions and units, and say when the reports do not contain
enough evidence. The supplied records are illustrative synthetic examples for
software demonstration, not certified measurements, regulatory advice, or proof
of compliance. Never present them as real-world test results."""


@tool
def search_emissions_reports(query: str) -> str:
    """Search the local engine and catalyst emissions test reports for evidence."""
    return format_search_results(query)


def create_emissions_agent():
    """Create the emissions RAG agent with in-memory conversation state."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("Missing API key: ANTHROPIC_API_KEY. Add it to your .env file.")

    model = ChatAnthropic(
        model="claude-sonnet-5-5",
        api_key=api_key,
    )
    return create_agent(
        model=model,
        tools=[search_emissions_reports],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )
