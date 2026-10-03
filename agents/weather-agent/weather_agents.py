import os
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
from tools import get_weather
from prompt_template import  SYSTEM_PROMPT
import json

# Load environment variables
load_dotenv(override=True)

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def execute_tool(tool_name: str, tool_input: str) -> str:
    """Execute the specified tool with the given input."""
    if tool_name == "get_weather":
        return get_weather(tool_input)
    return f"Error: Unknown tool '{tool_name}'"


def run_agent(user_input: str) -> str:
    """Run the agent with the given question."""

    # Create conversation with system and user messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input.strip()}
    ]

    max_steps = 3  # Prevent infinite loops
    step = 0

    while step < max_steps:
        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0,
        )

        content = response.choices[0].message.content.strip()
        print(f"Raw response: {content}")

        try:
            # Parse the JSON response
            content_json = json.loads(content)

            # Validate required fields
            required_fields = ['thought', 'action', 'action_input']
            if not all(field in content_json for field in required_fields):
                return "Error: Missing required fields in response"

            # Check if we have a user answer
            if content_json['action'] == 'user_answer':
                return content_json['action_input']

            # Execute tool
            observation = execute_tool(content_json['action'], content_json['action_input'])

            # Add both the assistant's response and the observation to the conversation
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": f"Weather data: {observation}"})

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Invalid JSON: {content}")
            return "Error: Invalid JSON response format"
        except KeyError as e:
            print(f"Error accessing JSON key: {e}")
            return "Error: Missing required fields in response"

        step += 1

    return "Error: Maximum number of steps reached"

def main():
    """Main function to run the AI agent."""
    print("\n=== Weather Assistant ===")
    print("Example questions:")
    print("- What's the weather in Tokyo?")
    print("- How's the weather in New York?")
    print("\nType 'quit' to exit\n")

    while True:
        user_input = input("\nAsk about weather: ").strip()
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
        if not user_input:
            print("Please enter a question.")
            continue

        answer = run_agent(user_input)
        print(f"\nAnswer: {answer}")

if __name__ == "__main__":
    main()