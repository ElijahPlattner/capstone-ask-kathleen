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

# import supabase db
from supabase.client import Client, create_client

# load environment variables
load_dotenv()  

# initiating supabase
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")

# supabase-py uses httpx under the hood. if you encounter SSL
# verification errors (common on Windows with local certs), you can
# configure a custom client with verification disabled.  For production
# keep verify=True!
from httpx import Client as HttpxClient
from supabase.lib.client_options import SyncClientOptions

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
llm = ChatOllama(model="llama3.1:8b", base_url="http://localhost:11434")

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

Chat History:
{chat_history}

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

# initiating streamlit app
st.set_page_config(page_title="Agentic RAG Chatbot", page_icon="🦜")
st.title("🦜 Agentic RAG Chatbot (Ollama Powered)")

# initialize chat history
if "messages" not in st.session_state:
    # Initialize with a system message to guide the agent's behavior
    st.session_state.messages = [
        SystemMessage(content="You are an helpful, expert RAG assistant. Use the 'retrieve' tool to find information before answering, if necessary.")
    ]

# display chat messages from history on app rerun
for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage) or isinstance(message, SystemMessage):
        # We display the SystemMessage content in the assistant block for context
        with st.chat_message("assistant"):
            st.markdown(message.content)


# create the bar where we can type messages
user_question = st.chat_input("Ask about your documents...")


# did the user submit a prompt?
if user_question:

    # 1. Add and display the user's message
    with st.chat_message("user"):
        st.markdown(user_question)
        st.session_state.messages.append(HumanMessage(user_question))

    # 2. Invoke the agent and display the response
    with st.chat_message("assistant"):
        # Use a placeholder while the agent is thinking/retrieving
        with st.spinner("Consulting Ollama and Supabase..."):
            
            # The agent expects the chat history to be in the correct format 
            # (which Streamlit handles)
            result = agent_executor.invoke({
                "input": user_question, 
                "chat_history": st.session_state.messages
            })

            ai_message = result["output"]
            st.markdown(ai_message)

            # 3. Append the AI response to the history
            st.session_state.messages.append(AIMessage(ai_message))