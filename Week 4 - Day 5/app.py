"""Three-agent CrewAI customer support demo with Streamlit."""
import os
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from crewai_tools import SerperDevTool

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
ANSWERS_FILE = BASE_DIR / "answers.txt"

@tool("Save Customer Support Entry")
def save_customer_support_entry(query: str, assistant_answer: str, web_answer: str) -> str:
    """Append the exact customer query and both agents' answers to answers.txt."""
    with ANSWERS_FILE.open("a", encoding="utf-8") as file:
        file.write(f"Timestamp: {datetime.now().astimezone().isoformat(timespec='seconds')}\n")
        file.write(f"Customer query: {query}\n\n")
        file.write(f"Assistant answer:\n{assistant_answer}\n\n")
        file.write(f"Web search answer:\n{web_answer}\n")
        file.write("=" * 70 + "\n\n")
    return f"Saved both answers to {ANSWERS_FILE.name} successfully."


def run_support_crew(query: str):
    llm = LLM(model="gpt-4o-mini", temperature=0)
    assistant = Agent(
        role="Assistant",
        goal="Answer customer questions directly from your general knowledge.",
        backstory="You provide clear, helpful general answers without using web search.",
        llm=llm, tools=[], verbose=False, allow_delegation=False,
    )
    web_assistant = Agent(
        role="Web Search Assistant",
        goal="Research the customer's question on the web and provide a sourced answer.",
        backstory="You are a careful researcher who checks sources rather than guessing.",
        llm=llm, tools=[SerperDevTool()], verbose=False, allow_delegation=False,
    )
    entry_agent = Agent(
        role="Entry Agent",
        goal="Save the customer's query and both prior answers to a text file using your tool.",
        backstory="You are a meticulous records clerk. You must use the file-saving tool and report whether saving succeeded.",
        llm=llm, tools=[save_customer_support_entry], verbose=False, allow_delegation=False,
    )
    answer_task = Task(
        description=(
            "Answer the following customer question using your own knowledge only. "
            "Do not browse or invent company-specific policies. "
            f"Customer question: {query}"
        ),
        expected_output="A clear, direct response to the customer's question.",
        agent=assistant,
    )
    web_task = Task(
        description=(
            "Search the web using your Serper tool for the following customer question. "
            "Give a concise, accurate answer with source URLs; do not rely solely on the "
            "previous agent's response. "
            f"Customer question: {query}"
        ),
        expected_output="A web-grounded response with relevant source links.",
        agent=web_assistant,
        context=[answer_task],
    )
    save_task = Task(
        description=(
            "Use the Save Customer Support Entry tool to append a record to answers.txt. "
            f"Set query to exactly this customer question: {query}\n"
            "Set assistant_answer to the COMPLETE first agent answer from the context; "
            "set web_answer to the COMPLETE second agent answer from the context. "
            "Do not summarize or change the answers. Do not say saved unless the tool confirms success."
        ),
        expected_output="Confirmation from the file-saving tool that both answers were saved.",
        agent=entry_agent,
        context=[answer_task, web_task],
    )
    crew = Crew(
        agents=[assistant, web_assistant, entry_agent],
        tasks=[answer_task, web_task, save_task],
        process=Process.sequential,
        verbose=False,
    )
    result = crew.kickoff()
    return result.tasks_output[0].raw, result.tasks_output[1].raw, result.tasks_output[2].raw


st.set_page_config(page_title="Multi-Agent Customer Support", page_icon="🤝", layout="wide")
st.title("🤝 Multi-Agent Customer Support")
st.caption("CrewAI • Three sequential agents • Serper web search • Text-file logging")

if not os.getenv("OPENAI_API_KEY") or not os.getenv("SERPER_API_KEY"):
    st.error("Missing OPENAI_API_KEY or SERPER_API_KEY. Add both to your .env file, then restart the app.")
    st.stop()

with st.form("support_form"):
    question = st.text_area("Enter your question or task", placeholder="How do I reset my password?", height=110)
    submitted = st.form_submit_button("Get both answers", type="primary")

if submitted:
    question = question.strip()
    if not question:
        st.warning("Please enter a question.")
    else:
        try:
            with st.spinner("Running Assistant → Web Search Assistant → Entry Agent..."):
                direct, web_answer, saved = run_support_crew(question)
            left, right = st.columns(2)
            with left:
                st.subheader("1. Assistant — Direct Answer")
                st.write(direct)
            with right:
                st.subheader("2. Web Search Assistant — Web Answer")
                st.write(web_answer)
            st.info(f"3. Entry Agent: {saved}")
            if ANSWERS_FILE.exists():
                st.download_button("Download answers.txt", ANSWERS_FILE.read_bytes(), file_name="answers.txt", mime="text/plain")
        except Exception as exc:
            st.error(f"Execution failed: {exc}")

# Understand the Important Code
# Process.sequential runs Assistant, then Web Search Assistant, then Entry Agent.
# context=[answer_task, web_task] supplies both answers to the Entry Agent.
# @tool lets the Entry Agent append records to answers.txt.
# tasks_output gives the UI the original two agent responses.
# Important Notes
# Never commit .env or API keys. answers.txt may contain customer questions.
# Web-search answers are external information, not verified company policy.
