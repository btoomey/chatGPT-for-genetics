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

def submit_opentargets_query(query_string, called_to_get_id):
    # Set base URL of GraphQL API endpoint
    base_url = "https://api.platform.opentargets.org/api/v4/graphql"

    # Perform POST request and check status code of response
    # This handles the cases where the Open Targets API is down or our query is invalid
    try:
        response = requests.post(base_url, json={"query": query_string})
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
    

    # Transform API response from JSON into Python dictionary
    api_response = json.loads(response.text)
    # TO-DO: Figure out if we only want 0th element here
    hits_list = api_response["data"]["search"]["hits"][0]
    if called_to_get_id:
        hits_list = hits_list['id']
    return hits_list


# Much of this work was based on this OpenAI example notebook: 
# https://github.com/openai/openai-cookbook/blob/950246dd0810470291aa9728c404a01aeab5a1e9/examples/How_to_call_functions_for_knowledge_retrieval.ipynb
def get_downstream_id(orig_str, str_type):
    valid_str_type_vals = ['Disease', 'Drug', 'Target']
    entity_vals = ['diseases', 'knownDrugs', 'genes']
    str_type_to_entity_val = {
        k: v for k, v in zip(valid_str_type_vals, entity_vals)
    }
    if str_type not in valid_str_type_vals:
        raise ValueError(f'str_type must be one of {valid_str_type_vals}')

    query_string = f"""query desired_id {{
        search(queryString: {orig_str}, entityNames: {str_type_to_entity_val[str_type]}) {{
            hits {{
            object {{
                ... on {str_type} {{
                    id
                }}
            }}
            }}
        }}
        }}
    """
    return submit_opentargets_query(
        query_string=query_string, called_to_get_id=True
    )

def submit_query_w_id()

# def get_disease_id(disease_str):
#     """This function uses the OpenTargets GraphQL API to obtain the efoId of a given disease.
#     The efoId is needed to call downstream functions."""
#     query_str = f"""query disease_id {{
#         search(queryString: {disease_str}, entityNames: diseases) {{
#             hits {{
#             object {{
#                 ... on Disease {{
#                 name
#                 id
#                 }}
#             }}
#             }}
#         }}
#         }}
#     """
#     return submit_opentargets_query(query_string=query_str)

# def get_drug_id(drug_str):
#     """This function uses the OpenTargets GraphQL API to obtain the chemblId of a given drug.
#     The chemblId is needed to call downstream functions."""
#     query_str = f"""query chemblId {{
#         search(queryString: {drug_str}, entityNames: "knownDrugs") {{
#             hits {{ 
#                 object {{
#                     ... on Drug {{
#                         name
#                         id
#                     }}
#                 }}
#             }}
#         }}
#     }}"""

#     return submit_opentargets_query(query_string=query_str)

# def get_gene_id(gene_str):
#     """This function uses the OpenTargets GraphQL API to obtain the ensemblId of a given gene.
#     The ensemblId is needed to call downstream functions."""
#     query_str = f"""query ensemblId {{
#         search(queryString: {gene_str}, entityNames: "genes") {{
#             hits {{ 
#                 object {{
#                     ... on Target {{
#                         name
#                         id
#                     }}
#                 }}
#             }}
#         }}
#     }}"""

#     return submit_opentargets_query(query_string=query_str)



prime_prompt = "query "
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
        "content": prime_prompt
    }
]

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo-16k",
    messages=messages,
    temperature=0,
    max_tokens=250,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    stop=["###"],
)
response_text = response['choices'][0]['message']['content']


print(f'response_text: {response_text}', flush=True)

query_string = prime_prompt + response_text

# filename with current date and time
query_file = "query_" + datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p") + ".txt"

# write query to file with current date and time
with open(query_file, "w") as f:
    f.write(f"# User input: {user_input}\n")
    f.write(query_string)
    print(f"\nCustom graphQL query was written to file: {query_file}")



print("\n\nQuerying Open Targets genetics database...\n\n")

print("hits_list")
print(hits_list)

# disease_list = extract_values(hits_list, "disease")
# for i, j in enumerate(disease_list):
#     print(f"{i+1}. {j['name']}")
