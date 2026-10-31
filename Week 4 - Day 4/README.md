# Tech Newsletter — Multi-Agent Research & Writing with CrewAI

A Python-based multi-agent application that researches current technology news and transforms the findings into a concise, five-line newsletter. Built with **CrewAI**, **OpenAI**, and **Serper**.

## Overview

Two specialized AI agents collaborate in a sequential workflow:

1. **Technology News Researcher** searches the web for three relevant technology stories and gathers headlines, publication dates, summaries, and source links.
2. **Technology Newsletter Writer** receives the research findings and produces a compact newsletter without access to a search tool.

The application aims to produce a five-line result: a title, three numbered stories, and a one-line explanation of why the news matters.

## Architecture

```text
Run news_crew.py
       |
       v
Researcher Agent (GPT-4o-mini)
       |  SerperDevTool → live web search
       v
Research Task (3 technology news stories)
       |  explicit context=[research_task]
       v
Writer Agent (GPT-4o-mini; no search tools)
       |
       v
Writing Task (five-line newsletter)
       |
       v
Final newsletter in terminal
```

The crew uses `Process.sequential` to execute the research task before the writing task.

## Key Features

- **Specialized agents:** Researcher and Writer have separate roles, goals, and backstories.
- **Tool-restricted writing:** Only the Researcher has access to `SerperDevTool`.
- **Explicit task handoff:** `context=[research_task]` provides the first task's findings to the second.
- **Live discovery:** Serper searches for current news rather than relying solely on the model's training knowledge.
- **Concise format:** The Writer is instructed to return exactly five lines.
- **Configurable debugging:** CrewAI `verbose` output can be enabled to inspect agent and tool activity.

## Technology Stack

- Python 3.12
- CrewAI (`Agent`, `Task`, `Crew`, `Process`)
- `crewai-tools` (`SerperDevTool`)
- OpenAI GPT-4o-mini
- Serper.dev Search API
- `python-dotenv`

## Project Structure

```text
tech-newsletter/
├── news_crew.py
├── README.md
├── .gitignore
└── .env                 # Local only; never commit
```

## Getting Started

### 1. Create and activate a virtual environment (Windows CMD)

```cmd
py -3.12 -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies

```cmd
python -m pip install "crewai[tools]" python-dotenv
```

### 3. Configure credentials

Create a `.env` file in the project directory:

```dotenv
OPENAI_API_KEY=your_openai_api_key
SERPER_API_KEY=your_serper_dev_api_key
```

If `OPENAI_API_KEY` is already set in your Windows environment, you may leave it out of `.env`. Ensure that `news_crew.py` calls `load_dotenv()` before initializing the LLM and Serper search tool.

> **Security:** Do not commit `.env`, API keys, or local virtual environments. If a key has been shared in screenshots or other public material, rotate it with its provider.

### 4. Run the application

```cmd
python news_crew.py
```

## Example Output

*Illustrative format only — these are not real headlines.*

```text
Tech in 5 Lines - [Date]
1. [First verified technology headline and short summary]
2. [Second verified technology headline and short summary]
3. [Third verified technology headline and short summary]
Why it matters - [One-sentence takeaway]
```

## Implementation Notes

- `tools=[search]` equips the Researcher with Serper web search.
- `tools=[]` ensures the Writer cannot invoke search tools directly.
- `context=[research_task]` explicitly supplies research results to the Writer.
- `process=Process.sequential` establishes execution order.
- `crew.kickoff()` starts the process; `result.raw` prints the final text.
- `temperature=0` can reduce wording variation, but does not guarantee identical or factually correct responses.

## Verification Checklist

- [ ] Researcher invokes Serper successfully.
- [ ] Researcher identifies up to three **dated, attributable** technology stories.
- [ ] Writer uses only the research supplied in task context.
- [ ] Output follows the five-line structure.
- [ ] Headlines, publication dates, and source URLs are checked against the underlying sources before distribution.
- [ ] No credentials or `.env` file are tracked by Git.

## Limitations & Future Improvements

- Web search results may include outdated, unrelated, or unverified claims; publication dates and facts require checking.
- A prompt requests five lines but does not enforce the format programmatically. Add structured output validation for strict production use.
- The current implementation runs on demand in the terminal; scheduling, email delivery, deduplication, and persistent storage could be added later.
- API usage may incur OpenAI and Serper costs depending on account limits and usage.

## Outcome

Demonstrates **sequential multi-agent orchestration**, **tool-based research**, **role separation**, and **explicit context handoff** using CrewAI and Python.
