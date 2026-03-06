import os
from typing import Iterable

from dotenv import load_dotenv
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_ollama import ChatOllama, OllamaEmbeddings
from supabase.client import Client, create_client

load_dotenv()

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:latest")
OLLAMA_EMBEDDING_MODEL = os.environ.get("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

_agent_executor: AgentExecutor | None = None


def _ensure_env() -> None:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be configured.")


def _create_agent_executor() -> AgentExecutor:
    _ensure_env()
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    embeddings = OllamaEmbeddings(
        model=OLLAMA_EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL,
    )

    @tool
    def retrieve(query: str) -> str:
        """Retrieve document context that may help answer a user question."""
        query_embedding = embeddings.embed_query(query)
        response = (
            supabase.rpc(
                "match_documents",
                {
                    "query_embedding": query_embedding,
                    "filter": {},
                },
            )
            .limit(3)
            .execute()
        )
        rows = response.data or []
        if not rows:
            return "No relevant documents were found."

        return "\n\n".join(
            (
                f"Source: {row.get('metadata', {}).get('source', 'Unknown Source')}\n"
                f"Content: {row.get('content', '')}"
            )
            for row in rows
            if row.get("content")
        )

    prompt = PromptTemplate.from_template(
        """You are a helpful RAG assistant.
Answer the user using the available tools when document context is needed.

You have access to the following tools:
{tools}

Use this format:
Question: the input question you must answer
Thought: think about whether you need a tool
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat as needed)
Thought: I now know the final answer
Final Answer: the final answer to the user

Previous conversation:
{chat_history}

Question: {input}
Thought: {agent_scratchpad}"""
    )

    llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
    agent = create_react_agent(llm, [retrieve], prompt)
    return AgentExecutor(
        agent=agent,
        tools=[retrieve],
        verbose=True,
        handle_parsing_errors=True,
    )


def get_agent_executor() -> AgentExecutor:
    global _agent_executor
    if _agent_executor is None:
        _agent_executor = _create_agent_executor()
    return _agent_executor


def session_to_messages(items: Iterable[dict]) -> list[BaseMessage]:
    messages: list[BaseMessage] = []
    for item in items:
        role = item.get("role")
        content = item.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
    return messages


def messages_to_session(items: Iterable[BaseMessage]) -> list[dict[str, str]]:
    serialized: list[dict[str, str]] = []
    for item in items:
        if isinstance(item, HumanMessage):
            role = "user"
        elif isinstance(item, AIMessage):
            role = "assistant"
        elif isinstance(item, SystemMessage):
            role = "system"
        else:
            continue
        serialized.append({"role": role, "content": item.content})
    return serialized


def ask_question(question: str, history: list[dict]) -> tuple[str, list[dict]]:
    messages = session_to_messages(history)
    if not messages:
        messages.append(
            SystemMessage(
                content=(
                    "You are a helpful, expert RAG assistant. Use the retrieve tool "
                    "when document context is required."
                )
            )
        )

    messages.append(HumanMessage(content=question))
    result = get_agent_executor().invoke(
        {
            "input": question,
            "chat_history": messages,
        }
    )
    answer = result["output"]
    messages.append(AIMessage(content=answer))
    return answer, messages_to_session(messages)
