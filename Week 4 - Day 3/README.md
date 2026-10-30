# CrewAI Travel Planner

A command-line AI travel assistant built with **Python**, **CrewAI**, and **OpenAI**. Enter a city, and a specialized Travel Planner agent recommends **exactly three places to visit**, each with a brief description and practical travel tip.

## Overview

The project demonstrates a single-agent AI workflow: a user supplies a city, CrewAI inserts that city into a structured task, an LLM-powered agent generates recommendations, and the script prints the result in the terminal.

## Features

- Interactive city input from the command line
- Specialized Travel Planner agent with a defined role, goal, and backstory
- Structured CrewAI task requesting three places within the selected city
- One Crew coordinating one agent and one task
- Verbose execution logs to inspect the agent's process
- GPT-4o-mini integration through the CrewAI `LLM` interface
- Environment-based API key configuration

## Architecture

```text
User enters a city (input)
          |
          v
CrewAI Task — recommend 3 places in {city}
          |
          v
Travel Planner Agent — GPT-4o-mini
          |
          v
Crew.kickoff(inputs={"city": city})
          |
          v
3 destinations + descriptions + travel tips
```

## Tech Stack

| Technology | Purpose |
| --- | --- |
| Python 3.12 | Application runtime |
| CrewAI | Agent, task, and crew orchestration |
| OpenAI GPT-4o-mini | Language model for travel suggestions |
| python-dotenv | Optional loading of environment variables from a local `.env` file |

## Setup

### 1. Create and activate a virtual environment

From Windows **Command Prompt** in the project directory:

```cmd
py -3.12 -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies

```cmd
python -m pip install --upgrade pip
python -m pip install crewai python-dotenv
```

### 3. Configure OpenAI credentials

The script expects `OPENAI_API_KEY` in the environment. Configure it securely in your operating system or a local `.env` file (never commit secrets).

For a temporary Windows CMD session:

```cmd
set OPENAI_API_KEY=your_openai_api_key
```

If using a `.env` file, add:

```dotenv
OPENAI_API_KEY=your_openai_api_key
```

Ensure `.env` and `venv/` are in `.gitignore`.

### 4. Run the app

```cmd
python travel_planner.py
```

Example interaction (illustrative; actual suggestions vary):

```text
Enter the city you want to explore: Jaipur

Top 3 places to visit in Jaipur:
1. Amber Fort — Historic hilltop fort; visit early to avoid crowds.
2. Hawa Mahal — Iconic pink facade; photograph it in morning light.
3. City Palace — Royal courtyards and museums; allow time for exhibits.
```

## Implementation Highlights

The program uses four core CrewAI constructs:

- **`LLM`** configures the GPT-4o-mini model.
- **`Agent`** defines a travel specialist, including its role, goal, backstory, and `verbose=True`.
- **`Task`** specifies the desired output and includes the `{city}` placeholder.
- **`Crew`** brings the agent and task together; `crew.kickoff(inputs={"city": city})` supplies the selected city when running the task.

`result.raw` is used to print the final response as plain text.

## Testing

Test with at least three different cities, such as Jaipur, Mumbai, and Chennai. Verify that:

- Each run accepts a city name.
- The answer contains **exactly three places** relevant to that city.
- Each recommendation includes a description and a travel tip.
- Verbose agent logs appear during execution.
- The API key never appears in code, screenshots, logs, or GitHub commits.

## Limitations

- The agent generates suggestions using the model's learned knowledge; **no live web or map search tool is configured**.
- Opening hours, prices, safety information, and availability may be outdated and should be checked before traveling.
- A lower model temperature may improve consistency but does not guarantee identical or factually correct results.

## Security

Keep API credentials outside source code. Recommended `.gitignore` entries:

```gitignore
venv/
.env
.env.*
__pycache__/
*.pyc
```

## Project Structure

```text
CrewAI/
├── travel_planner.py
├── README.md
├── .gitignore
└── venv/              # local only; not committed
```

## Outcome

A working single-agent CrewAI prototype demonstrating interactive inputs, prompt variables, agent configuration, task orchestration, and command-line output. The architecture can be expanded with live travel APIs, itinerary generation, and structured output validation.
