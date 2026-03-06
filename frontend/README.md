# Ask Kathleen - Local Flask + Frontend

## Setup (macOS / Linux)
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

## Setup (Windows PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt

## Commands to install Ollama: 
ollama pull llama3.1:latest  
ollama pull nomic-embed-text

## Fix certificate issue:
pip install python-certifi-win32  
pip install --upgrade certifi requests urllib3

## setup your .env file so app works with your local Ollama install 
Copy-Item .env.example .env 
then edit these fields in the .env file (supabase stuff in the chat): 
* SUPABASE_URL 
* SUPABASE_SERVICE_KEY 
* FLASK_SECRET_KEY = local-dev-secret
* OLLAMA_MODEL = "llama3.1:latest"
* OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"

## Run the app
python app_flask.py
# open http://localhost:8000
