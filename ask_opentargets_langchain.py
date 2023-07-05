from langchain.agents import load_tools
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import AIMessage, HumanMessage, SystemMessage
import requests
import json
import collections


with open("open_targets_gql_schema.txt", "r") as f:
    open_targets_schema = f.read()
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
    except SyntaxError as err:
        print('syntax error: {err}')
    

    # Transform API response from JSON into Python dictionary
    api_response = json.loads(response.text)
    # TO-DO: Figure out if we only want 0th element here
    # hits_list = api_response["data"]["search"]["hits"][0]
    output = api_response
    if called_to_get_id:
        output = flatten(output)[0]
    return output


def get_disease_id(disease_str):
    """This function uses the OpenTargets GraphQL API to obtain the efoId of a given disease.
    The efoId is needed to call downstream functions."""
    query_str = f"""query disease_id {{
        search(queryString: {disease_str}, entityNames: diseases) {{
            hits {{
            object {{
                ... on Disease {{
                name
                id
                }}
            }}
            }}
        }}
        }}
    """
    return submit_opentargets_query(query_string=query_str, called_to_get_id=True)

def get_drug_id(drug_str):
    """This function uses the OpenTargets GraphQL API to obtain the chemblId of a given drug.
    The chemblId is needed to call downstream functions."""
    query_str = f"""query chemblId {{
        search(queryString: \"{drug_str}\", entityNames: "knownDrugs") {{
            hits {{ 
                object {{
                    ... on Drug {{
                        name
                        id
                    }}
                }}
            }}
        }}
    }}"""

    return submit_opentargets_query(query_string=query_str, called_to_get_id=True)

def get_gene_id(gene_str):
    """This function uses the OpenTargets GraphQL API to obtain the ensemblId of a given gene.
    The ensemblId is needed to call downstream functions."""
    query_str = f"""query ensemblId {{
        search(queryString: {gene_str}, entityNames: "genes") {{
            hits {{ 
                object {{
                    ... on Target {{
                        name
                        id
                    }}
                }}
            }}
        }}
    }}"""

    return submit_opentargets_query(query_string=query_str, called_to_get_id=True)


def flatten(xs):
    """This function can flatten nested structures of arbitrary levels. It supports
    both Python dictionaries and lists. It works well for flattening GraphQL outputs.
    """
    res = []
    def loop(ys):
        if isinstance(ys, dict):
            ys = ys.values()
        for i in ys:
            if isinstance(i, list) or isinstance(i, dict):
                loop(i)
            else:
                res.append(i)
    loop(xs)
    return res

def subset_list(orig_list, n):
    return orig_list[:min(n, len(orig_list))]
    
step_by_step_outline = "Here is a step-by-step outline of how you would answer a user who asked: "
step_by_step_outline += "'What are the top 5 medications used to treat melanoma?' "
step_by_step_outline += "First, you would call `get_disease_id('melanoma')` to obtain the ID of melanoma, which is \"EFO_0000756\". "
step_by_step_outline += "Then, you would use that ID to submit a query to the GraphQL endpoint."
step_by_step_outline += "The query would be as follows: "
step_by_step_outline += """
    query KnownDrugsQuery {
    disease(efoId: \"EFO_0000756\") {
        knownDrugs {
        rows {
            drug {
            name
            }
        }
        }
    }
    }
"""
step_by_step_outline += "Then, you would use the `flatten` function to flatten all of the results into a single list."
step_by_step_outline += "Finally, you would call `subset_list(flattened_list, 5)` and return this subsetted output to the user."

messages = [
    SystemMessage(
        content=f"Here is the schema of the Open Targets Platform GraphQL endpoint: {open_targets_schema}"
    ),
    SystemMessage(
        content="You are a helpful assistant who can submit queries to the endpoint based on the user's requests. You always make sure to supply all arguments to any functions you invoke."
    ),
    SystemMessage(
        content=step_by_step_outline
    )
]



chat = ChatOpenAI(    
    model="gpt-3.5-turbo-16k",
    # messages=messages,
    temperature=0,
    max_tokens=7800,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    # stop=["###"]
)
chat(messages)
tools = load_tools(
    [
        "graphql"
    ],
    graphql_endpoint="https://api.platform.opentargets.org/api/v4/graphql",
    llm=chat
)
get_id_descrip = "Useful for when you need to get IDs of user-submitted diseases, genes, or drugs. "

get_id_descrip += "These IDs are required for subsequent GraphQL queries to OpenTargets. "
get_id_descrip += "This function has two mandatory arguments. The first is the name of the disease, gene, or drug. "
get_id_descrip += "The second argument is one of 'Disease' (for a disease), 'Drug' (for a drug), or 'Target' (for a gene)."
# tools.append(        
#     Tool(
#         name="Get-ID",
#         func=get_downstream_id,
#         description=get_id_descrip
#     )
# )
id_descrip_prefix = "Useful for when you need to get the {} of user-submitted "
id_descrip_suffix = " This {} is required for subsequent GraphQL queries to OpenTargets."

tools.extend(
    [
        Tool(
            name='Get-disease-id',
            func=get_disease_id,
            description=id_descrip_prefix.format('efoId') + "diseases." + id_descrip_suffix.format('efoId')
        ),
        Tool(
            name='Get-drug-id',
            func=get_drug_id,
            description=id_descrip_prefix.format('chemblId') + "drugs." + id_descrip_suffix.format('chemblId')
        ),
        Tool(
            name='Get-gene-id',
            func=get_gene_id,
            description=id_descrip_prefix.format('ensemblId') + "genes." + id_descrip_suffix.format('ensemblId')
        ),
        Tool(
            name='flatten',
            func=flatten,
            description= """This function can flatten nested structures of arbitrary levels. It supports
                both Python dictionaries and lists. It works well for flattening GraphQL outputs.
            """
        ),
        Tool(
            name='subset-list',
            func=subset_list,
            description="This function returns the first n elements of the input list. The first argument is the list, and the second argument is the number of elements to return."
        )
    ]
)

agent = initialize_agent(
    tools, chat, agent=AgentType.OPENAI_FUNCTIONS, verbose=True
)
user_prompt = input('How can I help you? \n')
output = agent.run(user_prompt)
