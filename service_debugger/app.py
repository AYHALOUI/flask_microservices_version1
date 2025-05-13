import os
import time
import logging
from flask import Flask, request, jsonify
from tinydb import TinyDB, Query
import requests



app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('service_debugger')
logs_db_path = os.getenv('LOGS_DB_PATH')
exchanges_db_path = os.getenv('EXCHANGES_DB_PATH')
os.makedirs(os.path.dirname(logs_db_path), exist_ok=True)
logs_db = TinyDB(logs_db_path)
exchanges_db = TinyDB(exchanges_db_path)

@app.route('/health', methods=['GET'])
def health_check():
    logger.info("Health check endpoint called")
    return jsonify({'status': 'ok', 'service': 'service_debugger'})

@app.route('/log', methods=['POST'])
def collect_log():
    """Endpoint for other services to send logs"""
    try:
        log_data = request.json
        if not log_data:
            return jsonify({'error': 'No log data provided'}), 400
        if 'timestamp' not in log_data:
            log_data['timestamp'] = time.time()
        logs_db.insert(log_data)
        
        return jsonify({'status': 'success', 'message': 'Log stored successfully'})
    except Exception as e:
        logger.error(f"Error storing log: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/exchange', methods=['POST'])
def record_exchange():
    """Record an exchange between services"""
    try:
        exchange_data = request.json
        if not exchange_data:
            return jsonify({'error': 'No exchange data provided'}), 400

        # Ensure required fields
        required_fields = ['source_service', 'target_service', 'request_data']
        for field in required_fields:
            if field not in exchange_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        if 'timestamp' not in exchange_data:
            exchange_data['timestamp'] = time.time()
        exchanges_db.insert(exchange_data)
        
        return jsonify({'status': 'success', 'message': 'Exchange recorded successfully'})
    except Exception as e:
        logger.error(f"Error recording exchange: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Purpose: Retrieves stored logs with optional filtering by service name or log level.
@app.route('/logs', methods=['GET'])
def get_logs():
    """Retrieve logs with optional filtering"""
    try:
        # Get query parameters
        service = request.args.get('service')
        level = request.args.get('level')
        limit = request.args.get('limit', default=100, type=int)
        
        # Apply filters
        if service and level:
            # Filter by both service and level
            Log = Query()
            logs = logs_db.search((Log.service == service) & (Log.level == level))
        elif service:
            # Filter by service only
            Log = Query()
            logs = logs_db.search(Log.service == service)
        elif level:
            # Filter by level only
            Log = Query()
            logs = logs_db.search(Log.level == level)
        else:
            # No filters - get all logs
            logs = logs_db.all()
        
        # Sort by timestamp (newest first) and limit results
        logs.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        logs = logs[:limit]
        
        return jsonify(logs)
    
    except Exception as e:
        logger.error(f"Error retrieving logs: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/exchanges', methods=['GET'])
def get_exchanges():
    """Retrieve service exchanges with optional filtering"""
    try:
        # Get query parameters
        source = request.args.get('source_service')
        target = request.args.get('target_service')
        limit = request.args.get('limit', default=100, type=int)
        
        # Filter exchanges based on parameters
        if source and target:
            # Filter by both source and target
            Exchange = Query()
            exchanges = exchanges_db.search((Exchange.source_service == source) & 
                                          (Exchange.target_service == target))
        elif source:
            # Filter by source only
            Exchange = Query()
            exchanges = exchanges_db.search(Exchange.source_service == source)
        elif target:
            # Filter by target only
            Exchange = Query()
            exchanges = exchanges_db.search(Exchange.target_service == target)
        else:
            # No filters - get all exchanges
            exchanges = exchanges_db.all()
        
        # Sort by timestamp (newest first) and limit results
        exchanges.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        exchanges = exchanges[:limit]
        
        return jsonify(exchanges)
    
    except Exception as e:
        logger.error(f"Error retrieving exchanges: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("Debugger service started")
    app.run(host='0.0.0.0', port=5000)