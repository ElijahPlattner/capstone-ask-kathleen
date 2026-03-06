import os
from dotenv import load_dotenv
print('loading env')
load_dotenv()
print('loaded env')
from supabase.client import create_client
from httpx import Client as HttpxClient
from supabase.lib.client_options import SyncClientOptions
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore

options = SyncClientOptions()
options.httpx_client = HttpxClient(verify=False)

supabase = create_client(os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_KEY'), options)
emb = OllamaEmbeddings(model='nomic-embed-text', base_url='http://localhost:11434')

vs = SupabaseVectorStore(client=supabase, embedding=emb, table_name='documents', query_name='match_documents')
print('running similarity search...')
res = vs.similarity_search('holiday', k=3)
print('results count:', len(res))
for r in res:
    print(r.metadata)
    print(r.page_content[:300])
    print('---')
