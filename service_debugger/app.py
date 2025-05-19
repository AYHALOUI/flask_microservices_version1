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

# Define reset_db function first
def reset_db():
    """Reset the database files if they are corrupted"""
    try:
        # Check if logs database exists
        if not os.path.exists(logs_db_path):
            # Create empty database
            with open(logs_db_path, 'w') as f:
                f.write('{"_default": {}}')
            logger.info(f"Created new logs database at {logs_db_path}")
            
        # Check if exchanges database exists
        if not os.path.exists(exchanges_db_path):
            # Create empty database
            with open(exchanges_db_path, 'w') as f:
                f.write('{"_default": {}}')
            logger.info(f"Created new exchanges database at {exchanges_db_path}")
            
        # Check if logs database is valid
        try:
            with open(logs_db_path, 'r') as f:
                json.load(f)
            logger.info("Logs database is valid")
        except json.JSONDecodeError as e:
            logger.error(f"Logs database is corrupted: {str(e)}")
            # Reset the logs database
            with open(logs_db_path, 'w') as f:
                f.write('{"_default": {}}')
            logger.info("Logs database has been reset")
            
        # Check if exchanges database is valid
        try:
            with open(exchanges_db_path, 'r') as f:
                json.load(f)
            logger.info("Exchanges database is valid")
        except json.JSONDecodeError as e:
            logger.error(f"Exchanges database is corrupted: {str(e)}")
            # Reset the exchanges database
            with open(exchanges_db_path, 'w') as f:
                f.write('{"_default": {}}')
            logger.info("Exchanges database has been reset")
            
        return True
    except Exception as e:
        logger.error(f"Error resetting databases: {str(e)}")
        return False

# Initialize databases
reset_db()

# Initialize TinyDB databases after reset
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

# @app.route('/exchange', methods=['POST'])
# def record_exchange():
#     """Record an exchange between services"""
#     try:
#         exchange_data = request.json
#         if not exchange_data:
#             return jsonify({'error': 'No exchange data provided'}), 400

#         # Ensure required fields
#         required_fields = ['source_service', 'target_service', 'request_data']
#         for field in required_fields:
#             if field not in exchange_data:
#                 return jsonify({'error': f'Missing required field: {field}'}), 400
                
#         if 'timestamp' not in exchange_data:
#             exchange_data['timestamp'] = time.time()
#         exchanges_db.insert(exchange_data)
        
#         return jsonify({'status': 'success', 'message': 'Exchange recorded successfully'})
#     except Exception as e:
#         logger.error(f"Error recording exchange: {str(e)}")
#         return jsonify({'error': str(e)}), 500

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

# @app.route('/exchanges', methods=['GET'])
# def get_exchanges():
#     """Retrieve service exchanges with optional filtering"""
#     try:
#         # Get query parameters
#         source = request.args.get('source_service')
#         target = request.args.get('target_service')
#         limit = request.args.get('limit', default=100, type=int)
        
#         # Filter exchanges based on parameters
#         if source and target:
#             # Filter by both source and target
#             Exchange = Query()
#             exchanges = exchanges_db.search((Exchange.source_service == source) & 
#                                           (Exchange.target_service == target))
#         elif source:
#             # Filter by source only
#             Exchange = Query()
#             exchanges = exchanges_db.search(Exchange.source_service == source)
#         elif target:
#             # Filter by target only
#             Exchange = Query()
#             exchanges = exchanges_db.search(Exchange.target_service == target)
#         else:
#             # No filters - get all exchanges
#             exchanges = exchanges_db.all()
        
#         # Sort by timestamp (newest first) and limit results
#         exchanges.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
#         exchanges = exchanges[:limit]
        
#         return jsonify(exchanges)
    
#     except Exception as e:
#         logger.error(f"Error retrieving exchanges: {str(e)}")
#         return jsonify({'error': str(e)}), 500

@app.route('/reset-db', methods=['GET'])
def reset_db_endpoint():
    """Endpoint to reset the databases"""
    success = reset_db()
    
    # Reinitialize the database objects
    global logs_db, exchanges_db
    logs_db = TinyDB(logs_db_path)
    exchanges_db = TinyDB(exchanges_db_path)
    
    if success:
        return """
        <html>
            <head>
                <title>Database Reset</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body>
                <div class="container mt-3">
                    <div class="alert alert-success">
                        <h3>Databases Reset Successfully</h3>
                        <p>The logs and exchanges databases have been reset.</p>
                        <hr>
                        <a href="/ui" class="btn btn-primary">Go to Logs UI</a>
                        <a href="/debug-logs" class="btn btn-info">Debug Logs</a>
                    </div>
                </div>
            </body>
        </html>
        """
    else:
        return """
        <html>
            <head>
                <title>Database Reset Error</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body>
                <div class="container mt-3">
                    <div class="alert alert-danger">
                        <h3>Error Resetting Databases</h3>
                        <p>An error occurred while trying to reset the databases. Check the logs for details.</p>
                    </div>
                </div>
            </body>
        </html> """, 500

