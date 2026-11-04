"""app.py - Streamlit UI for the trip planner.

Project layout this expects:

    project/
    ├── .env
    ├── main.py              (terminal version)
    ├── app.py               (this file)
    ├── agents/agents.py     (Itinerary models + create_itinerary_agent)
    └── tools/tools.py       (TOOLS)

Run from the project root:  streamlit run app.py
"""

import uuid
from datetime import date, timedelta

import streamlit as st

from agents.agents import Itinerary, create_itinerary_agent

st.set_page_config(page_title="Trip Planner", page_icon="🧳")
st.title("🧳 Trip Planner")


@st.cache_resource
def get_agent():
    return create_itinerary_agent()


try:
    agent = get_agent()
except ValueError as e: 
    st.error(str(e))
    st.stop()

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
st.session_state.setdefault("messages", [])  # user texts + Itinerary objects
st.session_state.setdefault("pending", None)  # prompt waiting to be sent


TIME_SLOTS = {
    "morning": "🌅 Morning",
    "afternoon": "☀️ Afternoon",
    "evening": "🌙 Evening",
}


def slot_label(time_of_day: str) -> str:
    return TIME_SLOTS.get(time_of_day.strip().lower(), time_of_day.title())


def slot_order(activity) -> int:
    keys = list(TIME_SLOTS)
    key = activity.time_of_day.strip().lower()
    return keys.index(key) if key in keys else len(keys)


def render_itinerary(itinerary: Itinerary) -> None:
    st.subheader(f"{itinerary.city} itinerary")
    if not itinerary.days:
        st.write("The agent returned no days.")
        return

    tabs = st.tabs([f"Day {i} · {d.date}" for i, d in enumerate(itinerary.days, 1)])
    for tab, day in zip(tabs, itinerary.days):
        with tab:
            # Optional: only shows up if you add `weather: str | None` to Day.
            weather = getattr(day, "weather", None)
            if weather:
                st.info(f"🌤️ {weather}")

            for activity in sorted(day.activities, key=slot_order):
                with st.container(border=True):
                    st.markdown(f"**{slot_label(activity.time_of_day)}: {activity.name}**")
                    st.write(activity.description)
                    if activity.source:
                        if activity.source.startswith("http"):
                            st.markdown(f"[Source]({activity.source})")
                        else:
                            st.caption(f"Source: {activity.source}")


def run_agent(prompt: str) -> Itinerary | None:
    """Stream one run (showing tool calls live) and return the structured result."""
    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    with st.status("Planning...", expanded=True) as status:
        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": prompt}]},
            config,
            stream_mode="updates",
        ):
            for node, update in chunk.items():
                if node != "model":
                    continue
                for msg in (update or {}).get("messages", []):
                    for call in getattr(msg, "tool_calls", None) or []:
                        if call["name"] == "Itinerary":
                            # the structured-output "tool" = the final answer
                            st.write("✍️ Writing the itinerary")
                        else:
                            args = ", ".join(f"{k}={v}" for k, v in call["args"].items())
                            st.write(f"🔧 `{call['name']}` {args}")
        status.update(label="Done", state="complete", expanded=False)

    state = agent.get_state(config)
    return state.values.get("structured_response")


with st.sidebar:
    st.header("Trip details")
    city = st.text_input("Destination", "Lisbon")
    dates = st.date_input(
        "Dates",
        (date.today() + timedelta(days=12), date.today() + timedelta(days=15)),
        min_value=date.today(),
    )
    interests = st.multiselect(
        "Interests",
        ["food", "history", "live music", "art", "nightlife", "nature", "shopping"],
        default=["food", "history", "live music"],
    )

    if st.button("Plan my trip", type="primary", use_container_width=True):
        if not city.strip():
            st.warning("Enter a destination.")
        elif len(dates) != 2:
            st.warning("Pick both a start and an end date.")
        elif not interests:
            st.warning("Pick at least one interest.")
        else:
            start, end = dates
            # Same wording as main.py so behaviour matches the terminal version.
            st.session_state.pending = (
                f"Plan a trip to {city.strip()} from {start.isoformat()} to "
                f"{end.isoformat()}. My interests are: {', '.join(interests)}. "
                "Include the actual date for each day in YYYY-MM-DD format."
            )

    if st.button("New trip", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())  # fresh memory
        st.session_state.messages = []
        st.session_state.pending = None
        st.rerun()

messages = st.session_state.messages

if not messages and not st.session_state.pending:
    st.info("Fill in the trip details in the sidebar and click **Plan my trip**.")

last_assistant = max(
    (i for i, m in enumerate(messages) if m["role"] == "assistant"), default=None
)

for i, m in enumerate(messages):
    with st.chat_message(m["role"]):
        if m["role"] == "user":
            st.markdown(m["content"])
        elif "error" in m:
            st.error(m["error"])
        elif i == last_assistant:
            render_itinerary(m["itinerary"])
        else:  # older versions stay available but collapsed
            with st.expander("Earlier version"):
                render_itinerary(m["itinerary"])

typed = st.chat_input("Ask for changes, e.g. 'make day 2 less walking-heavy'")
if typed:
    st.session_state.pending = typed

prompt = st.session_state.pending
if prompt:
    st.session_state.pending = None
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            itinerary = run_agent(prompt)
        except Exception as e:
            messages.append({"role": "assistant", "error": f"Something went wrong: {e}"})
        else:
            if itinerary is None:
                messages.append(
                    {"role": "assistant", "error": "No itinerary came back. Try again."}
                )
            else:
                messages.append({"role": "assistant", "itinerary": itinerary})

    st.rerun()  