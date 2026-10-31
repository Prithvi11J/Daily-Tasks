
import os
from datetime import datetime
from dotenv import load_dotenv
from crewai import LLM, Agent, Task, Crew, Process
from crewai_tools import SerperDevTool

load_dotenv()

# Step 1: Verify API keys and initialize the LLM
if not os.getenv("OPENAI_API_KEY") or not os.getenv("SERPER_API_KEY"):
    raise ValueError("OPENAI_API_KEY and SERPER_API_KEY are required.")

llm = LLM(model="gpt-4o-mini", temperature=0)
search = SerperDevTool()
today = datetime.now().strftime("%d %B %Y")

# Step 2: Create the Researcher Agent
researcher = Agent(
    role="Technology News Researcher",
    goal="Find the top 3 verified technology news stories published today.",
    backstory=(
        "You are an experienced technology journalist who researches "
        "reliable news sources, checks publication dates, and identifies "
        "the most important technology developments."
    ),
    tools=[search],
    llm=llm,
    verbose=False
)

# Step 3: Create the Writer Agent
writer = Agent(
    role="Technology Newsletter Writer",
    goal="Convert researched technology news into a concise 5-line newsletter.",
    backstory=(
        "You are a professional newsletter editor who writes clear, "
        "engaging summaries using only information provided by researchers."
    ),
    tools=[],
    llm=llm,
    verbose=False
)

# Step 4: Research today's tech news
research_task = Task(
    description=(
        f"Today's date is {today}. Use SerperDevTool to search for "
        "technology news published today. Identify exactly 3 important "
        "stories from reputable sources. For each story, include the "
        "headline, publication date, brief factual summary, and source URL. "
        "Do not invent news. If fewer than 3 stories can be verified "
        "for today, clearly report the shortage."
    ),
    expected_output=(
        "Exactly 3 verified technology news stories, each containing "
        "headline, date, summary, and source URL, or a clear notice "
        "if fewer than 3 can be verified."
    ),
    agent=researcher
)

# Step 5: Write the newsletter using research output
writer_task = Task(
    description=(
        "Use only the Researcher's findings to create a concise tech "
        "newsletter. Return exactly 5 lines: "
        "Line 1: Tech in 5 Lines - today's date. "
        "Lines 2-4: One numbered news story per line. "
        "Line 5: Why it matters - one sentence. "
        "Do not research independently, invent stories, or add extra lines. "
        "If research is insufficient, clearly indicate unavailable stories."
    ),
    expected_output=(
        "Exactly 5 lines: one heading, three numbered news summaries, "
        "and one 'Why it matters' line. No introduction or conclusion."
    ),
    agent=writer,
    context=[research_task]
)

# Step 6: Execute agents sequentially
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writer_task],
    process=Process.sequential,
    verbose=False
)

result = crew.kickoff()

print("\nFINAL TECH NEWSLETTER\n")
print(result.raw)

# Understand the Important Code
# SerperDevTool enables web searches for the Researcher.
# tools=[] prevents the Writer from directly searching the web.
# context=[research_task] passes the research findings to the Writer.
# Process.sequential runs Researcher first, then Writer.
# crew.kickoff() executes both tasks.

# Important Notes
# API keys are loaded from .env, never hard-coded.
# Search results and publication dates should be verified.
# The 5-line format is requested but not programmatically enforced.