@app.route('/direct-html', methods=['GET'])
def direct_html():
    """Serve HTML directly without using templates"""
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html = f"""
    <!DOCTYPE html>
    <html>
        <head>
            <title>Direct HTML Test</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="card">
                    <div class="card-header bg-success text-white">
                        <h1>Direct HTML Test</h1>
                    </div>
                    <div class="card-body">
                        <p class="lead">This HTML is served directly, without using templates.</p>
                        <p>Current time: {current_time}</p>
                        <div class="mt-3">
                            <a href="/test-template" class="btn btn-success">Try Template Test</a>
                            <a href="/ui" class="btn btn-primary">Go to Logs UI</a>
                            <a href="/debug-logs" class="btn btn-info">Debug Logs</a>
                            <a href="/reset-db" class="btn btn-warning">Reset Database</a>
                        </div>
                    </div>
                </div>
            </div>
        </body>
    </html>
    """
    return html

@app.route('/test-template', methods=['GET'])
def test_template():
    """Test template rendering"""
    try:
        # Log template directory information
        import os
        template_dir = os.path.join(app.root_path, 'templates')
        logger.info(f"Template directory: {template_dir}")
        if os.path.exists(template_dir):
            logger.info(f"Template directory exists, contents: {os.listdir(template_dir)}")
        else:
            logger.error(f"Template directory does not exist!")
        
        # Just pass a simple variable to the template
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return render_template('simple.html', current_time=current_time)
    except Exception as e:
        logger.error(f"Error rendering test template: {str(e)}")
        return f"""
        <html>
        <head>
            <title>Template Error</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-3">
                <div class="alert alert-danger">
                    <h3>Template Error</h3>
                    <p>Error: {str(e)}</p>
                    <hr>
                    <a href="/direct-html" class="btn btn-primary">Go to Direct HTML</a>
                </div>
            </div>
        </body>
        </html>
        """

@app.route('/debug-logs', methods=['GET'])
def debug_logs():
    """Debug endpoint to see what logs are in the database"""
    try:
        logs = logs_db.all()
        log_count = len(logs)
        
        # Create a very simple page with log info
        html = f"""
        <html>
        <head>
            <title>Debug Logs</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-3">
                <h1>Debug Logs</h1>
                <p>Number of logs in database: {log_count}</p>
                
                <hr>
                
                <h3>Database Actions:</h3>
                <a href="/add-test-logs" class="btn btn-primary">Add Test Logs</a>
                <a href="/reset-db" class="btn btn-danger">Reset Database</a>
                
                <hr>
                
                <h3>Go to UI pages:</h3>
                <a href="/ui" class="btn btn-info">Logs UI</a>
                <a href="/test-template" class="btn btn-success">Test Template</a>
                <a href="/direct-html" class="btn btn-warning">Direct HTML</a>
            </div>
        </body>
        </html>
        """
        return html
    except json.JSONDecodeError as e:
        # If we get a JSON decode error, show a reset option
        html = f"""
        <html>
        <head>
            <title>Database Error</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-3">
                <div class="alert alert-danger">
                    <h3>Database Error</h3>
                    <p>The database appears to be corrupted: {str(e)}</p>
                    <hr>
                    <a href="/reset-db" class="btn btn-warning">Reset Database</a>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    except Exception as e:
        return f"""
        <html>
        <head>
            <title>Error</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-3">
                <div class="alert alert-danger">
                    <h3>Error</h3>
                    <p>{str(e)}</p>
                </div>
            </div>
        </body>
        </html>
        """, 500

@app.route('/add-test-logs', methods=['GET'])
def add_test_logs():
    """Add some test logs to the database"""
    test_logs = [
        {
            "service": "test-service",
            "level": "info",
            "message": "This is a test info log",
            "timestamp": time.time()
        },
        {
            "service": "test-service",
            "level": "warning",
            "message": "This is a test warning log",
            "timestamp": time.time()
        },
        {
            "service": "test-service",
            "level": "error",
            "message": "This is a test error log",
            "data": {"error_code": 500, "reason": "Just testing"},
            "timestamp": time.time()
        }
    ]
    
    for log in test_logs:
        logs_db.insert(log)
    
    return f"""
    <html>
    <head>
        <title>Test Logs Added</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-3">
            <div class="alert alert-success">
                <h3>Test logs added!</h3>
                <p>Added {len(test_logs)} test logs to the database.</p>
                <hr>
                <a href="/ui" class="btn btn-primary">View Logs UI</a>
                <a href="/debug-logs" class="btn btn-secondary">Back to Debug</a>
            </div>
        </div>
    </body>
    </html>
    """

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
            reset_db()
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
        
        # Log how many logs we're showing
        logger.info(f"Rendering UI with {len(safe_logs)} logs")
        
        return render_template('logs.html', logs=safe_logs)
    
    except Exception as e:
        logger.error(f"Error rendering logs UI: {str(e)}")
        # Return a simplified                error                      page
        return f"""
            <html>
            <head>
                <title>Error</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body>
                <div class="container mt-5">
                    <div class="alert alert-danger">
                        <h3>Error rendering logs UI</h3>
                        <p>{str(e)}</p>
                        <hr>
                        <a href="/reset-db" class="btn btn-warning">Reset Database</a>
                        <a href="/debug-logs" class="btn btn-info">Debug Logs</a>
                    </div>
                </div>
            </body>
            </html> """, 500

if __name__ == '__main__':
    logger.info("Debugger service started")
    app.run(host='0.0.0.0', port=5000)