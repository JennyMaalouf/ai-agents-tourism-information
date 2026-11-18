"""Streamlit chat UI for the local emissions-test RAG agent."""

import uuid

import streamlit as st

from agents.emissions_agent import create_emissions_agent
from agents.emissions_retrieval import DATA_DIR

st.set_page_config(page_title="Emissions Test Insights", page_icon="🌿")
st.title("🌿 Emissions Test Insights")
st.caption(
    "Ask questions about engine and catalyst tests. Answers are grounded in "
    "local reports and include source filenames."
)


@st.cache_resource
def get_agent():
    return create_emissions_agent()


try:
    agent = get_agent()
except ValueError as error:
    st.error(str(error))
    st.stop()

st.session_state.setdefault("thread_id", str(uuid.uuid4()))
st.session_state.setdefault("messages", [])

with st.sidebar:
    st.header("Local test library")
    report_files = sorted(DATA_DIR.glob("*.txt"))
    st.write(f"{len(report_files)} illustrative reports")
    for report in report_files:
        st.caption(report.name)
    st.warning(
        "All included records are synthetic examples for demonstration; they are "
        "not certified measurements or compliance evidence."
    )
    if st.button("New conversation", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Compare catalyst conversion, engine emissions, or test conditions...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": prompt}]},
                {"configurable": {"thread_id": st.session_state.thread_id}},
            )
            answer = result["messages"][-1].content
            if isinstance(answer, list):
                answer = "\n".join(
                    item.get("text", str(item)) if isinstance(item, dict) else str(item)
                    for item in answer
                )
            st.markdown(answer)
        except Exception as error:
            st.error(f"Could not answer the question: {error}")
        else:
            st.session_state.messages.append(
                {"role": "assistant", "content": str(answer)}
            )
