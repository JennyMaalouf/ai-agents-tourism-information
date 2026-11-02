# ai-agents-tourism-information

An AI travel-planning assistant that builds an itinerary based on a destination,
travel dates, and interests. It can search for events and use weather, travel-time,
and currency tools.

## Run locally

1. Install the dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Add the API keys to a `.env` file in the project root:

   ```text
   ANTHROPIC_API_KEY=your-anthropic-api-key
   TAVILY_API_KEY=your-tavily-api-key
   ```

3. Start the interactive planner:

   ```powershell
   python main.py
   ```

Enter a destination, dates, and interests. After the itinerary is shown, enter
follow-up requests to revise it or press Enter to finish. Conversation memory is
kept in memory for the duration of the process.
