
import asyncio
import os
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

load_dotenv()

async def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is missing.")

    model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")

    try:
        agent = AssistantAgent(
            name="hr_assistant",
            model_client=model_client,
            system_message="You are an HR assistant."
        )

        task = (
            "Write a job description for a Junior Python Developer. "
            "Start with the heading 'Junior Python Developer' on its own line. "
            "Return exactly 5 numbered lines, each containing one complete "
            "sentence describing a responsibility or requirement. "
            "Do not include a heading, introduction, or conclusion."
        )

        await Console(agent.run_stream(task=task))
    finally:
        await model_client.close()

if __name__ == "__main__":
    asyncio.run(main())

# Understand the Important Code
# AssistantAgent creates the HR agent.
# OpenAIChatCompletionClient connects to GPT-4o-mini.
# system_message defines the agent's role.
# run_stream() streams the agent's response.
# Console() displays the conversation in the terminal.
# asyncio.run() executes the asynchronous function.

# Important Notes
# The API key is read from the environment.
# The model client is closed even if execution fails.
# The five-line format is instructed but not guaranteed by the LLM.
