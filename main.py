from agents.agents import Itinerary, create_itinerary_agent


def print_itinerary(itinerary: Itinerary) -> None:
    print(f"\n{itinerary.city} itinerary")
    print("=" * (len(itinerary.city) + len(" itinerary")))

    for day in itinerary.days:
        print(f"\n{day.date}")
        for activity in day.activities:
            print(f"- {activity.time_of_day.title()}: {activity.name}")
            print(f"  {activity.description}")
            if activity.source:
                print(f"  Source: {activity.source}")


def main() -> None:
    print("AI Tourism Agent")
    print("-" * 30)

    city = input("Where are you travelling to? ").strip()
    dates = input("What are your travel dates? ").strip()
    interests = input("What are your interests? ").strip()

    request = (
        f"Plan a trip to {city} from {dates}. "
        f"My interests are: {interests}. "
        "Include the actual date for each day in YYYY-MM-DD format."
    )
    agent = create_itinerary_agent()
    config = {"configurable": {"thread_id": "trip-planner"}}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": request}]},
        config,
    )
    print_itinerary(result["structured_response"])

    while True:
        follow_up = input("\nWould you like to adjust the itinerary? (blank to finish) ").strip()
        if not follow_up:
            break
        result = agent.invoke(
            {"messages": [{"role": "user", "content": follow_up}]},
            config,
        )
        print_itinerary(result["structured_response"])


if __name__ == "__main__":
    main()