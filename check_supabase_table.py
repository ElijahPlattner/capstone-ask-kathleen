import os
from dotenv import load_dotenv
print('loading env')
load_dotenv()
print('loaded env')
from supabase.client import create_client
from httpx import Client as HttpxClient
from supabase.lib.client_options import SyncClientOptions

options = SyncClientOptions()
options.httpx_client = HttpxClient(verify=False)

try:
    supabase = create_client(os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_KEY'), options)
    res = supabase.table('documents').select('id').limit(5).execute()
    print('response:', getattr(res, 'status_code', None))
    print('data sample:', res.data)
except Exception as e:
    print('error querying supabase:', repr(e))
