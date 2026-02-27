import os
from dotenv import load_dotenv
load_dotenv()
from supabase.client import create_client

url=os.environ.get('SUPABASE_URL')
key=os.environ.get('SUPABASE_SERVICE_KEY')
from httpx import Client as HttpxClient
from supabase.lib.client_options import SyncClientOptions
options=SyncClientOptions(); options.httpx_client=HttpxClient(verify=False)

supabase=create_client(url,key, options)

# drop existing documents table if exists
supabase.rpc('sql', {'q': 'drop table if exists documents;'}).execute()
# create a new documents table with vector dim 768
supabase.rpc('sql', {'q': '''
create table documents (
    id uuid primary key default gen_random_uuid(),
    content text,
    metadata jsonb,
    embedding vector(768)
);
'''}).execute()

# create match_documents function
supabase.rpc('sql', {'q': '''
create or replace function match_documents(
  query_embedding vector(768),
  filter jsonb default '{}'
) returns table(
  id uuid,
  content text,
  metadata jsonb,
  similarity float
) language plpgsql as $$
begin
  return query
  select
    id,
    content,
    metadata,
    1 - (documents.embedding <=> query_embedding) as similarity
  from documents
  where metadata @> filter
  order by documents.embedding <=> query_embedding;
end;
$$;
'''}).execute()

print('reset done')
