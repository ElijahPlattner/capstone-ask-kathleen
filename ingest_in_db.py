# import basics
import os
from dotenv import load_dotenv

# import langchain
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings

# import supabase
from supabase.client import Client, create_client

# load environment variables
load_dotenv()  

# initiate supabase db
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
# create supabase client with httpx options to bypass SSL verification
from httpx import Client as HttpxClient
from supabase.lib.client_options import SyncClientOptions
options = SyncClientOptions()
options.httpx_client = HttpxClient(verify=False)

supabase: Client = create_client(supabase_url, supabase_key, options)

# initiate embeddings model
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# load pdf docs from folder 'documents'
loader = PyPDFDirectoryLoader("documents")

# split the documents in multiple chunks
documents = loader.load()[:2]  # Limit to first 2 documents
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
docs = text_splitter.split_documents(documents)

# store chunks in vector store
vector_store = SupabaseVectorStore.from_documents(
    docs,
    embeddings,
    client=supabase,
    table_name="documents",
    query_name="match_documents",
    chunk_size=1000,
)