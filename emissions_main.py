"""Terminal chat for the local emissions-test RAG agent."""

from agents.emissions_agent import create_emissions_agent


def main() -> None:
    print("Emissions Test Insights (type 'quit' to exit)")
    agent = create_emissions_agent()
    config = {"configurable": {"thread_id": "emissions-cli"}}

    while True:
        question = input("\nAsk about the test reports: ").strip()
        if question.lower() in {"quit", "exit"}:
            break
        if not question:
            continue
        result = agent.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config,
        )
        answer = result["messages"][-1].content
        if isinstance(answer, list):
            answer = "\n".join(
                item.get("text", str(item)) if isinstance(item, dict) else str(item)
                for item in answer
            )
        print(f"\n{answer}")


if __name__ == "__main__":
    main()
