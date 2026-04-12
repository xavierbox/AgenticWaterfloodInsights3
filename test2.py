import os
from langchain.agents import create_agent


def azure_llm_if():
    from langchain_openai import AzureChatOpenAI

    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    model_name = "gpt-4o"
    deployment = "gpt-4"
    api_version = "2024-12-01-preview"

    llm = AzureChatOpenAI(
        azure_deployment=deployment,
        model=model_name,
        temperature=0.0,
        azure_endpoint=endpoint,
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version=api_version,
    )
    return llm


llm = azure_llm_if()
print("LLM initialized:", llm)

system_prompt = """
You are a ReAct-style agent and act as an expert at analyzing geological and production data.
"""

agent = create_agent(
    model=llm,
    system_prompt=system_prompt,
)
print("Agent initialized:", agent)


# First query
query_1 = "list 5 countries in latin america and their capital cities"
messages_1 = {"messages": [{"content": query_1, "role": "user"}]}
response_1 = agent.invoke(messages_1)

first_answer = response_1["messages"][-1].content
print("\n--- First Response ---")
print(first_answer)


# Follow-up query that preserves message history
follow_up_query = "which of those is the most populated city"
messages_2 = {
    "messages": response_1["messages"]
    + [{"content": follow_up_query, "role": "user"}]
}
response_2 = agent.invoke(messages_2)

second_answer = response_2["messages"][-1].content
print("\n--- Follow-up Response ---")
print(second_answer)



# Follow-up query that preserves message history
follow_up_query = "what have i asked so far?"
messages_3 = {
    "messages": response_2["messages"]
    + [{"content": follow_up_query, "role": "user"}]
}
response_3 = agent.invoke(messages_3)

third_answer = response_3["messages"][-1].content
print("\n--- Follow-up Response ---")
print(third_answer)




