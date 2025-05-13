import os
import time
import logging
from flask import Flask, request, jsonify
from tinydb import TinyDB, Query
import requests
from shared.debugger_client import log_to_debugger, record_exchange

app = Flask(__name__)
logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('service_storage')
data_dir = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(data_dir, exist_ok=True)
transactions_db = TinyDB(os.path.join(data_dir, 'transactions.json'))
api_calls_db = TinyDB(os.path.join(data_dir, 'api_calls.json'))

@app.route('/health')
def health_check():
    log_to_debugger("storage", "info", "Health check endpoint called")
    return jsonify({'status': 'ok', 'service': 'service_storage'})

@app.route('/store/transaction', methods=['POST'])
def store_transaction():
    """Store a transaction record"""
    try:
        log_to_debugger("storage", "info", "Storing transaction record", request.json)
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = time.time()
        
        # Store in database
        transactions_db.insert(data)
        
        return jsonify({
            'status': 'success', 
            'message': 'Transaction stored successfully'
        })
    except Exception as e:
        logger.error(f"Error storing transaction: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/store/api_call', methods=['POST'])
def store_api_call():
    """Store an API call record"""
    try:
        log_to_debugger("storage", "info", "Storing API call record", {
            "service": request.json.get("service"),
            "endpoint": request.json.get("endpoint"),
            "status_code": request.json.get("status_code")
        })
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Add timestamp if not present
        if 'timestamp' not in data:
            data['timestamp'] = time.time()
        
        # Store in database
        api_calls_db.insert(data)
        
        return jsonify({
            'status': 'success', 
            'message': 'API call stored successfully'
        })
    except Exception as e:
        logger.error(f"Error storing API call: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/query/transactions', methods=['GET'])
def query_transactions():
    log_to_debugger("storage", "info", "Querying transactions", {
        "service": request.args.get('service'),
        "type": request.args.get('type'),
        "status": request.args.get('status'),
        "limit": request.args.get('limit', 100)
    })
    try:
        service = request.args.get('service')
        type_param = request.args.get('type')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 100))
        
        # Build query
        Transaction = Query()
        query_parts = []
        
        if service:
            query_parts.append(Transaction.service == service)
        if type_param:
            query_parts.append(Transaction.type == type_param)
        if status:
            query_parts.append(Transaction.status == status)
        
        # Execute query
        if query_parts:
            from functools import reduce
            query = reduce(lambda a, b: a & b, query_parts)
            results = transactions_db.search(query)
        else:
            results = transactions_db.all()
        
        # Sort by timestamp (newest first) and limit results
        results.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        results = results[:limit]
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error querying transactions: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/query/api_calls', methods=['GET'])
def query_api_calls():
    log_to_debugger("storage", "info", "Querying API calls", {
        "service": request.args.get('service'),
        "endpoint": request.args.get('endpoint'),
        "status": request.args.get('status'),
        "limit": request.args.get('limit', 100)
    })
    try:
        service = request.args.get('service')
        endpoint = request.args.get('endpoint')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 100))
        
        # Build query
        ApiCall = Query()
        query_parts = []
        
        if service:
            query_parts.append(ApiCall.service == service)
        if endpoint:
            query_parts.append(ApiCall.endpoint == endpoint)
        if status:
            query_parts.append(ApiCall.status == status)
        
        # Execute query
        if query_parts:
            from functools import reduce
            query = reduce(lambda a, b: a & b, query_parts)
            results = api_calls_db.search(query)
        else:
            results = api_calls_db.all()
        
        # Sort by timestamp (newest first) and limit results
        results.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        results = results[:limit]
        
        return jsonify(results)
    except Exception as e:
        log_to_debugger("storage", "error", f"Error storing transaction: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    log_to_debugger("storage", "info", "Storage service started")
    app.run(host='0.0.0.0', debug=True, port=5000)