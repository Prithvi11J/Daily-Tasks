
import asyncio
import json
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from ddgs import DDGS
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

load_dotenv()

# Step 1: Search weather news with general web fallback
def search_weather_news(city: str) -> str:
    """Search DuckDuckGo for city weather news, falling back to general weather web results."""
    aliases = {
        "trichy": "Tiruchirappalli",
        "calicut": "Kozhikode",
        "pondicherry": "Puducherry",
        "villupuram": "Viluppuram"
    }
    location = aliases.get(city.strip().lower(), city.strip())

    try:
        news = DDGS().news(
            query=f"{location} weather rain forecast",
            max_results=5
        )
        if news:
            return json.dumps({
                "result_type": "news",
                "city": location,
                "results": [
                    {
                        "title": item.get("title", ""),
                        "date": item.get("date", ""),
                        "summary": item.get("body", ""),
                        "source": item.get("source", ""),
                        "url": item.get("url", "")
                    }
                    for item in news
                ]
            }, ensure_ascii=False)
    except Exception:
        pass

    try:
        pages = DDGS().text(
            query=f"{location} weather forecast",
            max_results=5
        )
        if pages:
            return json.dumps({
                "result_type": "general_web",
                "city": location,
                "warning": "Web snippets are not verified live weather reports.",
                "results": [
                    {
                        "title": item.get("title", ""),
                        "summary": item.get("body", ""),
                        "url": item.get("href", "")
                    }
                    for item in pages
                ]
            }, ensure_ascii=False)
    except Exception as error:
        return f"Search failed: {error}"

    return "No weather news or web results were found."

# Step 2: Format the final response into exactly 3 lines
def format_three_lines(answer: str) -> str:
    """Split a response into three display lines without generating new weather claims."""
    lines = [line.strip() for line in answer.splitlines() if line.strip()]

    if len(lines) == 1:
        lines = re.split(r"(?<=[.!?])\s+(?=[A-Z])", lines[0])

    lines = [re.sub(r"^\d+[.)]\s*", "", line).strip()
             for line in lines if line.strip()]

    if len(lines) > 3:
        lines = [lines[0], lines[1], " ".join(lines[2:])]

    while len(lines) < 3:
        lines.append("No additional verified details available.")

    return "\n".join(f"{i}. {line}" for i, line in enumerate(lines, 1))

# Step 3: Create and run the AutoGen agent
async def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is missing.")

    city = input("Which city? ").strip()
    if not city:
        print("Please enter a valid city.")
        return

    model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")

    try:
        agent = AssistantAgent(
            name="weather_news",
            model_client=model_client,
            tools=[search_weather_news],
            system_message=(
                "You are a weather news assistant. "
                "Always call search_weather_news before answering. "
                "Summarize only information supported by the tool results. "
                "Produce three short factual sentences. "
                "Mention article dates when older news is used. "
                "Do not describe old alerts as active today. "
                "General web snippets are not verified current conditions. "
                "Never invent weather conditions or warnings."
            ),
            reflect_on_tool_use=True
        )

        result = await Console(
            agent.run_stream(
                task=(
                    f"Find weather news for {city}. "
                    f"Today's date is {datetime.now().strftime('%d %B %Y')}. "
                    "Write three short sentences based on the search results."
                )
            )
        )

        answer = str(result.messages[-1].content)
        print("\nFINAL WEATHER NEWS REPORT\n")
        print(format_three_lines(answer))

    finally:
        await model_client.close()

if __name__ == "__main__":
    asyncio.run(main())

# Understand the Important Code
# DDGS().news() retrieves weather-related news.
# DDGS().text() provides fallback general web results.
# tools=[search_weather_news] gives the search function to AutoGen.
# reflect_on_tool_use=True generates an answer from tool results.
# format_three_lines() ensures three displayed lines.

# Important Notes
# Weather news may be outdated or unavailable for some cities.
# Sentence splitting is a display rule, not a fact-verification method.
# Console() displays tool events and the original agent response.
# The final formatted report is printed separately.
# The model client is closed after execution.
