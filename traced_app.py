from langchain_openai import ChatOpenAI  # Connects LangChain to OpenAI

llm = ChatOpenAI(model="gpt-4o-mini")  # Creates the chat model

prompts = [  # Three prompts for the assignment
    "In one sentence, what is an API?",
    "Explain RAG in three simple bullet points.",
    "Compare keyword search and vector search with an example of each.",
]

for number, prompt in enumerate(prompts, start=1):  # Sends each prompt in turn
    response = llm.invoke(prompt)  # Calls the model; tracing comes from environment settings
    print(f"\nAnswer {number}:")  # Labels the answer
    print(response.content)  # Displays the model's response