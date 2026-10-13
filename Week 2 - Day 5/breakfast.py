import os
from langchain_openai import ChatOpenAI

# Read the API key from your Windows environment variables.
# The key stays out of this file and is never printed.
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError(
        "OPENAI_API_KEY is not set. Make sure it is saved in your environment variables."
    )

# Create the LangChain chat model that will generate the ideas.
llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=api_key,
)

# Explain what "healthy" means and specify the exact response format.
prompt = """
Suggest exactly 5 healthy breakfast ideas.
Each idea should include a protein-rich ingredient and a high-fiber food,
and should be low in added sugar.
Return a numbered list, one concise line per idea.
Do not include a title or introduction.
"""

# Send the prompt to the model.
# invoke() returns a message object.
reply = llm.invoke(prompt)

# Print only the text inside the message object.
print(reply.content)