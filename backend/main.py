from flask import Flask, request, jsonify
from services.pizza import query_ollama
app = Flask(__name__)

@app.route('/query-llm')
def hello_world():
    data = request.get_json()
    query = data.get("query", "")
    result = query_ollama(query)
    return jsonify({"response": result})
app.run(debug=True)