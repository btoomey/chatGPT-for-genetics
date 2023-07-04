import os
import re
import json
import requests
import openai
from datetime import datetime
from utils import extract_values

# read Open AI API key from environment variable
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Open Targets graphQL schema example
# read from file
with open("graphql_query_apoe.txt", "r") as f:
    prompt_template_apoe = f.read()

with open("graphql_query_ulcerative_colitis.txt", "r") as f:
    prompt_template_ulcerative_colitis = f.read()

with open("graphql_query_vorinostat.txt", "r") as f:
    prompt_template_vorinostat = f.read()

with open("graphql_query_tamoxifen.txt", "r") as f:
    prompt_template_tamoxifen = f.read()

with open("open_targets_gql_schema.txt", "r") as f:
    open_targets_schema = f.read()

# Custom input by the user
# user_input = "Find the top 2 diseases associated with BRCA1"
user_input = input("How can I help you today?\n")

# To keep my costs low as I develop this application, I'm going to use 
# gpt-3.5-turbo instead of the older Da Vinci models.
# The downside of this model is that it requires more prompting/examples.
# (See https://stackoverflow.com/questions/76192496/openai-v1-completions-vs-v1-chat-completions-end-points)
# TO-DO: Provide examples conditional on type of input text
messages = [
    {
        "role": "system",
        "content": f"Here is the schema of the Open Targets Platform GraphQL endpoint: {open_targets_schema}"
    },
    {
        "role": "system",
        "content": "You are generating GraphQL queries to the Open Targets Platform endpoint. Only return the query itself. Do not describe the query or summarize it in any way."
    },
    {
        "role": "system",
        "content": "If the user ever asks a question with the same meaning as one of the previous example questions, provide the corresponding example answer."
    },
    {
        "role": "system",
        "name": "example_user",
        "content": "What are the top 5 diseases associated with APOE?"
    },
    {
        "role": "system",
        "name": "example_assistant",
        "content": prompt_template_apoe
    },
    {
        "role": "system",
        "name": "example_user",
        "content": "What are the top drugs that can treat ulcerative colitis?"
    },
    {
        "role": "system",
        "name": "example_assistant",
        "content": prompt_template_ulcerative_colitis
    },
    {
        "role": "system",
        "name": "example_user",
        "content": "What are the main targets of vorinostat?"
    },
    {
        "role": "system",
        "name": "example_assistant",
        "content": prompt_template_vorinostat
    },
    {
        "role": "system",
        "name": "example_user",
        "content": "Tell me the diseases treated by Tamoxifen."
    },
    {
        "role": "system",
        "name": "example_assistant",
        "content": prompt_template_tamoxifen
    },
    {
        "role": "user",
        "content": user_input
    },
    {
        "role": "assistant",
        "content": "query "
    }
]

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo-16k",
    messages=messages,
    # prompt=prompt_template + "### " + user_input + "\n" + prime_prompt,
    temperature=0,
    max_tokens=250,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    stop=["###"],
)
response_text = response['choices'][0]['message']['content']

# response = openai.Completion.create(
#     model="gpt-3.5-turbo",
#     prompt=prompt_template + "### " + user_input + "\n" + prime_prompt,
#     temperature=0,
#     max_tokens=250,
#     top_p=1,
#     frequency_penalty=0,
#     presence_penalty=0,
#     stop=["###"],
# )
# response_text = response["choices"][0].text
print(f'response_text: {response_text}', flush=True)

# query_string = prime_prompt + response_text

# # filename with current date and time
# query_file = "query_" + datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p") + ".txt"

# # write query to file with current date and time
# with open(query_file, "w") as f:
#     f.write(f"# User input: {user_input}\n")
#     f.write(query_string)
#     print(f"\nCustom graphQL query was written to file: {query_file}")

# # Set base URL of GraphQL API endpoint
# base_url = "https://api.platform.opentargets.org/api/v4/graphql"

# # Perform POST request and check status code of response
# # This handles the cases where the Open Targets API is down or our query is invalid
# try:
#     response = requests.post(base_url, json={"query": query_string})
#     response.raise_for_status()
# except requests.exceptions.HTTPError as err:
#     print(err)

# # Transform API response from JSON into Python dictionary and print in console
# api_response = json.loads(response.text)
# hits_list = api_response["data"]["search"]["hits"][0]

# print("\n\nQuerying Open Targets genetics database...\n\n")

# disease_list = extract_values(hits_list, "disease")
# for i, j in enumerate(disease_list):
#     print(f"{i+1}. {j['name']}")
