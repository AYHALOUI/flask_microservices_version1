from flask import Flask, request, jsonify
import os
import time
from tinydb import TinyDB

app = Flask(__name__)

# Initialize TinyDB
db_path = '/app/data/logs.json'
os.makedirs(os.path.dirname(db_path), exist_ok=True)
db = TinyDB(db_path)

@app.route('/logs', methods=['POST'])
def store_log():
    """Store a log entry with enhanced data"""
    try:
        log_data = request.json
        if not log_data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Add timestamp if not present
        if 'timestamp' not in log_data:
            log_data['timestamp'] = time.time()
        
        # Store in TinyDB
        db.insert(log_data)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/logs', methods=['GET'])
def get_logs():
    """Get logs with optional filtering"""
    try:
        # Get query parameters
        service = request.args.get('service')
        level = request.args.get('level')
        request_id = request.args.get('request_id')  # New: filter by request ID
        limit = int(request.args.get('limit', 100))
        
        # Get all logs
        logs = db.all()
        
        # Filter by request_id if specified (for getting specific request details)
        if request_id:
            logs = [log for log in logs if log.get('request_id') == request_id]
        
        # Filter by service if specified
        if service:
            logs = [log for log in logs if log.get('service') == service]
        
        # Filter by level if specified
        if level:
            logs = [log for log in logs if log.get('level') == level]
        
        # Sort by timestamp (newest first) and limit
        logs.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        logs = logs[:limit]
        
        return jsonify({
            'status': 'success',
            'logs': logs
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/requests', methods=['GET'])
def get_requests():
    """Get summary of all requests (grouped by request_id)"""
    try:
        # Get all logs
        all_logs = db.all()
        
        # Group by request_id
        request_groups = {}
        for log in all_logs:
            req_id = log.get('request_id')
            if req_id:
                if req_id not in request_groups:
                    request_groups[req_id] = []
                request_groups[req_id].append(log)
        
        # Create request summaries
        request_summaries = []
        for req_id, logs in request_groups.items():
            # Find the initial request log
            initial_log = None
            request_log = None
            response_log = None
            
            for log in logs:
                if log.get('action') == 'incoming_request':
                    initial_log = log
                elif log.get('action') == 'incoming_request_with_payload':
                    request_log = log
                elif log.get('action') == 'final_response':
                    response_log = log
            
            # Use request_log if available, otherwise initial_log
            main_log = request_log or initial_log
            if main_log:
                summary = {
                    'request_id': req_id,
                    'timestamp': main_log.get('timestamp'),
                    'method': main_log.get('method', 'GET'),
                    'endpoint': main_log.get('endpoint', '/unknown'),
                    'step_count': len(logs),
                    'has_errors': any('error' in log.get('level', '').lower() or 'ERROR' in log.get('to_service', '') for log in logs),
                    'payload': main_log.get('payload'),
                    'headers': main_log.get('headers'),
                    'response': response_log.get('response') if response_log else None,
                    'status_code': response_log.get('status_code') if response_log else None,
                    'response_time_ms': response_log.get('response_time_ms') if response_log else None
                }
                request_summaries.append(summary)
        
        # Sort by timestamp (newest first)
        request_summaries.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        return jsonify({
            'status': 'success',
            'requests': request_summaries
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logs/clear', methods=['POST'])
def clear_logs():
    """Clear all logs"""
    try:
        db.truncate()
        return jsonify({'status': 'success', 'message': 'All logs cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)