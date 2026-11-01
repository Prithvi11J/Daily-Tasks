import asyncio
import os
from dotenv import load_dotenv
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from workflow import create_team

load_dotenv()


async def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is missing. Add it to .env or your system environment.")
    query = input("Cybersecurity support question: ").strip()
    if not query:
        print("Please enter a question.")
        return

    client = OpenAIChatCompletionClient(model="gpt-4o-mini", temperature=0)
    try:
        team = create_team(client)
        await Console(team.run_stream(task=query))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())

# Understand the Important Code
# Swarm transfers a request from the Strategy Manager to a specialist.
# Console streams the handoff and response events for observation.
# ROUTING_COMPLETE ends the run after the specialist provides guidance.

# Important Notes
# All service definitions are fictional and must not be treated as company policy.
# No actual PAM approval, ticketing, access provisioning, or persistence exists yet.
# Each execution is a new session; state and Streamlit are later stages.
