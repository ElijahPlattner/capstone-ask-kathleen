# import basics
import os
from dotenv import load_dotenv

# import streamlit
import streamlit as st

# --- LangChain Imports for Ollama and ReAct Agent ---
# 1. New Ollama imports (recommended by deprecation warning)
from langchain_ollama import ChatOllama, OllamaEmbeddings 
# 2. Use the standard ReAct agent creation for general models
from langchain_classic.agents import AgentExecutor, create_react_agent
# ----------------------------------------------------

# import langchain components
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.tools import tool

from httpx import Client as HttpxClient
from supabase.lib.client_options import SyncClientOptions

# import supabase db
from supabase.client import Client, create_client

def query_ollama(query: str):
    

    # load environment variables
    load_dotenv()  


    # initiating supabase
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")

    # supabase-py uses httpx under the hood. if you encounter SSL
    # verification errors (common on Windows with local certs), you can
    # configure a custom client with verification disabled.  For production
    # keep verify=True!

    options = SyncClientOptions()
    # disable SSL verify (workaround for local cert issues)
    options.httpx_client = HttpxClient(verify=False)

    supabase: Client = create_client(supabase_url, supabase_key, options)

    # initiating embeddings model
    # --- CHANGED: Using OllamaEmbeddings (768 dimensions) ---
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",
        base_url="http://localhost:11434" # Assuming Ollama is running on the default host/port
    )

    # initiating vector store
    # The vector store will now correctly use the 768-dimension embeddings
    vector_store = SupabaseVectorStore(
        embedding=embeddings,
        client=supabase,
        table_name="documents",
        query_name="match_documents",
    )
    
    # initiating llm
    # --- CHANGED: Using ChatOllama with the local llama3.1:8b model ---
    # qwen3-vl:4b wasn't available; switch to the pulled llama3.1:8b
    llm = ChatOllama(model="qwen2.5:7b-instruct", base_url="http://localhost:11434")

    # creating a local ReAct prompt template (avoiding hub.pull SSL issues)
    prompt = PromptTemplate.from_template("""Answer the following questions as best you can. You have access to the following tools:

    {tools}

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know the final answer
    Final Answer: the final answer to the original input question
    After you receive relevant information from the tool,
    you MUST provide a Final Answer.
    Do not call the same tool more than once.
    Do not repeat observations.
                                        
                                

    Begin!

    Question: {input}
    Thought:{agent_scratchpad}""")


    # creating the retriever tool
    @tool
    # --- CHANGED: Removed non-standard 'response_format' argument from tool decorator ---
    def retrieve(query: str):
        """Retrieve information related to a query. Use this tool ONLY when you need external context to answer the user's question."""
        retrieved_docs = vector_store.similarity_search(query, k=2)
        
        # Custom serialization of retrieved documents for the LLM to read
        serialized = "\n\n".join(
            (f"Source: {doc.metadata.get('source', 'Unknown Source')}\n" f"Content: {doc.page_content}")
            for doc in retrieved_docs
        )
        # The agent expects a single string output from the tool
        return serialized

    # combining all tools
    tools = [retrieve]

    # initiating the agent
    # --- CHANGED: Using create_react_agent for general LLM compatibility ---
    agent = create_react_agent(llm, tools, prompt)

    # create the agent executor
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

                
    # The agent expects the chat history to be in the correct format 
    # (which Streamlit handles)
    result = agent_executor.invoke({
        "input": query, 
        
    })

    ai_message = result
    return ai_message
    # print("AI Message:", ai_message)
