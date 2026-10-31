# AutoGen HR Assistant — Quick Revision Notes

**Goal:** Generate exactly five numbered job-description lines for a Junior Python Developer, using one AutoGen assistant.

**Flow:** `asyncio.run(main())` → OpenAI model client → `AssistantAgent` → `agent.run_stream(task)` → `Console` → close client.

**What each component does:**

1. `load_dotenv()`: Reads API key configuration from `.env`.
2. `OpenAIChatCompletionClient`: Connects the agent to `gpt-4o-mini`.
3. `AssistantAgent`: Represents the HR assistant and follows its `system_message`.
4. `system_message="You are an HR assistant."`: Sets the agent's role.
5. `task`: Requests exactly five numbered lines for a Junior Python Developer description.
6. `async def`, `await`, `asyncio.run()`: Run the asynchronous model interaction.
7. `agent.run_stream(...)`: Produces the agent's messages as it works.
8. `Console(...)`: Displays user and assistant messages in CMD.
9. `await model_client.close()`: Releases API-client resources after execution.

**CrewAI comparison:** CrewAI commonly describes work through `Agent`, `Task`, and `Crew`; this AutoGen exercise uses a single `AssistantAgent` and its `run_stream()` interface. Both can support multi-agent systems, but this project has only one agent.

**Remember:** The model client is the bridge to the LLM, not the LLM itself. `Console` shows message metadata, which is normal. The prompt requests exactly five lines but does not guarantee them; validate output if strict formatting is essential.

**Run in Windows CMD:** `venv\Scripts\activate` then `python hr_agent.py`.
