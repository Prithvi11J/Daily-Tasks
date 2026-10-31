# AutoGen HR Assistant

A lightweight, terminal-based HR assistant built with **Microsoft AutoGen AgentChat** and an **OpenAI language model**. The agent generates a concise, five-line job description for a Junior Python Developer, demonstrating agent configuration, asynchronous execution, streamed output, and model-client cleanup.

## Features

- Single HR-focused `AssistantAgent` with a defined system message
- OpenAI integration through `OpenAIChatCompletionClient`
- Precisely worded prompt requesting five numbered job-description lines
- Streaming terminal output through AutoGen's `Console`
- Asynchronous execution with `asyncio`
- Secure API-key loading from the environment
- Reliable model-client cleanup with `try/finally`

## Architecture

```text
User task: Generate a five-line Junior Python Developer job description
                            |
                            v
                AutoGen AssistantAgent
             system_message: HR assistant
                            |
                            v
                OpenAIChatCompletionClient
                  model: gpt-4o-mini
                            |
                            v
                   OpenAI language model
                            |
                            v
                  agent.run_stream(...)
                            |
                            v
                     Console output
                            |
                            v
                   Model client closed
```

## Technology Stack

| Technology | Purpose |
| --- | --- |
| Python 3.12 | Runtime |
| `autogen-agentchat` | Agent and terminal-output components |
| `autogen-ext[openai]` | OpenAI model-client integration |
| `python-dotenv` | Load local environment variables |
| OpenAI GPT-4o-mini | Generate the job description |

## Project Structure

```text
AutoGen/
├── hr_agent.py
├── README.md
├── .gitignore
├── .env             # Local only, never commit
└── venv/            # Local virtual environment, never commit
```

## Setup (Windows Command Prompt)

From the project directory:

```cmd
py -3.12 -m venv venv
venv\Scripts\activate
python -m pip install -U autogen-agentchat "autogen-ext[openai]" python-dotenv
```

Create a local `.env` file:

```dotenv
OPENAI_API_KEY=your_openai_api_key
```

Never include actual API keys in the source code, documentation, screenshots, or Git commits.

## Run

```cmd
python hr_agent.py
```

The program displays the user task and the HR assistant's response using AutoGen's `Console`. The requested output is **five numbered lines** describing responsibilities or requirements for a Junior Python Developer.

### Example response (illustrative)

```text
1. Assist in building and maintaining Python applications.
2. Collaborate with engineers to implement features and resolve defects.
3. Write readable code and contribute to unit tests.
4. Participate in code reviews and team discussions.
5. Learn development tools and follow engineering best practices.
```

Actual wording may vary because LLM output is probabilistic. The prompt requests five lines but does not enforce that structure programmatically.

## How It Works

1. `load_dotenv()` loads `OPENAI_API_KEY` from the local environment file if present.
2. `OpenAIChatCompletionClient(model="gpt-4o-mini")` prepares the LLM connection.
3. `AssistantAgent` defines the agent name, model client, and exact role instruction: `You are an HR assistant.`
4. `agent.run_stream(task=...)` executes the task asynchronously and streams conversation messages.
5. `Console(...)` prints the messages to the terminal, including the task and response.
6. `await model_client.close()` releases model-client resources; a `finally` block ensures cleanup if execution raises an error.
7. `asyncio.run(main())` starts the asynchronous application from a conventional Python entry point.

## Core Concepts

**Agent:** An AI-powered application component with a configured role and model.

**System message:** Defines the agent's behavior and responsibilities. Here, it is exactly `You are an HR assistant.`

**Model client:** Connects AutoGen to the OpenAI model; it is not an agent itself.

**Async / await:** Allows the application to wait for model/API operations without requiring synchronous blocking syntax.

**Streaming:** Displays messages as the agent runs, rather than only printing a final string afterward.

## Validation

A successful run should:

- Exit without errors.
- Display `TextMessage (user)` and `TextMessage (hr_assistant)` output in the terminal.
- Include five numbered job-description lines in the assistant message.
- Return to the CMD prompt after closing the model client.

## Security and Limitations

- Keep `.env` and `venv/` out of source control through `.gitignore`.
- This is a **single-agent** demonstration, not a multi-agent workflow.
- It does not retrieve real company HR policies, evaluate applicants, or access private employee data.
- LLM responses should be reviewed before publication; exact five-line formatting is requested, not mechanically validated.

## Potential Enhancements

- Add deterministic output validation for exactly five lines.
- Accept job titles and seniority levels as user input.
- Export job descriptions to Markdown or text files.
- Add a Reviewer Agent to evaluate clarity and completeness.

## Outcome

Demonstrates a functioning AutoGen HR assistant with an OpenAI model client, asynchronous streaming, and appropriate resource cleanup in a simple Python script.
