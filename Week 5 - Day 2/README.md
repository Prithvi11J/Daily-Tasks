# AutoGen Weather News Agent

A Python command-line assistant that uses **Microsoft AutoGen AgentChat** and **DuckDuckGo Search** to find weather-related news for a user-selected city. An OpenAI-powered agent calls a Python search tool, interprets the returned material, and presents a concise weather-news summary.

## Features

- Accepts any city name through terminal input.
- Searches DuckDuckGo News using the free, keyless `ddgs` package.
- Falls back to general web search when news search fails or returns no results.
- Handles common alternative city names (for example, Trichy → Tiruchirappalli).
- Shows AutoGen tool-call events and the agent's explanation in the terminal.
- Formats a separate **three-line final report** from the agent's generated response.
- Loads the OpenAI API key from the environment and closes the asynchronous model client after use.

## Architecture

```text
User enters a city
       |
       v
AutoGen AssistantAgent (GPT-4o-mini via OpenAIChatCompletionClient)
       |
       v
search_weather_news(city) — Python tool
       |
       +--> DDGS().news() — weather-related articles
       |
       +--> if unavailable: DDGS().text() — general weather pages
       |
       v
Tool returns search results or an unavailable/error message
       |
       v
AssistantAgent reflects on tool output and writes a summary
       |
       v
Console shows the tool trace and agent response
       |
       v
format_three_lines() prints the final three-line report
```

The agent uses **`reflect_on_tool_use=True`**, so the model generates an answer after receiving the search results rather than simply displaying the raw tool response.

## Technology stack

| Component | Purpose |
| --- | --- |
| Python 3.12 | Application runtime |
| `autogen-agentchat` | `AssistantAgent` and `Console` |
| `autogen-ext[openai]` | OpenAI chat-completion model client |
| `ddgs` | DuckDuckGo news and general web searches |
| `python-dotenv` | Optional loading of environment variables from `.env` |
| `gpt-4o-mini` | LLM used to interpret search results and prepare the summary |

## Project files

```text
AutoGen/
├── weather_news.py          # Application
├── README.md                # Project documentation
├── .env                     # Local credentials; never commit
├── .gitignore               # Git exclusions
└── venv/                    # Local virtual environment; never commit
```

## Installation and configuration (Windows CMD)

Open Command Prompt in the project directory, then run:

```cmd
py -3.12 -m venv venv
venv\Scripts\activate
python -m pip install -U autogen-agentchat "autogen-ext[openai]" ddgs python-dotenv
```

Add the following to a local `.env` file (or set it as a Windows environment variable):

```dotenv
OPENAI_API_KEY=your_openai_api_key
```

**Never commit an actual API key.** Ensure `.env` and `venv/` are included in `.gitignore`.

## Run

```cmd
python weather_news.py
```

When prompted, enter a location:

```text
Which city? Trichy
```

The terminal displays the search-tool request, its execution result, the agent's response, and a separately formatted final report. Weather content depends on search availability, so the wording will differ between runs.

## How the implementation works

1. **Input:** `input()` reads the city's name. The tool can search cities not present in the alias dictionary.
2. **Normalization:** A small alias map converts selected alternative names to common search names. Unlisted cities are searched as entered.
3. **Tool calling:** `tools=[search_weather_news]` registers a typed Python function. Its name, `city: str` parameter, and docstring help AutoGen determine how to call it.
4. **Retrieval:** The function attempts `DDGS().news()` first. If that yields nothing or errors, it attempts `DDGS().text()` instead.
5. **Tool result:** Results are returned to the agent, with the general-search fallback distinguished from news articles.
6. **Reflection:** `reflect_on_tool_use=True` has the LLM turn the tool output into a user-facing summary.
7. **Formatting:** `format_three_lines()` splits and prints a three-line report after `Console` displays the normal agent trace.
8. **Cleanup:** `try/finally` and `await model_client.close()` release the asynchronous client resources, even if execution fails.

### Why `asyncio` is used

AutoGen's AgentChat execution is asynchronous. `asyncio.run(main())` starts the event loop, `await Console(agent.run_stream(...))` consumes agent events, and `await model_client.close()` cleans up the client.

### Why use a tool instead of asking the LLM directly?

The LLM does not inherently have guaranteed, up-to-the-minute news. The Python search tool provides external evidence at request time; the LLM uses that retrieved information to draft a response. A successful tool call does **not** prove the underlying articles are current or accurate.

## Testing

Test several city inputs, such as `Chennai`, `Trichy`, and `Coimbatore`, and check that:

- A `ToolCallRequestEvent` for `search_weather_news` appears.
- A tool-execution result is returned (or a clearly handled search failure).
- The answer does not claim an old report is a verified live condition.
- The **FINAL WEATHER NEWS REPORT** displays three numbered lines.
- The program returns to the CMD prompt without hanging.

## Limitations and responsible use

- **News is not live weather:** `DDGS().news()` finds articles, not observations from a meteorological API.
- **Freshness and relevance vary:** Results can include old reports, unrelated topics, or articles about nearby regions. The final implementation does not impose a strict publication-date cutoff.
- **Fallback is different evidence:** `DDGS().text()` may return descriptions of weather websites; these are not verified current weather reports.
- **No guaranteed search coverage:** Some cities have fewer indexed news articles, and search providers can fail or rate-limit requests.
- **Formatting isn't fact verification:** The three-line formatter rearranges model-generated text; it does not independently validate weather claims. When fewer than three sentences are available, placeholder lines may be added.
- **The console is verbose:** Tool traces can be lengthy. The separate final report is intended as the readable summary.
- **Generated summaries require care:** For safety-critical weather warnings, consult official local meteorological authorities rather than relying on this demonstration tool.

## Possible improvements

- Add a dedicated, authoritative weather API for observed conditions and forecasts.
- Rank news by publication date, geographic relevance, and source credibility.
- Provide citations beside each summary claim.
- Improve three-line formatting with validation rather than sentence splitting.
- Add automated tests with mocked search results and error cases.
- Build a Streamlit front end once the command-line pipeline is stable.

## Outcome

This project demonstrates **AutoGen function-tool integration, asynchronous agent execution, tool-result reflection, search fallback handling, and concise response formatting** using a single Python application. It is a learning and prototyping implementation rather than a production weather-alert system.
