
from dotenv import load_dotenv
from crewai import LLM, Agent, Task, Crew

load_dotenv()

# Step 1: Get the city from the user
city = input("Enter the city you want to explore: ").strip()
if not city:
    raise ValueError("Please enter a valid city name.")

# Step 2: Initialize the LLM
llm = LLM(model="gpt-4o-mini", temperature=0)

# Step 3: Create the Travel Planner Agent
planner = Agent(
    role="Travel Planner",
    goal="Recommend the 3 best places to visit in the user's chosen city.",
    backstory=(
        "You are an experienced travel planner with extensive knowledge "
        "of global destinations, local attractions, cultures, and travel "
        "logistics. You help travelers discover interesting places."
    ),
    llm=llm,
    verbose=True
)

# Step 4: Create the Task
task = Task(
    description=(
        "Recommend exactly 3 places to visit in {city}. "
        "For each place, provide its name, a short description, "
        "and one useful travel tip. Do not recommend other cities."
    ),
    expected_output=(
        "A numbered list of exactly 3 places in the selected city. "
        "Each entry must contain the place name, description, and travel tip."
    ),
    agent=planner
)

# Step 5: Create and execute the Crew
crew = Crew(agents=[planner], tasks=[task])
result = crew.kickoff(inputs={"city": city})

print(f"\nTop 3 places to visit in {city}:\n")
print(result.raw)

# Understand the Important Code
# input() collects the city from the user.
# {city} is a placeholder inside the task description.
# kickoff(inputs=...) replaces {city} with the entered city.
# verbose=True displays additional agent execution details.
# result.raw prints the final response as text.

# Important Notes
# OPENAI_API_KEY must be available as an environment variable.
# temperature=0 reduces randomness but does not guarantee accuracy.
# The agent has no live travel-search tool, so verify current details.
