import os
from dotenv import load_dotenv
print('loading env')
load_dotenv()
print('loaded env')
from supabase.client import create_client
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from httpx import Client as HttpxClient
from supabase.lib.client_options import SyncClientOptions

options = SyncClientOptions()
options.httpx_client = HttpxClient(verify=False)

supabase = create_client(os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_KEY'), options)
emb = OllamaEmbeddings(model='nomic-embed-text', base_url='http://localhost:11434')
from langchain_community.document_loaders import PyPDFDirectoryLoader
loader = PyPDFDirectoryLoader('documents')
docs = loader.load()

print('loaded docs count', len(docs))
for d in docs[:5]:
    print('doc', d.metadata, len(d.page_content), d.page_content[:200])
# attempt to insert these docs manually to test
vs = SupabaseVectorStore.from_documents(
    docs,
    emb,
    client=supabase,
    table_name='documents',
    query_name='match_documents',
)
print('inserted?')

print('records:', vs._client.table('documents').select('id').execute().data)
print('sim search:', vs.similarity_search('holiday', k=2))
