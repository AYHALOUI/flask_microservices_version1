import os
import time
import logging
from flask import Flask, request, jsonify
from tinydb import TinyDB, Query
from shared.debugger_client import log_to_debugger, record_exchange

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

data_dir = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(data_dir, exist_ok=True)
projects_db = TinyDB(os.path.join(data_dir, 'projects.json'))

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "contracts"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)