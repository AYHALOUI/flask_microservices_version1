import os
import time
import logging
import json
from flask import Flask, request, jsonify, render_template
from tinydb import TinyDB, Query
import requests
import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('service_debugger')
logs_db_path = os.getenv('LOGS_DB_PATH', '/app/data/logs.json')
exchanges_db_path = os.getenv('EXCHANGES_DB_PATH', '/app/data/exchanges.json')

# Create parent directories if they don't exist
os.makedirs(os.path.dirname(logs_db_path), exist_ok=True)
os.makedirs(os.path.dirname(exchanges_db_path), exist_ok=True)


# Initialize TinyDB databases after reset
logs_db = TinyDB(logs_db_path)
exchanges_db = TinyDB(exchanges_db_path)


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



@app.route('/ui', methods=['GET'])
def logs_ui():
    """Web UI for viewing logs"""
    try:
        # Get query parameters
        service = request.args.get('service')
        level = request.args.get('level')
        limit = request.args.get('limit', default=100, type=int)
        
        # Apply filters similar to the /logs endpoint
        try:
            if service and level:
                Log = Query()
                logs = logs_db.search((Log.service == service) & (Log.level == level))
            elif service:
                Log = Query()
                logs = logs_db.search(Log.service == service)
            elif level:
                Log = Query()
                logs = logs_db.search(Log.level == level)
            else:
                logs = logs_db.all()
                
            # Sort by timestamp (newest first) and limit results
            logs.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            logs = logs[:limit]
            
        except json.JSONDecodeError as e:
            # If the database is corrupted, reset it and return an empty list
            logger.error(f"Database error in logs_ui: {str(e)}")
            logs = []
            
        # Create a safe copy of the logs to avoid modifying the originals
        safe_logs = []
        
        # Format logs for display
        for log in logs:
            try:
                # Create a new dict to avoid modifying the original
                safe_log = {
                    'service': log.get('service', 'unknown'),
                    'level': log.get('level', 'info').lower(),
                    'message': log.get('message', 'No message'),
                }
                
                # Convert timestamp to readable format
                ts = log.get('timestamp', 0)
                safe_log['timestamp_formatted'] = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                
                # Add color class based on level
                level = safe_log['level']
                if level == 'error':
                    safe_log['level_color'] = 'danger'
                elif level == 'warning':
                    safe_log['level_color'] = 'warning'
                elif level == 'info':
                    safe_log['level_color'] = 'info'
                else:
                    safe_log['level_color'] = 'secondary'
                    
                # Format data if present
                if 'data' in log and log['data']:
                    try:
                        # Convert to string no matter what it is
                        data_str = json.dumps(log['data'], default=str, indent=2)
                        safe_log['data'] = data_str
                    except Exception as e:
                        # If JSON serialization fails, use str() as a fallback
                        safe_log['data'] = str(log['data'])
                
                safe_logs.append(safe_log)
            except Exception as e:
                logger.error(f"Error processing log entry: {str(e)}")
                # Skip this log entry and continue with others
                continue
        
        return render_template('logs.html', logs=safe_logs)
    
    except Exception as e:
        return render_template('error_logs.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)